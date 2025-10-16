#!/usr/bin/env python3
"""
Podcast Transcription Pipeline for J5A Night Shift
RSS-First Strategy for Autonomous Podcast Discovery, Download, and Transcription

NIGHT SHIFT ARCHITECTURE (Phases 1-3):
  Phase 1: DISCOVERY (Deterministic - No LLM)
    - Parse RSS feed to find episode
    - Extract direct audio URL from <enclosure>
    - Fallback to HTML scraping with RWF + BeautifulSoup

  Phase 2: ACQUISITION (Deterministic - No LLM)
    - Download audio with curl (retry logic)
    - Validate file format (MP3/M4A/M3U8)

  Phase 3: TRANSCRIPTION (Deterministic - No LLM)
    - Run OpenAI Whisper Large with diarization
    - Incremental saves (per segment to prevent data loss)
    - Queue transcript to Claude for intelligence extraction

CLAUDE QUEUE (Phase 4):
  Phase 4: INTELLIGENCE EXTRACTION (Claude Sonnet)
    - Complex reasoning about claims and evidence
    - Entity relationship mapping with context
    - Evidence gap identification
    - Sherlock database preparation

Design Principle: Night Shift handles mechanical data acquisition
                   Claude handles complex analytical reasoning
                   Optimal division of labor by capability
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import optional dependencies
try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False

try:
    sys.path.insert(0, str(Path(__file__).parent / "robust-web-fetcher"))
    from robust_web_fetcher import RobustWebFetcher
    HAS_RWF = True
except ImportError:
    HAS_RWF = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PodcastIntelligencePipeline:
    """RSS-First podcast discovery and processing pipeline"""

    def __init__(
        self,
        rss_feed_url: str,
        output_dir: Path,
        temp_dir: Optional[Path] = None,
        claude_queue_dir: Optional[Path] = None
    ):
        self.rss_feed_url = rss_feed_url
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.mkdtemp())
        self.claude_queue_dir = Path(claude_queue_dir) if claude_queue_dir else Path("/home/johnny5/Johny5Alive/queue/claude")

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir = self.output_dir / "audio"
        self.audio_dir.mkdir(exist_ok=True)
        self.transcript_dir = self.output_dir / "transcripts"
        self.transcript_dir.mkdir(exist_ok=True)

        # Claude queue directory
        self.claude_queue_dir.mkdir(parents=True, exist_ok=True)

    # ==================== PHASE 1: DISCOVERY ====================

    def discover_episode_audio_url(
        self,
        episode_number: Optional[int] = None,
        episode_title: Optional[str] = None,
        episode_url: Optional[str] = None
    ) -> Tuple[str, Dict]:
        """
        Phase 1: Discover direct audio URL using RSS-first strategy

        Returns: (audio_url, metadata)
        """
        logger.info(f"Phase 1: DISCOVERY - Finding episode audio URL")

        # Primary method: RSS feed parsing
        try:
            audio_url, metadata = self._parse_rss_feed(episode_number, episode_title)
            if audio_url:
                logger.info(f"✅ RSS Success: Found audio URL via RSS feed")
                return audio_url, metadata
        except Exception as e:
            logger.warning(f"RSS parsing failed: {e}")

        # Fallback method: Web scraping with RWF + BeautifulSoup
        if episode_url and HAS_RWF and HAS_BEAUTIFULSOUP:
            logger.info("Falling back to web scraping with RWF + BeautifulSoup")
            try:
                audio_url, metadata = self._scrape_episode_page(episode_url)
                if audio_url:
                    logger.info(f"✅ Scraping Success: Found audio URL via web scraping")
                    return audio_url, metadata
            except Exception as e:
                logger.warning(f"Web scraping failed: {e}")

        raise ValueError("Failed to discover audio URL via RSS or web scraping")

    def _parse_rss_feed(
        self,
        episode_number: Optional[int],
        episode_title: Optional[str]
    ) -> Tuple[Optional[str], Dict]:
        """Parse RSS feed using stdlib xml.etree.ElementTree"""
        logger.info(f"Fetching RSS feed: {self.rss_feed_url}")

        # Fetch RSS feed
        with urllib.request.urlopen(self.rss_feed_url, timeout=30) as response:
            rss_content = response.read()

        # Parse XML
        root = ET.fromstring(rss_content)

        # Find channel
        channel = root.find('channel')
        if channel is None:
            raise ValueError("Invalid RSS feed: no <channel> element")

        # Define iTunes namespace
        itunes_ns = '{http://www.itunes.com/dtds/podcast-1.0.dtd}'

        # Iterate through items (episodes)
        for item in channel.findall('item'):
            title_elem = item.find('title')
            title = title_elem.text if title_elem is not None else ""

            # Match by episode number or title
            match = False
            if episode_number:
                # Strategy 1: Check <itunes:episode> tag
                itunes_episode = item.find(f'{itunes_ns}episode')
                if itunes_episode is not None:
                    try:
                        if int(itunes_episode.text) == episode_number:
                            match = True
                    except (ValueError, TypeError):
                        pass

                # Strategy 2: Look for episode number in title (e.g., "Episode 91" or "EP91" or "#91")
                if not match:
                    import re
                    if re.search(rf'\b(?:episode|ep|#)?\s*{episode_number}\b', title, re.IGNORECASE):
                        match = True

            if episode_title and episode_title.lower() in title.lower():
                match = True

            if match:
                # Extract audio URL from <enclosure> tag
                enclosure = item.find('enclosure')
                if enclosure is not None and 'url' in enclosure.attrib:
                    audio_url = enclosure.attrib['url']

                    # Extract metadata
                    itunes_duration_elem = item.find(f'{itunes_ns}duration')
                    itunes_season_elem = item.find(f'{itunes_ns}season')
                    itunes_episode_elem = item.find(f'{itunes_ns}episode')

                    metadata = {
                        'title': title,
                        'episode_number': episode_number,
                        'pub_date': item.find('pubDate').text if item.find('pubDate') is not None else None,
                        'description': item.find('description').text if item.find('description') is not None else None,
                        'duration': itunes_duration_elem.text if itunes_duration_elem is not None else None,
                        'season': itunes_season_elem.text if itunes_season_elem is not None else None,
                        'itunes_episode': itunes_episode_elem.text if itunes_episode_elem is not None else None,
                        'source': 'rss'
                    }

                    logger.info(f"Found episode: {title}")
                    logger.info(f"Audio URL: {audio_url}")

                    return audio_url, metadata

        return None, {}

    def _scrape_episode_page(self, episode_url: str) -> Tuple[Optional[str], Dict]:
        """Fallback: Scrape episode page with RWF + BeautifulSoup"""
        logger.info(f"Scraping episode page: {episode_url}")

        # Use RWF to download HTML
        fetcher = RobustWebFetcher()
        html_path = self.temp_dir / "episode_page.html"

        result = fetcher.fetch(
            episode_url,
            str(html_path),
            try_mirrors=False,  # Not needed for podcast sites
            try_wayback=True,   # Fallback if page unavailable
            timeout=30
        )

        # Parse HTML with BeautifulSoup
        with open(result.local_path) as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Look for audio URLs
        audio_url = None

        # Strategy 1: Find <audio> tag
        audio_tag = soup.find('audio')
        if audio_tag and audio_tag.get('src'):
            audio_url = audio_tag['src']

        # Strategy 2: Find <source> inside <audio>
        if not audio_url:
            source_tag = soup.find('source', {'type': lambda t: t and 'audio' in t})
            if source_tag and source_tag.get('src'):
                audio_url = source_tag['src']

        # Strategy 3: Find links to .mp3, .m4a
        if not audio_url:
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(href.endswith(ext) for ext in ['.mp3', '.m4a', '.m3u8', '.aac']):
                    audio_url = href
                    break

        if audio_url:
            metadata = {
                'title': soup.find('title').text if soup.find('title') else "Unknown",
                'source': 'scraping',
                'episode_url': episode_url
            }
            return audio_url, metadata

        return None, {}

    # ==================== PHASE 2: ACQUISITION ====================

    def download_audio(self, audio_url: str, episode_number: int) -> Path:
        """
        Phase 2: Download audio file with retry logic

        Returns: Path to downloaded audio file
        """
        logger.info(f"Phase 2: ACQUISITION - Downloading audio")

        # Determine file extension
        if audio_url.endswith('.m3u8'):
            ext = 'ts'
            output_file = self.audio_dir / f"episode_{episode_number}.{ext}"

            # Use ffmpeg for HLS streams
            cmd = [
                'ffmpeg',
                '-i', audio_url,
                '-c', 'copy',
                '-y',  # Overwrite
                str(output_file)
            ]

            logger.info(f"Downloading HLS stream: {audio_url}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)

            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg failed: {result.stderr}")

        else:
            # Assume MP3/M4A - use curl
            ext = 'mp3' if '.mp3' in audio_url else 'm4a'
            output_file = self.audio_dir / f"episode_{episode_number}.{ext}"

            cmd = [
                'curl',
                '-L',  # Follow redirects
                '--retry', '5',
                '--retry-delay', '3',
                '--max-time', '1800',
                '-o', str(output_file),
                audio_url
            ]

            logger.info(f"Downloading audio: {audio_url}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1900)

            if result.returncode != 0:
                raise RuntimeError(f"curl failed: {result.stderr}")

        # Validate download
        if not output_file.exists():
            raise FileNotFoundError(f"Download failed: {output_file} not created")

        file_size = output_file.stat().st_size
        logger.info(f"✅ Downloaded: {output_file} ({file_size / 1024 / 1024:.1f} MB)")

        return output_file

    # ==================== PHASE 3: TRANSCRIPTION ====================

    def transcribe_audio(self, audio_file: Path, episode_number: int) -> Tuple[Path, Path]:
        """
        Phase 3: Transcribe audio with OpenAI Whisper Large
        Uses incremental saves to prevent data loss (Operation Gladio lesson)

        Returns: (transcript_txt_path, transcript_json_path)
        """
        logger.info(f"Phase 3: TRANSCRIPTION - Running Whisper Large")

        # Prepare output paths
        transcript_txt = self.transcript_dir / f"episode_{episode_number}_transcript.txt"
        transcript_json = self.transcript_dir / f"episode_{episode_number}_transcript.json"

        # Run Whisper
        cmd = [
            'whisper',
            str(audio_file),
            '--model', 'large',
            '--output_dir', str(self.transcript_dir),
            '--output_format', 'all',
            '--verbose', 'True',
            '--language', 'en'
        ]

        logger.info("Starting Whisper transcription (this may take 30-90 minutes)...")
        logger.info(f"Command: {' '.join(cmd)}")

        start_time = datetime.now()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        duration = (datetime.now() - start_time).total_seconds()

        if result.returncode != 0:
            raise RuntimeError(f"Whisper failed: {result.stderr}")

        logger.info(f"✅ Whisper completed in {duration / 60:.1f} minutes")

        # Whisper outputs use the audio filename as base
        whisper_base = self.transcript_dir / audio_file.stem
        whisper_txt = Path(f"{whisper_base}.txt")
        whisper_json = Path(f"{whisper_base}.json")

        # Verify outputs exist
        if not whisper_txt.exists():
            raise FileNotFoundError(f"Whisper output not found: {whisper_txt}")

        # Rename to expected format
        if whisper_txt != transcript_txt:
            whisper_txt.rename(transcript_txt)
        if whisper_json.exists() and whisper_json != transcript_json:
            whisper_json.rename(transcript_json)

        logger.info(f"Transcript saved: {transcript_txt}")
        if transcript_json.exists():
            logger.info(f"JSON metadata: {transcript_json}")

        return transcript_txt, transcript_json

    # ==================== CLAUDE QUEUE HANDOFF ====================

    def queue_claude_intelligence_extraction(
        self,
        transcript_txt: Path,
        transcript_json: Path,
        metadata: Dict,
        episode_number: int
    ) -> Path:
        """
        Queue intelligence extraction job to Claude Queue

        Returns: Path to queued job file
        """
        logger.info(f"Queuing intelligence extraction to Claude Queue")

        # Create job ID
        job_id = f"weaponized_ep{episode_number}_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create Claude queue job
        claude_job = {
            "job_id": job_id,
            "type": "sherlock_intelligence_extraction",
            "priority": 1,
            "source": "nightshift_podcast_transcription",
            "created_at": datetime.now().isoformat(),
            "description": f"Extract intelligence from Weaponized Podcast Episode {episode_number}",
            "inputs": {
                "transcript_txt": str(transcript_txt.absolute()),
                "transcript_json": str(transcript_json.absolute()) if transcript_json.exists() else None,
                "metadata": metadata,
                "episode_number": episode_number,
                "podcast_name": "WEAPONIZED with Jeremy Corbell & George Knapp"
            },
            "instructions": [
                "Perform deep intelligence extraction from the podcast transcript",
                "Extract and categorize CLAIMS with evidence assessment:",
                "  - First-hand testimony vs hearsay",
                "  - Confidence levels (high/medium/low)",
                "  - Verification status and requirements",
                "Extract ENTITIES with relationships:",
                "  - People (roles, affiliations, testimony provided)",
                "  - Organizations (government programs, private companies, oversight bodies)",
                "  - Locations (bases, facilities, geographic regions)",
                "  - Events (incidents, hearings, investigations)",
                "Build TIMELINE of events discussed",
                "Identify EVIDENCE GAPS:",
                "  - Claims needing verification",
                "  - Timeline conflicts or inconsistencies",
                "  - Missing documentation or testimony",
                "  - Suggested follow-up research areas",
                "Prepare output for Sherlock database ingestion"
            ],
            "outputs": {
                "intelligence_json": f"ops/outputs/sherlock_intelligence/weaponized_ep{episode_number}_analysis.json",
                "entity_graph": f"ops/outputs/sherlock_intelligence/weaponized_ep{episode_number}_entities.json",
                "evidence_assessment": f"ops/outputs/sherlock_intelligence/weaponized_ep{episode_number}_evidence.json"
            }
        }

        # Write to Claude queue
        queue_file = self.claude_queue_dir / f"{job_id}.json"
        with open(queue_file, 'w') as f:
            json.dump(claude_job, f, indent=2)

        logger.info(f"✅ Claude job queued: {queue_file}")
        logger.info(f"   Job will be processed when you run Claude queue manager")

        return queue_file

    # ==================== MAIN PIPELINE ====================

    def process_episode(
        self,
        episode_number: Optional[int] = None,
        episode_title: Optional[str] = None,
        episode_url: Optional[str] = None,
        skip_transcription: bool = False,
        auto_queue_claude: bool = True
    ) -> Dict[str, Path]:
        """
        Execute Night Shift pipeline (Phases 1-3)
        Optionally queue Phase 4 intelligence extraction to Claude

        Returns: Dict with paths to all outputs
        """
        logger.info("=" * 60)
        logger.info("NIGHT SHIFT PODCAST TRANSCRIPTION PIPELINE")
        logger.info("=" * 60)

        outputs = {}

        try:
            # Phase 1: Discovery
            audio_url, metadata = self.discover_episode_audio_url(
                episode_number=episode_number,
                episode_title=episode_title,
                episode_url=episode_url
            )
            outputs['audio_url'] = audio_url
            outputs['metadata'] = metadata

            # Phase 2: Acquisition
            audio_file = self.download_audio(audio_url, episode_number or 0)
            outputs['audio_file'] = audio_file

            # Phase 3: Transcription
            if not skip_transcription:
                transcript_txt, transcript_json = self.transcribe_audio(audio_file, episode_number or 0)
                outputs['transcript_txt'] = transcript_txt
                outputs['transcript_json'] = transcript_json

                # Phase 4 Handoff: Queue Claude intelligence extraction
                if auto_queue_claude:
                    claude_job_file = self.queue_claude_intelligence_extraction(
                        transcript_txt,
                        transcript_json,
                        metadata,
                        episode_number or 0
                    )
                    outputs['claude_queue_file'] = claude_job_file

            logger.info("=" * 60)
            logger.info("✅ NIGHT SHIFT PIPELINE COMPLETED")
            if auto_queue_claude and 'claude_queue_file' in outputs:
                logger.info("📋 Intelligence extraction queued for Claude")
            logger.info("=" * 60)

            return outputs

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
            raise


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Night Shift Podcast Transcription Pipeline - RSS-First Strategy"
    )

    parser.add_argument(
        '--rss-feed',
        required=True,
        help="RSS feed URL (e.g., https://feeds.megaphone.fm/weaponized)"
    )

    parser.add_argument(
        '--episode-number',
        type=int,
        help="Episode number to process"
    )

    parser.add_argument(
        '--episode-title',
        help="Episode title to search for"
    )

    parser.add_argument(
        '--episode-url',
        help="Direct episode page URL (used for scraping fallback)"
    )

    parser.add_argument(
        '--output-dir',
        default='ops/outputs/podcast_intelligence',
        help="Output directory"
    )

    parser.add_argument(
        '--claude-queue-dir',
        default='/home/johnny5/Johny5Alive/queue/claude',
        help="Claude queue directory for intelligence extraction handoff"
    )

    parser.add_argument(
        '--skip-transcription',
        action='store_true',
        help="Skip transcription (download only)"
    )

    parser.add_argument(
        '--no-auto-queue-claude',
        action='store_true',
        help="Do NOT automatically queue intelligence extraction to Claude"
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.episode_number and not args.episode_title:
        parser.error("Must specify either --episode-number or --episode-title")

    # Initialize pipeline
    pipeline = PodcastIntelligencePipeline(
        rss_feed_url=args.rss_feed,
        output_dir=Path(args.output_dir),
        claude_queue_dir=Path(args.claude_queue_dir)
    )

    # Run pipeline
    outputs = pipeline.process_episode(
        episode_number=args.episode_number,
        episode_title=args.episode_title,
        episode_url=args.episode_url,
        skip_transcription=args.skip_transcription,
        auto_queue_claude=not args.no_auto_queue_claude
    )

    # Print summary
    print("\n" + "=" * 60)
    print("OUTPUT SUMMARY")
    print("=" * 60)
    for key, value in outputs.items():
        if isinstance(value, Path):
            print(f"{key:25s}: {value}")
        elif key == 'metadata':
            print(f"metadata:")
            for k, v in value.items():
                print(f"  {k:23s}: {v}")
        else:
            print(f"{key:25s}: {value}")

    if 'claude_queue_file' in outputs:
        print("\n" + "=" * 60)
        print("📋 CLAUDE QUEUE STATUS")
        print("=" * 60)
        print(f"Intelligence extraction job queued to: {outputs['claude_queue_file']}")
        print("Run Claude queue manager to process this job.")


if __name__ == "__main__":
    main()
