#!/usr/bin/env python3
"""
Night Shift Task Retriever - Enhanced with retry logic and error handling
Retrieves media files (podcast audio, PDFs, etc.) for J5A Night Shift operations
"""
import sys, json, pathlib, logging
from retriever.rwf import RobustWebFetcher
from retriever.discovery import discover_audio_from_homepage, DiscoveryRetryConfig, DiscoveryError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_payload(payload: dict) -> tuple:
    """Validate input payload"""
    if not isinstance(payload, dict):
        return False, "Payload must be a JSON object"

    home = payload.get("home_url")
    if not home:
        return False, "home_url is required"

    if not isinstance(home, str) or not home.startswith(("http://", "https://")):
        return False, "home_url must be a valid HTTP(S) URL"

    return True, ""

def download_media(media_url: str, outpath: pathlib.Path, fetcher: RobustWebFetcher, timeout: int = 120) -> dict:
    """
    Download media file with enhanced error handling

    Returns:
        dict with download status and metadata
    """
    try:
        logger.info(f"Starting download: {media_url}")
        logger.info(f"Output path: {outpath}")

        with fetcher.s.get(media_url, stream=True, timeout=timeout) as r:
            r.raise_for_status()

            # Get content length for progress tracking
            total_size = int(r.headers.get('content-length', 0))
            if total_size > 0:
                logger.info(f"Content length: {total_size / (1024*1024):.2f} MB")

            downloaded = 0
            chunk_size = 1024 * 512  # 512KB chunks

            with open(outpath, "wb") as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Log progress every 10MB
                        if total_size > 0 and downloaded % (10 * 1024 * 1024) < chunk_size:
                            progress = (downloaded / total_size) * 100
                            logger.info(f"Download progress: {progress:.1f}%")

        actual_size = outpath.stat().st_size
        logger.info(f"✅ Download complete: {actual_size / (1024*1024):.2f} MB")

        return {
            "success": True,
            "path": str(outpath),
            "size_bytes": actual_size,
            "size_mb": round(actual_size / (1024*1024), 2)
        }

    except Exception as e:
        logger.error(f"❌ Download failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "path": str(outpath)
        }

def main():
    try:
        # Parse input
        logger.info("Reading task payload from stdin")
        payload = json.load(sys.stdin)
        logger.info(f"Payload received: {json.dumps(payload, indent=2)}")

    except json.JSONDecodeError as e:
        error_result = {"error": f"Invalid JSON input: {str(e)}", "success": False}
        print(json.dumps(error_result))
        sys.exit(1)
    except Exception as e:
        error_result = {"error": f"Failed to read input: {str(e)}", "success": False}
        print(json.dumps(error_result))
        sys.exit(1)

    # Validate payload
    valid, error_msg = validate_payload(payload)
    if not valid:
        error_result = {"error": error_msg, "success": False}
        print(json.dumps(error_result))
        sys.exit(1)

    # Extract parameters
    home = payload.get("home_url")
    prefer_title = payload.get("prefer_title")
    prefer_epnum = payload.get("prefer_epnum")
    should_download = payload.get("download", False) or payload.get("outdir")

    # Configure retry behavior
    retry_config = DiscoveryRetryConfig(
        max_cascade_retries=payload.get("max_cascade_retries", 2),
        max_stage_retries=payload.get("max_stage_retries", 2),
        retry_delay=payload.get("retry_delay", 2.0),
        exponential_backoff=payload.get("exponential_backoff", True)
    )

    logger.info(f"Starting discovery for: {home}")
    if prefer_title:
        logger.info(f"Preferred title: {prefer_title}")
    if prefer_epnum:
        logger.info(f"Preferred episode: {prefer_epnum}")

    try:
        # Initialize fetcher and run discovery
        fetcher = RobustWebFetcher(
            timeout=payload.get("fetch_timeout", 25),
            max_retries=payload.get("fetch_max_retries", 3)
        )

        media_url, meta = discover_audio_from_homepage(
            home,
            prefer_title,
            prefer_epnum,
            fetcher=fetcher,
            retry_config=retry_config
        )

        logger.info(f"✅ Discovery successful: {media_url}")
        logger.info(f"Discovery method: {meta.get('method')}")

        result = {
            "success": True,
            "media_url": media_url,
            "meta": meta
        }

        # Download if requested
        if should_download:
            outdir = pathlib.Path(payload.get("outdir", "./output"))
            outdir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory: {outdir}")

            # Determine file extension
            ext = ".bin"
            for e in (".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav"):
                if media_url.lower().endswith(e):
                    ext = e
                    break

            fname = payload.get("filename") or f"downloaded_episode{ext}"
            outpath = outdir / fname

            download_result = download_media(
                media_url,
                outpath,
                fetcher,
                timeout=payload.get("download_timeout", 1800)  # 30 min default
            )

            result["download"] = download_result

        # Output result
        print(json.dumps(result, indent=2))
        sys.exit(0)

    except DiscoveryError as e:
        logger.error(f"❌ Discovery failed: {str(e)}")
        error_result = {
            "success": False,
            "error": str(e),
            "stage": e.stage,
            "errors": e.errors
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        error_result = {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
