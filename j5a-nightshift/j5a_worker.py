#!/usr/bin/env python3
"""
J5A Nightshift Worker - Main orchestrator for autonomous overnight operations
Processes jobs from queue with local LLM execution and validation
Enhanced with Retriever v2.1 integration

Constitutional Authority: J5A_CONSTITUTION.md - All Principles
Strategic Framework: J5A_STRATEGIC_AI_PRINCIPLES.md - All Principles
"""

import os
import sys
import yaml
import json
import time
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

# Add j5a-nightshift/core to path for principle imports
sys.path.insert(0, str(Path(__file__).parent / "core"))

try:
    from governance_logger import GovernanceLogger
    from strategic_principles import StrategicPrinciples
    GOVERNANCE_AVAILABLE = True
except ImportError:
    GOVERNANCE_AVAILABLE = False
    # Graceful degradation if governance module not available yet

# Import Nightshift components
from llm_gateway import LLMGateway, LLMMode, retry_with_backoff
from sherlock_ingest import ingest
from sherlock_chunk import chunk, select_excerpts
from summarize_local import summarize

# Import Retriever v2.1 integration
sys.path.append('ops/fetchers')
from j5a_retrieval_gateway import J5ARetrievalGateway
from sherlock_retrieval import SherlockRetrieval

# Import validators
sys.path.append('ops/validators')
from code_validator import validate_code_file
from summaries_validator import validate_summary

logger = logging.getLogger(__name__)


class JobType(Enum):
    """Job types supported by Nightshift"""
    RESEARCH_REPORT = "research_report"
    CODE_STUB = "code_stub"
    SUMMARY = "summary"
    TRANSCRIPTION = "transcription"
    PODCAST_TRANSCRIPTION = "podcast_transcription"
    # v2.1 Retriever job types
    INTELLIGENCE_DISCOVERY = "intelligence_discovery"
    DATABASE_QUERY = "database_query"
    WEB_SCRAPING = "web_scraping"
    ML_INFERENCE = "ml_inference"
    MULTI_SOURCE_RETRIEVAL = "multi_source_retrieval"


class JobClass(Enum):
    """Job complexity classification"""
    STANDARD = "standard"      # Local 7B can handle
    DEMANDING = "demanding"    # Requires larger model or API


class J5AWorker:
    """
    Main Nightshift worker orchestrator

    Responsibilities:
    - Load jobs from queue database
    - Route to appropriate processing pipeline
    - Validate outputs using quality gates
    - Update job status and metrics
    """

    def __init__(self, config_path: str = None):
        """Initialize worker with configuration"""
        if config_path is None:
            config_path = "/home/johnny5/Johny5Alive/j5a-nightshift/rules.yaml"

        # Load configuration
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.phase = self.config.get("phase", 1)
        self.base_path = Path(self.config["paths"]["base"])

        # Initialize LLM gateway
        llm_mode = LLMMode.LOCAL if self.config["llm"]["default_mode"] == "local" else LLMMode.REMOTE
        self.gateway = LLMGateway(mode=llm_mode, config=self.config)

        # Initialize Retriever v2.1 gateway
        try:
            self.retrieval_gateway = J5ARetrievalGateway(self.config.get("retriever", {}))
            self.sherlock_retrieval = SherlockRetrieval(self.config.get("retriever", {}))
            logger.info("Retriever v2.1 gateway initialized")
        except Exception as e:
            logger.warning(f"Retriever v2.1 initialization failed: {e}")
            self.retrieval_gateway = None
            self.sherlock_retrieval = None

        # Initialize Governance logging
        if GOVERNANCE_AVAILABLE:
            try:
                self.gov_logger = GovernanceLogger(log_dir=str(self.base_path / "governance"))
                self.principles = StrategicPrinciples()
                logger.info("✅ Governance logging and Strategic Principles enabled")
            except Exception as e:
                logger.warning(f"Governance initialization failed: {e}")
                self.gov_logger = None
                self.principles = None
        else:
            self.gov_logger = None
            self.principles = None

        logger.info(f"J5A Worker initialized (Phase {self.phase}, LLM mode: {llm_mode.value})")

    def process_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single job from queue

        Args:
            job: Job definition dict with type, inputs, outputs, etc.

        Returns:
            Result dict with success, outputs, errors
        """
        job_id = job.get("job_id", "unknown")
        job_type = job.get("type", "")
        job_class = job.get("class", JobClass.STANDARD.value)

        logger.info(f"Processing job {job_id}: {job_type} (class: {job_class})")

        # Log job acceptance decision with governance
        if self.gov_logger:
            try:
                self.gov_logger.log_decision(
                    decision_type="job_processing",
                    context={
                        "job_id": job_id,
                        "job_type": job_type,
                        "job_class": job_class,
                        "phase": self.phase
                    },
                    decision={
                        "action": "accept_job",
                        "reasoning": f"Job {job_id} accepted for processing in Phase {self.phase}"
                    },
                    principle_alignment=[
                        "Principle 2: Transparency - Job processing logged",
                        "Strategic Principle 7: Autonomous Workflows - Night Shift operation"
                    ]
                )
            except Exception as e:
                logger.warning(f"Failed to log governance decision: {e}")

        # Phase 1: Park demanding jobs
        if self.phase == 1 and job_class == JobClass.DEMANDING.value:
            logger.info(f"Parking demanding job {job_id} (Phase 1 local-only)")

            # Log parking decision
            if self.gov_logger:
                try:
                    self.gov_logger.log_decision(
                        decision_type="job_deferral",
                        context={"job_id": job_id, "job_class": job_class, "phase": self.phase},
                        decision={
                            "action": "park_job",
                            "reasoning": "Demanding job parked in Phase 1 (local-only mode)"
                        },
                        principle_alignment=[
                            "Principle 4: Resource Stewardship - Respecting Phase 1 local-only constraint"
                        ]
                    )
                except Exception as e:
                    logger.warning(f"Failed to log parking decision: {e}")

            return {
                "success": False,
                "status": "parked",
                "reason": "Phase 1: Demanding jobs parked for Phase 2"
            }

        # Check thermal safety
        if not self._check_thermal_safe():
            logger.warning(f"Thermal unsafe, deferring job {job_id}")

            # Log thermal deferral decision
            if self.gov_logger:
                try:
                    self.gov_logger.log_decision(
                        decision_type="job_deferral",
                        context={"job_id": job_id, "reason": "thermal_safety"},
                        decision={
                            "action": "defer_job",
                            "reasoning": "CPU temperature exceeds safety threshold"
                        },
                        principle_alignment=[
                            "Principle 4: Resource Stewardship - Protecting hardware from thermal damage"
                        ]
                    )
                except Exception as e:
                    logger.warning(f"Failed to log thermal deferral: {e}")

            return {
                "success": False,
                "status": "deferred",
                "reason": "CPU temperature too high"
            }

        # Route to appropriate processor
        try:
            result = None

            if job_type == JobType.SUMMARY.value or job_type == JobType.RESEARCH_REPORT.value:
                result = self._process_summary_job(job)
            elif job_type == JobType.CODE_STUB.value:
                result = self._process_code_job(job)
            elif job_type == JobType.TRANSCRIPTION.value:
                result = self._process_transcription_job(job)
            elif job_type == JobType.PODCAST_TRANSCRIPTION.value:
                result = self._process_podcast_transcription_job(job)
            # v2.1 Retriever job types
            elif job_type == JobType.INTELLIGENCE_DISCOVERY.value:
                result = self._process_intelligence_discovery_job(job)
            elif job_type == JobType.DATABASE_QUERY.value:
                result = self._process_database_query_job(job)
            elif job_type == JobType.WEB_SCRAPING.value:
                result = self._process_web_scraping_job(job)
            elif job_type == JobType.ML_INFERENCE.value:
                result = self._process_ml_inference_job(job)
            elif job_type == JobType.MULTI_SOURCE_RETRIEVAL.value:
                result = self._process_multi_source_retrieval_job(job)
            else:
                result = {
                    "success": False,
                    "status": "failed",
                    "reason": f"Unknown job type: {job_type}"
                }

            # Log job completion with governance
            if self.gov_logger and result:
                try:
                    self.gov_logger.log_decision(
                        decision_type="job_completion",
                        context={
                            "job_id": job_id,
                            "job_type": job_type,
                            "success": result.get("success"),
                            "status": result.get("status")
                        },
                        decision={
                            "action": "complete_job",
                            "reasoning": f"Job {job_id} completed with status: {result.get('status')}",
                            "outputs": result.get("outputs", [])
                        },
                        principle_alignment=[
                            "Principle 2: Transparency - Job completion logged",
                            "Principle 3: System Viability - Job processed to completion"
                        ] if result.get("success") else [
                            "Principle 2: Transparency - Job failure logged for learning"
                        ]
                    )
                except Exception as e:
                    logger.warning(f"Failed to log job completion: {e}")

            return result

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)

            # Log job failure with governance
            if self.gov_logger:
                try:
                    self.gov_logger.log_decision(
                        decision_type="job_failure",
                        context={"job_id": job_id, "job_type": job_type, "error": str(e)},
                        decision={
                            "action": "fail_job",
                            "reasoning": f"Job {job_id} failed with exception: {str(e)[:200]}"
                        },
                        principle_alignment=[
                            "Principle 2: Transparency - Failure logged for debugging",
                            "Strategic Principle 5: Adaptive Feedback - Learning from failures"
                        ]
                    )
                except Exception as log_error:
                    logger.warning(f"Failed to log job failure: {log_error}")

            return {
                "success": False,
                "status": "failed",
                "reason": str(e)
            }

    def _process_summary_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process summary/research report job"""
        job_id = job["job_id"]
        inputs = job.get("inputs", [])

        if not inputs:
            return {"success": False, "reason": "No inputs provided"}

        # Ingest content
        txt_paths = []
        for input_spec in inputs:
            path_or_url = input_spec.get("path") or input_spec.get("url")
            if path_or_url:
                txt_path = ingest(path_or_url)
                txt_paths.append(txt_path)

        if not txt_paths:
            return {"success": False, "reason": "Content ingestion failed"}

        # Chunk and select excerpts (using first input for now)
        chunks_path = chunk(txt_paths[0])

        # Generate summary
        try:
            summary_path = summarize(
                chunks_path,
                mode=LLMMode.LOCAL,
                max_excerpts=10,
                max_tokens_input=self.config["llm"]["max_context"]
            )
        except ValueError as e:
            # LLM returned INSUFFICIENT_EVIDENCE or validation failed
            return {
                "success": True,  # Job completed, just insufficient data
                "status": "insufficient_evidence",
                "outputs": [],
                "reason": str(e)
            }

        # Validate summary
        if not validate_summary(summary_path, chunks_path):
            return {
                "success": False,
                "status": "validation_failed",
                "reason": "Summary validation failed (< 3 citations)"
            }

        return {
            "success": True,
            "status": "completed",
            "outputs": [summary_path],
            "validation": "passed"
        }

    def _process_code_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process code generation job"""
        job_id = job["job_id"]

        # Load contract
        contract_path = self.base_path / "contracts" / "code_stub_contract.txt"
        with open(contract_path) as f:
            contract = f.read()

        # Get function spec and tests from inputs
        inputs = job.get("inputs", [])
        if not inputs:
            return {"success": False, "reason": "No inputs (need spec + tests)"}

        # Ingest spec and tests
        excerpts = []
        for input_spec in inputs:
            path = input_spec.get("path")
            if path:
                txt_path = ingest(path)
                with open(txt_path, 'r') as f:
                    excerpts.append({
                        "text": f.read(),
                        "source": Path(path).name,
                        "score": 1.0
                    })

        # Generate code
        code_text = self.gateway.complete(
            instructions=contract,
            excerpts=excerpts,
            limits={"max_output": self.config["llm"]["max_output"]}
        )

        # Save code
        output_dir = self.base_path / "ops" / "outputs"
        code_path = output_dir / f"{job_id}_generated.py"

        with open(code_path, 'w') as f:
            f.write(code_text)

        # Find test file (if provided)
        test_path = None
        for input_spec in inputs:
            if "test" in input_spec.get("path", "").lower():
                test_path = input_spec["path"]
                break

        # Validate code
        if not validate_code_file(str(code_path), test_path):
            return {
                "success": False,
                "status": "validation_failed",
                "reason": "Code validation failed (ruff/mypy/pytest)"
            }

        return {
            "success": True,
            "status": "completed",
            "outputs": [str(code_path)],
            "validation": "passed"
        }

    def _process_transcription_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process audio transcription job with Whisper"""
        import subprocess
        import requests
        import tempfile
        import shutil
        from urllib.parse import urlparse

        job_id = job["job_id"]
        inputs = job.get("inputs", [])
        outputs = job.get("outputs", [])
        metadata = job.get("metadata", {})

        logger.info(f"Starting transcription job: {job_id}")

        if not inputs:
            return {"success": False, "reason": "No inputs provided"}

        # Get audio source
        input_spec = inputs[0]
        source_url = input_spec.get("source") or input_spec.get("url") or input_spec.get("path")
        episode = input_spec.get("episode")

        if not source_url:
            return {"success": False, "reason": "No audio source provided"}

        # Determine audio file location or download URL
        audio_file = None
        temp_dir = None

        try:
            # Check if it's a local file
            if Path(source_url).exists():
                audio_file = source_url
            else:
                # Try to download from URL
                logger.info(f"Downloading audio from: {source_url}")
                temp_dir = Path(tempfile.mkdtemp())
                audio_file = temp_dir / f"episode_{episode}.mp3"

                # Use youtube-dl/yt-dlp if available for podcast feeds
                # For now, try direct download
                try:
                    response = requests.get(source_url, stream=True, timeout=30)
                    if response.status_code == 200:
                        with open(audio_file, 'wb') as f:
                            shutil.copyfileobj(response.raw, f)
                    else:
                        return {"success": False, "reason": f"Failed to download audio: HTTP {response.status_code}"}
                except requests.RequestException as e:
                    return {"success": False, "reason": f"Download failed: {e}"}

            if not Path(audio_file).exists():
                return {"success": False, "reason": "Audio file not found"}

            logger.info(f"Audio file ready: {audio_file}")

            # Prepare output paths
            output_txt = None
            output_json = None

            for output_spec in outputs:
                path = output_spec.get("path")
                if path:
                    # Create output directory
                    Path(path).parent.mkdir(parents=True, exist_ok=True)

                    if output_spec.get("format") == "txt" or path.endswith(".txt"):
                        output_txt = path
                    elif output_spec.get("format") == "json" or path.endswith(".json"):
                        output_json = path

            # Run Whisper transcription
            logger.info("Running Whisper transcription (this may take a while)...")

            # Create temporary output directory for Whisper
            whisper_output_dir = temp_dir or Path(tempfile.mkdtemp())

            # Whisper command with speaker diarization (if supported by installed version)
            # Note: Basic openai-whisper doesn't have built-in diarization
            # Using 'large' model for best accuracy
            whisper_cmd = [
                "whisper",
                str(audio_file),
                "--model", "large",
                "--output_dir", str(whisper_output_dir),
                "--output_format", "all",  # Get multiple formats
                "--verbose", "False"
            ]

            logger.info(f"Whisper command: {' '.join(whisper_cmd)}")

            result = subprocess.run(
                whisper_cmd,
                capture_output=True,
                text=True,
                timeout=7200  # 2 hour timeout for long episodes
            )

            if result.returncode != 0:
                logger.error(f"Whisper failed: {result.stderr}")
                return {
                    "success": False,
                    "reason": f"Whisper transcription failed: {result.stderr[:500]}"
                }

            logger.info("Whisper transcription completed")

            # Find generated files
            audio_basename = Path(audio_file).stem
            whisper_txt = whisper_output_dir / f"{audio_basename}.txt"
            whisper_json = whisper_output_dir / f"{audio_basename}.json"

            # Copy outputs to specified locations
            generated_outputs = []

            if output_txt and whisper_txt.exists():
                shutil.copy(whisper_txt, output_txt)
                generated_outputs.append(output_txt)
                logger.info(f"Saved transcript: {output_txt}")

            if output_json and whisper_json.exists():
                shutil.copy(whisper_json, output_json)
                generated_outputs.append(output_json)
                logger.info(f"Saved JSON: {output_json}")

            if not generated_outputs:
                return {
                    "success": False,
                    "reason": "Whisper completed but no output files found"
                }

            return {
                "success": True,
                "status": "completed",
                "outputs": generated_outputs,
                "validation": "transcription_completed"
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "reason": "Transcription timeout (>2 hours)"
            }
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            return {
                "success": False,
                "reason": f"Transcription error: {str(e)}"
            }
        finally:
            # Cleanup temporary files
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp dir: {e}")

    def _process_podcast_transcription_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process podcast transcription using RSS-first podcast intelligence pipeline
        Phases 1-3: Night Shift (discovery, download, transcription)
        Phase 4: Automatically queued to Claude (intelligence extraction)
        """
        import subprocess
        import sys

        job_id = job["job_id"]
        inputs = job.get("inputs", {})

        logger.info(f"Starting podcast transcription job: {job_id}")

        # Extract parameters
        rss_feed = inputs.get("rss_feed")
        episode_number = inputs.get("episode_number")
        episode_title = inputs.get("episode_title")
        episode_url = inputs.get("episode_url")

        if not rss_feed:
            return {"success": False, "reason": "No RSS feed URL provided"}

        if not episode_number and not episode_title:
            return {"success": False, "reason": "Must specify either episode_number or episode_title"}

        # Build command for podcast intelligence pipeline
        pipeline_path = self.base_path / "ops" / "fetchers" / "podcast_intelligence_pipeline.py"

        cmd = [
            sys.executable,
            str(pipeline_path),
            "--rss-feed", rss_feed,
            "--output-dir", str(self.base_path / "ops" / "outputs" / "podcast_intelligence"),
            "--claude-queue-dir", "/home/johnny5/Johny5Alive/queue/claude"
        ]

        if episode_number:
            cmd.extend(["--episode-number", str(episode_number)])

        if episode_title:
            cmd.extend(["--episode-title", episode_title])

        if episode_url:
            cmd.extend(["--episode-url", episode_url])

        logger.info(f"Running podcast pipeline: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=7200  # 2 hour timeout for full pipeline
            )

            if result.returncode != 0:
                logger.error(f"Podcast pipeline failed: {result.stderr}")
                return {
                    "success": False,
                    "status": "failed",
                    "reason": f"Pipeline error: {result.stderr[:500]}"
                }

            logger.info("Podcast transcription completed successfully")
            logger.info(f"Pipeline output:\n{result.stdout}")

            # Parse outputs from pipeline
            # The pipeline saves transcripts and queues Claude job automatically
            outputs = [
                str(self.base_path / "ops" / "outputs" / "podcast_intelligence" / "transcripts" / f"episode_{episode_number}_transcript.txt"),
                str(self.base_path / "ops" / "outputs" / "podcast_intelligence" / "transcripts" / f"episode_{episode_number}_transcript.json")
            ]

            return {
                "success": True,
                "status": "completed",
                "outputs": outputs,
                "validation": "transcription_completed_claude_queued",
                "message": "Transcript ready. Intelligence extraction queued for Claude."
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "status": "failed",
                "reason": "Pipeline timeout (>2 hours)"
            }
        except Exception as e:
            logger.error(f"Podcast transcription failed: {e}", exc_info=True)
            return {
                "success": False,
                "status": "failed",
                "reason": f"Error: {str(e)}"
            }

    # =================================================================
    # v2.1 Retriever Job Processors
    # =================================================================

    def _process_intelligence_discovery_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process intelligence source discovery job using Sherlock Retrieval"""
        job_id = job["job_id"]
        inputs = job.get("inputs", {})

        if not self.sherlock_retrieval:
            return {
                "success": False,
                "reason": "Sherlock Retrieval not available"
            }

        logger.info(f"Intelligence discovery job: {job_id}")

        topic = inputs.get("topic")
        source_types = inputs.get("source_types", ["files", "web", "databases"])
        search_depth = inputs.get("search_depth", "standard")

        if not topic:
            return {"success": False, "reason": "No topic provided"}

        try:
            result = self.sherlock_retrieval.discover_intelligence_sources(
                topic=topic,
                source_types=source_types,
                search_depth=search_depth
            )

            # Save discovered sources to output
            output_dir = self.base_path / "ops" / "outputs"
            output_path = output_dir / f"{job_id}_discovered_sources.json"

            import json
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)

            return {
                "success": True,
                "status": "completed",
                "outputs": [str(output_path)],
                "sources_found": result.get("sources_found", 0),
                "validation": "discovery_completed"
            }

        except Exception as e:
            logger.error(f"Intelligence discovery failed: {e}", exc_info=True)
            return {
                "success": False,
                "status": "failed",
                "reason": str(e)
            }

    def _process_database_query_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process database query job"""
        job_id = job["job_id"]
        inputs = job.get("inputs", {})

        if not self.retrieval_gateway:
            return {
                "success": False,
                "reason": "Retrieval gateway not available"
            }

        logger.info(f"Database query job: {job_id}")

        query = inputs.get("query")
        database_type = inputs.get("database_type", "sqlite")
        database_path = inputs.get("database_path")

        if not query:
            return {"success": False, "reason": "No query provided"}

        try:
            result = self.retrieval_gateway.sherlock_query_database(
                query=query,
                database_type=database_type,
                database=database_path
            )

            # Save query results
            output_dir = self.base_path / "ops" / "outputs"
            output_path = output_dir / f"{job_id}_query_results.json"

            import json
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)

            return {
                "success": True,
                "status": "completed",
                "outputs": [str(output_path)],
                "row_count": result.get("row_count", result.get("count", 0)),
                "validation": "query_completed"
            }

        except Exception as e:
            logger.error(f"Database query failed: {e}", exc_info=True)
            return {
                "success": False,
                "status": "failed",
                "reason": str(e)
            }

    def _process_web_scraping_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process web scraping job"""
        job_id = job["job_id"]
        inputs = job.get("inputs", {})

        if not self.retrieval_gateway:
            return {
                "success": False,
                "reason": "Retrieval gateway not available"
            }

        logger.info(f"Web scraping job: {job_id}")

        url = inputs.get("url")
        selectors = inputs.get("selectors", {})
        wait_for = inputs.get("wait_for")
        screenshot = inputs.get("screenshot", False)

        if not url:
            return {"success": False, "reason": "No URL provided"}

        try:
            # Get webscraper agent
            scraper = self.retrieval_gateway._get_webscraper_agent()

            result = scraper.retrieve({
                "type": "webscraper",
                "url": url,
                "selectors": selectors,
                "wait_for": wait_for,
                "screenshot": screenshot,
                "backend": inputs.get("backend", "selenium"),
                "headless": inputs.get("headless", True)
            })

            # Save scraped data
            output_dir = self.base_path / "ops" / "outputs"
            output_path = output_dir / f"{job_id}_scraped_data.json"

            import json
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)

            outputs = [str(output_path)]
            if result.get("screenshot_path"):
                outputs.append(result["screenshot_path"])

            return {
                "success": True,
                "status": "completed",
                "outputs": outputs,
                "validation": "scraping_completed"
            }

        except Exception as e:
            logger.error(f"Web scraping failed: {e}", exc_info=True)
            return {
                "success": False,
                "status": "failed",
                "reason": str(e)
            }

    def _process_ml_inference_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process ML inference job"""
        job_id = job["job_id"]
        inputs = job.get("inputs", {})

        if not self.retrieval_gateway:
            return {
                "success": False,
                "reason": "Retrieval gateway not available"
            }

        logger.info(f"ML inference job: {job_id}")

        model_path = inputs.get("model_path")
        input_data = inputs.get("input_data")
        operation = inputs.get("operation", "predict")

        if not model_path or input_data is None:
            return {"success": False, "reason": "Missing model_path or input_data"}

        try:
            result = self.retrieval_gateway.nightshift_ml_inference(
                model_path=model_path,
                input_data=input_data,
                operation=operation,
                preprocess=inputs.get("preprocess"),
                postprocess=inputs.get("postprocess")
            )

            # Save inference results
            output_dir = self.base_path / "ops" / "outputs"
            output_path = output_dir / f"{job_id}_ml_predictions.json"

            import json
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)

            return {
                "success": True,
                "status": "completed",
                "outputs": [str(output_path)],
                "prediction_count": result.get("prediction_count", 0),
                "validation": "inference_completed"
            }

        except Exception as e:
            logger.error(f"ML inference failed: {e}", exc_info=True)
            return {
                "success": False,
                "status": "failed",
                "reason": str(e)
            }

    def _process_multi_source_retrieval_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Process multi-source retrieval job with intelligent orchestration"""
        job_id = job["job_id"]
        inputs = job.get("inputs", {})

        if not self.retrieval_gateway:
            return {
                "success": False,
                "reason": "Retrieval gateway not available"
            }

        logger.info(f"Multi-source retrieval job: {job_id}")

        query = inputs.get("query")
        if not query:
            return {"success": False, "reason": "No query provided"}

        try:
            # Use intelligent multi-step retrieval
            result = self.retrieval_gateway.retrieve_multi_step(
                query=query,
                **inputs
            )

            # Save results
            output_dir = self.base_path / "ops" / "outputs"
            output_path = output_dir / f"{job_id}_multi_source_results.json"

            import json
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)

            return {
                "success": True,
                "status": "completed",
                "outputs": [str(output_path)],
                "steps_completed": result.get("steps_completed", 0),
                "validation": "multi_source_completed"
            }

        except Exception as e:
            logger.error(f"Multi-source retrieval failed: {e}", exc_info=True)
            return {
                "success": False,
                "status": "failed",
                "reason": str(e)
            }

    # =================================================================
    # Helper Methods
    # =================================================================

    def _check_thermal_safe(self) -> bool:
        """Check if CPU temperature is safe for processing"""
        thermal_limit = self.config["resources"]["thermal_limit_celsius"]

        try:
            # Try to get CPU temperature
            import subprocess
            result = subprocess.run(
                ['sensors'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse temperature from output
                for line in result.stdout.split('\n'):
                    if 'Package id 0' in line or 'Core 0' in line:
                        # Extract temperature (format: +XX.X°C)
                        import re
                        match = re.search(r'\+(\d+\.\d+)°C', line)
                        if match:
                            temp = float(match.group(1))
                            if temp > thermal_limit:
                                logger.warning(f"CPU temp {temp}°C exceeds limit {thermal_limit}°C")
                                return False
                            return True

        except Exception as e:
            logger.warning(f"Could not check thermal status: {e}")
            # If we can't check, assume safe (better than blocking all jobs)
            return True

        return True


def process_queue(worker: J5AWorker, queue_db_path: str = None):
    """
    Process jobs from queue database

    Args:
        worker: J5AWorker instance
        queue_db_path: Path to queue database (default: from config)
    """
    if queue_db_path is None:
        queue_db_path = worker.config["paths"]["queue_db"]

    # Connect to queue database
    conn = sqlite3.connect(queue_db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name

    try:
        # Find queued jobs
        cursor = conn.execute("""
            SELECT * FROM task_executions
            WHERE status = 'queued'
            ORDER BY priority ASC, created_timestamp ASC
            LIMIT 10
        """)

        jobs = cursor.fetchall()
        logger.info(f"Found {len(jobs)} queued jobs")

        for job_row in jobs:
            job = dict(job_row)

            # Process job
            result = worker.process_job(job)

            # Update status
            new_status = result.get("status", "failed")
            outputs = json.dumps(result.get("outputs", []))

            conn.execute("""
                UPDATE task_executions
                SET status = ?, outputs = ?, updated_timestamp = ?
                WHERE task_id = ?
            """, (new_status, outputs, datetime.now().isoformat(), job["task_id"]))

            conn.commit()

            logger.info(f"Job {job['task_id']}: {new_status}")

    finally:
        conn.close()


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize worker
    worker = J5AWorker()

    # Test with sample job
    test_job = {
        "job_id": "test_001",
        "type": "summary",
        "class": "standard",
        "inputs": [
            {"path": "/home/johnny5/Johny5Alive/j5a-nightshift/ops/inbox/test_input.txt"}
        ],
        "outputs": [
            {"kind": "markdown", "path": "/home/johnny5/Johny5Alive/j5a-nightshift/ops/outputs/test_summary.md"}
        ]
    }

    # Create test input if doesn't exist
    test_input_path = test_job["inputs"][0]["path"]
    os.makedirs(os.path.dirname(test_input_path), exist_ok=True)

    if not os.path.exists(test_input_path):
        with open(test_input_path, 'w') as f:
            f.write("""
# Introduction to Autonomous Systems

Autonomous systems are capable of performing tasks without human intervention.
They use sensors, algorithms, and machine learning to make decisions.

# Applications

Autonomous systems are used in:
- Self-driving cars
- Robotics
- Drone delivery
- Industrial automation

# Challenges

Key challenges include safety, reliability, and ethical considerations.
            """.strip())

    print("Testing J5A Worker with sample job...")
    result = worker.process_job(test_job)

    print("\n" + "="*60)
    print("JOB RESULT:")
    print("="*60)
    print(f"Success: {result.get('success')}")
    print(f"Status: {result.get('status')}")
    if result.get('outputs'):
        print(f"Outputs: {result['outputs']}")
    if result.get('reason'):
        print(f"Reason: {result['reason']}")
