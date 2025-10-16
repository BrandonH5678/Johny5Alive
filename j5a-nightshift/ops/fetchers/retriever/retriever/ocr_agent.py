"""
OcrAgent - OCR text extraction from images and PDFs using Tesseract
"""
from __future__ import annotations
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base import BaseAgent

logger = logging.getLogger(__name__)

# Image file extensions that support OCR
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif', '.webp'}
DOCUMENT_EXTENSIONS = {'.pdf'}
OCR_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS


class OcrAgent(BaseAgent):
    """
    Extracts text from images and PDFs using OCR

    Supports:
    - Image OCR (PNG, JPG, TIFF, BMP, etc.) via Tesseract
    - PDF text extraction (native text + OCR fallback)
    - Multi-page document processing
    - Language selection
    - Confidence scores
    - Preprocessing options
    """

    def __init__(
        self,
        tesseract_cmd: str = 'tesseract',
        language: str = 'eng',
        dpi: int = 300,
        psm: int = 3
    ):
        """
        Initialize OcrAgent

        Args:
            tesseract_cmd: Path to tesseract executable
            language: OCR language (eng, fra, deu, etc.)
            dpi: DPI for PDF rendering
            psm: Page segmentation mode (0-13, default 3=automatic)
        """
        self.tesseract_cmd = tesseract_cmd
        self.language = language
        self.dpi = dpi
        self.psm = psm

        # Check if tesseract is available
        self._check_tesseract()

    def _check_tesseract(self):
        """Verify Tesseract is installed and accessible"""
        try:
            result = subprocess.run(
                [self.tesseract_cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Tesseract OCR available: {result.stdout.split()[1]}")
            else:
                logger.warning("Tesseract OCR not found - OCR functionality will be limited")
        except Exception as e:
            logger.warning(f"Tesseract check failed: {e}")

    def supports(self, target: Any) -> bool:
        """Check if target is an OCR operation"""
        if not isinstance(target, dict):
            return False

        target_type = target.get('type', '').lower()
        if target_type in ('ocr', 'text_extraction', 'document'):
            return True

        # Check by file extension
        path = target.get('path', '')
        if path:
            ext = Path(path).suffix.lower()
            return ext in OCR_EXTENSIONS

        return False

    def retrieve(self, target: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Extract text from image or PDF

        Target structure:
            {
                'type': 'ocr',
                'path': '/path/to/image.png' or '/path/to/document.pdf',
                'language': 'eng' (optional, default from init),
                'psm': 3 (optional, page segmentation mode),
                'preprocess': True (optional, apply preprocessing),
                'extract_confidence': True (optional, include confidence scores),
                'pages': [1, 2, 3] (optional, specific PDF pages to process)
            }

        Returns:
            {
                'text': 'Extracted text content...',
                'pages': [
                    {
                        'page_number': 1,
                        'text': 'Page 1 text...',
                        'confidence': 92.5,
                        'word_count': 123
                    },
                    ...
                ],
                'total_pages': 3,
                'word_count': 456,
                'avg_confidence': 91.2,
                'meta': {
                    'method': 'ocr',
                    'engine': 'tesseract',
                    'language': 'eng',
                    'file_type': 'pdf',
                    'processing_time_ms': 1234
                }
            }
        """
        import time

        path = target.get('path')
        if not path:
            raise ValueError("OCR target must include 'path'")

        # Validate file exists
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        logger.info(f"Extracting text from: {path}")

        start_time = time.time()

        # Determine file type
        ext = file_path.suffix.lower()

        if ext == '.pdf':
            result = self._extract_from_pdf(target, file_path)
        elif ext in IMAGE_EXTENSIONS:
            result = self._extract_from_image(target, file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Add metadata
        result['meta'] = {
            'method': 'ocr',
            'engine': 'tesseract',
            'language': target.get('language', self.language),
            'file_type': ext[1:],  # Remove leading dot
            'processing_time_ms': processing_time_ms
        }

        logger.info(f"Text extraction complete: {result.get('word_count', 0)} words in {processing_time_ms}ms")

        return result

    def _extract_from_image(self, target: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """Extract text from image using Tesseract"""
        language = target.get('language', self.language)
        psm = target.get('psm', self.psm)
        extract_confidence = target.get('extract_confidence', False)

        # Build tesseract command
        cmd = [
            self.tesseract_cmd,
            str(file_path),
            'stdout',  # Output to stdout
            '-l', language,
            '--psm', str(psm)
        ]

        if extract_confidence:
            cmd.append('--tsv')  # TSV output includes confidence

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise ValueError(f"Tesseract failed: {result.stderr}")

            text = result.stdout.strip()

            # Calculate stats
            word_count = len(text.split())

            # Extract confidence if requested
            confidence = None
            if extract_confidence and text:
                confidence = self._calculate_confidence(result.stdout)

            return {
                'text': text,
                'pages': [{
                    'page_number': 1,
                    'text': text,
                    'confidence': confidence,
                    'word_count': word_count
                }],
                'total_pages': 1,
                'word_count': word_count,
                'avg_confidence': confidence
            }

        except subprocess.TimeoutExpired:
            raise ValueError("OCR processing timeout (>60s)")
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            raise ValueError(f"OCR failed: {e}")

    def _extract_from_pdf(self, target: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """Extract text from PDF (native text + OCR fallback)"""

        # First try native PDF text extraction
        try:
            native_text = self._extract_pdf_native_text(file_path)
            if native_text and len(native_text.strip()) > 50:  # Meaningful text found
                logger.info("Using native PDF text extraction (no OCR needed)")
                word_count = len(native_text.split())
                return {
                    'text': native_text,
                    'pages': [{
                        'page_number': 1,
                        'text': native_text,
                        'confidence': 100.0,  # Native text is 100% accurate
                        'word_count': word_count
                    }],
                    'total_pages': 1,
                    'word_count': word_count,
                    'avg_confidence': 100.0
                }
        except Exception as e:
            logger.warning(f"Native PDF extraction failed: {e}, falling back to OCR")

        # Fallback to OCR (requires converting PDF to images)
        logger.info("PDF requires OCR - using image conversion")
        return self._extract_pdf_with_ocr(target, file_path)

    def _extract_pdf_native_text(self, file_path: Path) -> str:
        """Extract native text from PDF using pdftotext"""
        try:
            result = subprocess.run(
                ['pdftotext', str(file_path), '-'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return ""

        except FileNotFoundError:
            logger.warning("pdftotext not found - install poppler-utils for native PDF text extraction")
            return ""
        except Exception as e:
            logger.warning(f"pdftotext failed: {e}")
            return ""

    def _extract_pdf_with_ocr(self, target: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """Extract text from PDF using OCR (convert to images first)"""

        # This requires pdftoppm (from poppler-utils) to convert PDF to images
        # Then run Tesseract on each page image

        import tempfile

        language = target.get('language', self.language)
        pages_to_process = target.get('pages')  # Optional list of page numbers

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Convert PDF to images
            try:
                cmd = [
                    'pdftoppm',
                    '-png',
                    '-r', str(self.dpi),
                    str(file_path),
                    str(tmp_path / 'page')
                ]

                result = subprocess.run(cmd, capture_output=True, timeout=120)

                if result.returncode != 0:
                    raise ValueError(f"PDF conversion failed: {result.stderr.decode()}")

            except FileNotFoundError:
                raise ValueError("pdftoppm not found - install poppler-utils for PDF OCR")
            except subprocess.TimeoutExpired:
                raise ValueError("PDF conversion timeout (>120s)")

            # Process each page image
            page_images = sorted(tmp_path.glob('page-*.png'))

            if not page_images:
                raise ValueError("No pages extracted from PDF")

            all_pages = []
            all_text = []
            total_words = 0
            total_confidence = 0

            for i, img_path in enumerate(page_images, start=1):
                # Skip if specific pages requested and this isn't one
                if pages_to_process and i not in pages_to_process:
                    continue

                logger.info(f"OCR processing page {i}/{len(page_images)}")

                # Run OCR on page image
                page_result = self._extract_from_image(
                    {'language': language, 'extract_confidence': True},
                    img_path
                )

                page_text = page_result['text']
                page_words = page_result['word_count']
                page_conf = page_result['avg_confidence'] or 0

                all_pages.append({
                    'page_number': i,
                    'text': page_text,
                    'confidence': page_conf,
                    'word_count': page_words
                })

                all_text.append(page_text)
                total_words += page_words
                total_confidence += page_conf

            # Calculate average confidence
            avg_conf = total_confidence / len(all_pages) if all_pages else 0

            return {
                'text': '\n\n'.join(all_text),
                'pages': all_pages,
                'total_pages': len(all_pages),
                'word_count': total_words,
                'avg_confidence': round(avg_conf, 2)
            }

    def _calculate_confidence(self, tsv_output: str) -> Optional[float]:
        """Calculate average confidence from Tesseract TSV output"""
        try:
            lines = tsv_output.strip().split('\n')
            if len(lines) < 2:  # Need header + data
                return None

            confidences = []
            for line in lines[1:]:  # Skip header
                fields = line.split('\t')
                if len(fields) >= 11:  # TSV has 12 fields
                    conf = fields[10]  # Confidence is field 11 (0-indexed 10)
                    if conf and conf != '-1':
                        try:
                            confidences.append(float(conf))
                        except ValueError:
                            pass

            if confidences:
                return round(sum(confidences) / len(confidences), 2)
            return None

        except Exception as e:
            logger.warning(f"Confidence calculation failed: {e}")
            return None
