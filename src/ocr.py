import io
import logging

import pytesseract
from PIL import Image
from PyPDF2 import PageObject, PdfReader

from src.utils import clean_text, setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF file. Uses OCR if text extraction fails or is empty.
    """
    text = ""
    with open(file_path, "rb") as f:
        pdf_reader = PdfReader(f)
        logger.info("Opened PDF file for text extraction: %s", file_path)

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                    logger.info("Extracted text from page %s without OCR.", page_num)
                else:
                    logger.info("No text found on page %s; attempting OCR.", page_num)
                    text += extract_text_from_images(page)
            except Exception as e:
                logger.error(
                    "Error processing page %s: %s; attempting OCR fallback.",
                    page_num,
                    e,
                )
                try:
                    text += extract_text_from_images(page)
                except Exception as ocr_error:
                    logger.error(
                        "OCR fallback failed on page %s: %s", page_num, ocr_error
                    )

    cleaned_text = clean_text(text)
    logger.info("Completed text extraction for %s", file_path)
    return cleaned_text


def extract_text_from_images(page: PageObject) -> str:
    """Extracts text from images on a page using OCR."""
    text = ""
    for image_file_object in page.images:
        try:
            image = Image.open(io.BytesIO(image_file_object.data))
            ocr_text = pytesseract.image_to_string(image)
            text += ocr_text
            logger.info("Extracted text from image using OCR.")
        except Exception as e:
            logger.error("Error processing image for OCR: %s", e)
    return text
