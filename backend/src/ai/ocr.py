"""
OCR Service for PolicySight.
Extracts text from uploaded policy documents (images and PDFs).
Uses Tesseract for images and PyPDF2/pdfminer for PDFs.
"""

import io
import logging
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


class OCRService:
    """
    Optical Character Recognition service.
    Extracts text from image and PDF documents for LLM processing.
    """

    @staticmethod
    async def extract_text_from_image(file_bytes: bytes, filename: str = "") -> str:
        """
        Extract text from an image file using Tesseract OCR.
        Supports PNG, JPG, JPEG formats.

        Falls back gracefully if Tesseract is not installed.
        """
        try:
            import pytesseract
        except ImportError:
            logger.warning("pytesseract not installed, returning placeholder text")
            return "[OCR unavailable — pytesseract not installed]"

        try:
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)
            return text.strip() or "[No text detected in image]"
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return f"[OCR extraction failed: {e}]"

    @staticmethod
    async def extract_text_from_pdf(file_bytes: bytes) -> str:
        """
        Extract text from a PDF file.
        Tries PyMuPDF first, then falls back to PyPDF2/pdfminer.
        """
        text = ""

        # Try PyMuPDF (fastest)
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text()
            doc.close()
            if text.strip():
                return text.strip()
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}")

        # Fall back to PyPDF2
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            if text.strip():
                return text.strip()
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")

        # Fall back to pdfminer
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(io.BytesIO(file_bytes))
            if text.strip():
                return text.strip()
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"pdfminer extraction failed: {e}")

        if not text.strip():
            return "[No text could be extracted from this PDF. It may be a scanned document.]"

        return text.strip()

    @staticmethod
    async def extract_text(file_bytes: bytes, filename: str = "") -> str:
        """
        Extract text from an uploaded file.
        Automatically detects file type and routes to the appropriate extractor.
        """
        lower_name = filename.lower()

        if lower_name.endswith(".pdf"):
            return await OCRService.extract_text_from_pdf(file_bytes)
        elif any(lower_name.endswith(ext) for ext in (".png", ".jpg", ".jpeg")):
            return await OCRService.extract_text_from_image(file_bytes, filename)
        else:
            # Try as plain text
            try:
                return file_bytes.decode("utf-8").strip()
            except UnicodeDecodeError:
                return "[Unable to extract text from this file type]"