#!/usr/bin/env python3
"""
Podcast Fetcher with Robust Web Fetcher Integration
Finds and downloads podcast audio files from episode pages
"""

import sys
import os
import json
import argparse
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Add RWF to path
RWF_PATH = Path(__file__).parent / "robust-web-fetcher"
sys.path.insert(0, str(RWF_PATH))

from robust_web_fetcher import RobustWebFetcher

logger = logging.getLogger(__name__)


class PodcastFetcher:
    """Fetch podcast audio using RWF + LLM guidance"""

    def __init__(self, model: str = "qwen2.5:7b-instruct", endpoint: str = "http://localhost:11434"):
        self.model = model
        self.endpoint = endpoint
        self.rf = RobustWebFetcher()

    def fetch_page(self, url: str) -> Dict:
        """Fetch episode page with RWF"""
        logger.info(f"Fetching page: {url}")
        result = self.rf.fetch(url, render_js=True, extract_media=True)
        return result

    def find_audio_candidates(self, rwf_result: Dict) -> List[Dict]:
        """Use LLM to identify audio URL candidates from RWF result"""
        # Load contract
        contract_path = Path(__file__).parents[2] / "contracts" / "find_candidates_rwf.txt"

        if not contract_path.exists():
            logger.warning(f"Contract not found: {contract_path}")
            return self._fallback_find_audio(rwf_result)

        with open(contract_path) as f:
            prompt = f.read().strip()

        # Build context from RWF result
        context = json.dumps({
            "media_urls": rwf_result.get("media_urls", []),
            "links": rwf_result.get("links", [])[:50],  # Limit links
            "meta_tags": rwf_result.get("meta_tags", {})
        }, indent=2)

        # Query LLM
        try:
            import requests
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{prompt}\n\nDATA:\n{context}\n\nOUTPUT:",
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                llm_output = response.json().get("response", "")
                # Parse JSON from response
                try:
                    candidates = json.loads(llm_output)
                    logger.info(f"LLM found {len(candidates)} candidates")
                    return candidates
                except json.JSONDecodeError:
                    logger.warning("LLM output not valid JSON")
                    return self._fallback_find_audio(rwf_result)
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return self._fallback_find_audio(rwf_result)

    def _fallback_find_audio(self, rwf_result: Dict) -> List[Dict]:
        """Simple fallback audio detection"""
        candidates = []

        # Check media_urls first
        for url in rwf_result.get("media_urls", []):
            if any(ext in url.lower() for ext in [".mp3", ".m4a", ".ogg", ".aac"]):
                candidates.append({
                    "url": url,
                    "reason": "Direct media URL",
                    "confidence": 0.9
                })

        # Check links
        for link in rwf_result.get("links", []):
            url = link.get("href", "")
            if any(ext in url.lower() for ext in [".mp3", ".m4a"]):
                candidates.append({
                    "url": url,
                    "reason": "Audio file link",
                    "confidence": 0.7
                })

        return candidates[:5]

    def generate_download_command(self, audio_url: str) -> Optional[Dict]:
        """Use LLM to generate appropriate download command"""
        contract_path = Path(__file__).parents[2] / "contracts" / "download_command_rwf.txt"

        if not contract_path.exists():
            logger.warning(f"Contract not found: {contract_path}")
            return self._fallback_download_command(audio_url)

        with open(contract_path) as f:
            prompt = f.read().strip()

        # Query LLM
        try:
            import requests
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{prompt}\n\nURL: {audio_url}\n\nOUTPUT:",
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                llm_output = response.json().get("response", "")
                try:
                    cmd_info = json.loads(llm_output)
                    return cmd_info
                except json.JSONDecodeError:
                    logger.warning("LLM output not valid JSON")
                    return self._fallback_download_command(audio_url)
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return self._fallback_download_command(audio_url)

    def _fallback_download_command(self, audio_url: str) -> Dict:
        """Simple fallback download command generation"""
        if ".m3u8" in audio_url.lower():
            return {
                "cmd": f'ffmpeg -i "{audio_url}" -c copy "episode.ts"',
                "explain": "HLS stream, using ffmpeg"
            }
        else:
            return {
                "cmd": f'curl -L --retry 5 -o "episode.mp3" "{audio_url}"',
                "explain": "Direct file, using curl"
            }

    def download_audio(self, audio_url: str, output_path: Path) -> bool:
        """Download audio file"""
        logger.info(f"Downloading from: {audio_url}")

        cmd_info = self.generate_download_command(audio_url)
        if not cmd_info:
            logger.error("Could not generate download command")
            return False

        # Update command with actual output path
        cmd = cmd_info["cmd"]
        if "episode.mp3" in cmd:
            cmd = cmd.replace("episode.mp3", str(output_path))
        elif "episode.ts" in cmd:
            cmd = cmd.replace("episode.ts", str(output_path.with_suffix(".ts")))

        logger.info(f"Running: {cmd}")
        logger.info(f"Explanation: {cmd_info['explain']}")

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )

            if result.returncode == 0:
                logger.info(f"Download successful: {output_path}")
                return True
            else:
                logger.error(f"Download failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Download timeout")
            return False
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Fetch podcast audio with RWF")
    parser.add_argument("--url", required=True, help="Episode page URL")
    parser.add_argument("--title", required=True, help="Episode title")
    parser.add_argument("--model", default="qwen2.5:7b-instruct", help="LLM model")
    parser.add_argument("--endpoint", default="http://localhost:11434", help="Ollama endpoint")
    parser.add_argument("--outdir", default="ops/outputs/podcast_download", help="Output directory")
    parser.add_argument("--log", default="ops/logs/podcast_fetch.log", help="Log file")

    args = parser.parse_args()

    # Setup logging
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

    # Create output directory
    output_dir = Path(args.outdir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize fetcher
    fetcher = PodcastFetcher(model=args.model, endpoint=args.endpoint)

    # Fetch page
    logger.info(f"Processing: {args.title}")
    rwf_result = fetcher.fetch_page(args.url)

    # Save RWF result
    result_path = output_dir / "rwf_result.json"
    with open(result_path, "w") as f:
        json.dump(rwf_result, f, indent=2)
    logger.info(f"RWF result saved: {result_path}")

    # Find audio candidates
    candidates = fetcher.find_audio_candidates(rwf_result)

    if not candidates:
        logger.error("No audio candidates found")
        return 1

    # Save candidates
    candidates_path = output_dir / "audio_candidates.json"
    with open(candidates_path, "w") as f:
        json.dump(candidates, f, indent=2)
    logger.info(f"Found {len(candidates)} candidates: {candidates_path}")

    # Try to download from best candidate
    for i, candidate in enumerate(candidates, 1):
        logger.info(f"Trying candidate {i}/{len(candidates)}: {candidate['url']}")
        logger.info(f"  Reason: {candidate['reason']}")
        logger.info(f"  Confidence: {candidate['confidence']}")

        # Determine output file extension
        url = candidate["url"]
        if ".m3u8" in url.lower():
            ext = ".ts"
        elif ".m4a" in url.lower():
            ext = ".m4a"
        else:
            ext = ".mp3"

        output_path = output_dir / f"episode{ext}"

        if fetcher.download_audio(url, output_path):
            logger.info(f"✅ Successfully downloaded: {output_path}")

            # Save success info
            success_info = {
                "title": args.title,
                "url": args.url,
                "audio_url": url,
                "output_file": str(output_path),
                "candidate_rank": i,
                "confidence": candidate["confidence"]
            }

            success_path = output_dir / "download_success.json"
            with open(success_path, "w") as f:
                json.dump(success_info, f, indent=2)

            return 0
        else:
            logger.warning(f"❌ Candidate {i} failed, trying next...")

    logger.error("All candidates failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
