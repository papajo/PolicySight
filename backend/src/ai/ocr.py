"""
OCR Service for PolicySight.
Extracts text from uploaded policy documents (images and PDFs).
"""

from __future__ import annotations

import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)


class OCRService:
    """Optical Character Recognition service."""

    MIN_EXTRACTED_TEXT_LENGTH = 20

    @staticmethod
    async def extract_text_from_image(file_bytes: bytes, filename: str = "") -> str:
        try:
            import pytesseract
        except ImportError:
            logger.warning("pytesseract not installed")
            return ""

        try:
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error("OCR extraction failed for %s: %s", filename, e)
            return ""

    @staticmethod
    async def extract_text_from_pdf(file_bytes: bytes) -> str:
        text = ""

        try:
            import fitz

            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text()
            doc.close()
            if text.strip():
                return text.strip()
        except ImportError:
            pass
        except Exception as e:
            logger.warning("PyMuPDF extraction failed: %s", e)

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
            logger.warning("PyPDF2 extraction failed: %s", e)

        try:
            from pdfminer.high_level import extract_text

            text = extract_text(io.BytesIO(file_bytes))
            if text.strip():
                return text.strip()
        except ImportError:
            pass
        except Exception as e:
            logger.warning("pdfminer extraction failed: %s", e)

        return ""

    @classmethod
    async def extract_text(cls, file_bytes: bytes, filename: str = "") -> str:
        lower_name = filename.lower()

        if lower_name.endswith(".pdf"):
            return await cls.extract_text_from_pdf(file_bytes)
        if any(lower_name.endswith(ext) for ext in (".png", ".jpg", ".jpeg")):
            return await cls.extract_text_from_image(file_bytes, filename)
        return ""

    @classmethod
    def has_meaningful_text(cls, text: str) -> bool:
        return bool(text and len(text.strip()) >= cls.MIN_EXTRACTED_TEXT_LENGTH)
