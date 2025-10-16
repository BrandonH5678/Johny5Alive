"""
MediaAgent - Media file download and validation with progress tracking
"""
from __future__ import annotations
import os
import time
import logging
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from urllib.parse import urlparse
import requests
from .base import BaseAgent

logger = logging.getLogger(__name__)

# Media file extensions
AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.aac', '.ogg', '.opus', '.wav', '.flac', '.wma'}
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff'}
MEDIA_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS | IMAGE_EXTENSIONS


class MediaAgent(BaseAgent):
    """
    Downloads and validates media files (audio, video, images)

    Supports:
    - HTTP/HTTPS downloads with progress tracking
    - Format detection and validation
    - Checksum verification
    - Resume partial downloads
    - Size validation
    """

    def __init__(
        self,
        chunk_size: int = 8192,
        timeout: int = 300,
        verify_ssl: bool = True,
        max_retries: int = 3
    ):
        """
        Initialize MediaAgent

        Args:
            chunk_size: Download chunk size in bytes
            timeout: Request timeout in seconds
            verify_ssl: Verify SSL certificates
            max_retries: Maximum retry attempts for failed downloads
        """
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.max_retries = max_retries
        self.session = requests.Session()

    def supports(self, target: Any) -> bool:
        """Check if target is a media file"""
        if not isinstance(target, dict):
            return False

        target_type = target.get('type', '').lower()
        if target_type in ('file', 'media', 'audio', 'video', 'image'):
            return True

        # Check by URL extension
        url = target.get('url', '')
        if url:
            path = urlparse(url).path
            ext = os.path.splitext(path)[1].lower()
            return ext in MEDIA_EXTENSIONS

        # Check by local path extension
        path = target.get('path', '')
        if path:
            ext = os.path.splitext(path)[1].lower()
            return ext in MEDIA_EXTENSIONS

        return False

    def retrieve(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Retrieve media file

        Target structure:
            {
                'type': 'media' or 'audio' or 'video',
                'url': 'https://example.com/file.mp3' (for download),
                'path': '/local/path/file.mp3' (for local file),
                'output_dir': '/path/to/save' (optional, for downloads),
                'output_filename': 'custom_name.mp3' (optional),
                'checksum': {'algorithm': 'sha256', 'value': '...'} (optional),
                'expected_size': 12345678 (optional, bytes),
                'progress_callback': callback_function (optional)
            }

        Returns:
            {
                'path': '/path/to/file.mp3',
                'size_bytes': 12345678,
                'format': 'mp3',
                'mime_type': 'audio/mpeg',
                'duration_seconds': 123.45 (if available),
                'checksum': {'sha256': '...'},
                'meta': {
                    'method': 'download' or 'local',
                    'url': '...',
                    'download_time_ms': 1234,
                    'download_speed_mbps': 12.34
                }
            }
        """
        # Check if local file or download
        url = target.get('url')
        local_path = target.get('path')

        if url:
            return self._download_media(target, **kwargs)
        elif local_path:
            return self._validate_local_media(target, **kwargs)
        else:
            raise ValueError("Media target must include 'url' or 'path'")

    def _download_media(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Download media file from URL"""
        url = target['url']
        output_dir = target.get('output_dir', '.')
        output_filename = target.get('output_filename')
        progress_callback = target.get('progress_callback')

        # Determine output filename
        if not output_filename:
            parsed = urlparse(url)
            output_filename = os.path.basename(parsed.path) or 'downloaded_media'

        # Ensure output directory exists
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        output_path = output_dir_path / output_filename

        logger.info(f"Downloading media: {url} -> {output_path}")

        # Retry logic
        last_error = None
        start_time = time.time()

        for attempt in range(1, self.max_retries + 1):
            try:
                # Check if partial download exists
                resume_pos = 0
                if output_path.exists():
                    resume_pos = output_path.stat().st_size
                    logger.info(f"Resuming download from byte {resume_pos}")

                # Setup headers for resume
                headers = {}
                if resume_pos > 0:
                    headers['Range'] = f'bytes={resume_pos}-'

                # Make request
                response = self.session.get(
                    url,
                    headers=headers,
                    stream=True,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )

                if response.status_code not in (200, 206):  # 206 = Partial Content
                    raise ValueError(f"HTTP {response.status_code}: {response.reason}")

                # Get total size
                content_length = response.headers.get('Content-Length')
                total_size = int(content_length) if content_length else None

                if resume_pos > 0 and total_size:
                    total_size += resume_pos

                # Download with progress tracking
                mode = 'ab' if resume_pos > 0 else 'wb'
                downloaded = resume_pos
                last_progress_time = time.time()

                with open(output_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            # Progress callback
                            if progress_callback and total_size:
                                current_time = time.time()
                                if current_time - last_progress_time >= 1.0:  # Update every second
                                    progress_pct = (downloaded / total_size) * 100
                                    progress_callback(downloaded, total_size, progress_pct)
                                    last_progress_time = current_time

                # Download complete
                download_time_ms = int((time.time() - start_time) * 1000)
                final_size = output_path.stat().st_size

                # Calculate download speed
                download_time_sec = download_time_ms / 1000.0
                download_speed_mbps = 0
                if download_time_sec > 0:
                    download_speed_mbps = (final_size / 1024 / 1024) / download_time_sec

                logger.info(f"Download complete: {final_size} bytes in {download_time_ms}ms ({download_speed_mbps:.2f} MB/s)")

                # Validate file
                validation = self._validate_file(output_path, target)

                return {
                    'path': str(output_path),
                    'size_bytes': final_size,
                    'format': validation['format'],
                    'mime_type': validation['mime_type'],
                    'checksum': validation['checksum'],
                    'meta': {
                        'method': 'download',
                        'url': url,
                        'download_time_ms': download_time_ms,
                        'download_speed_mbps': round(download_speed_mbps, 2),
                        'attempts': attempt,
                        'success': True
                    }
                }

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Download attempt {attempt} failed: {e}")

                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue

        # All retries failed
        return {
            'path': None,
            'error': last_error,
            'meta': {
                'method': 'download',
                'url': url,
                'attempts': self.max_retries,
                'success': False
            }
        }

    def _validate_local_media(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Validate local media file"""
        path = Path(target['path'])

        if not path.exists():
            raise FileNotFoundError(f"Media file not found: {path}")

        logger.info(f"Validating local media: {path}")

        validation = self._validate_file(path, target)

        return {
            'path': str(path),
            'size_bytes': path.stat().st_size,
            'format': validation['format'],
            'mime_type': validation['mime_type'],
            'checksum': validation['checksum'],
            'meta': {
                'method': 'local',
                'success': True
            }
        }

    def _validate_file(self, path: Path, target: Dict[str, Any]) -> Dict[str, Any]:
        """Validate media file"""
        # Detect format
        ext = path.suffix.lower()
        mime_type, _ = mimetypes.guess_type(str(path))

        # Calculate checksum
        checksum = self._calculate_checksum(path, algorithm='sha256')

        # Verify expected checksum if provided
        expected_checksum = target.get('checksum', {})
        if expected_checksum:
            expected_algo = expected_checksum.get('algorithm', 'sha256')
            expected_value = expected_checksum.get('value')

            if expected_value:
                actual_value = checksum.get(expected_algo)
                if actual_value != expected_value:
                    raise ValueError(f"Checksum mismatch: expected {expected_value}, got {actual_value}")

        # Verify expected size if provided
        expected_size = target.get('expected_size')
        if expected_size:
            actual_size = path.stat().st_size
            if actual_size != expected_size:
                raise ValueError(f"Size mismatch: expected {expected_size} bytes, got {actual_size} bytes")

        return {
            'format': ext[1:] if ext else 'unknown',  # Remove leading dot
            'mime_type': mime_type or 'application/octet-stream',
            'checksum': checksum
        }

    def _calculate_checksum(self, path: Path, algorithm: str = 'sha256') -> Dict[str, str]:
        """Calculate file checksum"""
        hash_obj = hashlib.new(algorithm)

        with open(path, 'rb') as f:
            while chunk := f.read(self.chunk_size):
                hash_obj.update(chunk)

        return {algorithm: hash_obj.hexdigest()}
