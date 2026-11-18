import io
import logging

from src.utils import clean_text, setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF file. Uses OCR if text extraction fails or is empty.
    """
    from PyPDF2 import PdfReader

    text = ""
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()
    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
    logger.info("Opened PDF file for text extraction: %s", file_path)

    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        try:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text += page_text
                logger.info("Extracted text from page %s without OCR.", page_num)
            else:
                logger.info("No text found on page %s; attempting OCR.", page_num)
                text += _ocr_page(pdf_bytes, page, page_num)
        except Exception as e:
            logger.error(
                "Error processing page %s: %s; attempting OCR fallback.",
                page_num,
                e,
            )
            try:
                text += _ocr_page(pdf_bytes, page, page_num)
            except Exception as ocr_error:
                logger.error("OCR fallback failed on page %s: %s", page_num, ocr_error)

    cleaned_text = clean_text(text)
    logger.info("Completed text extraction for %s", file_path)
    return cleaned_text


def _ocr_page(pdf_bytes: bytes, page: object, page_num: int) -> str:
    """OCR embedded images, then a rendered page when that finds nothing."""
    from PyPDF2 import PageObject

    embedded = ""
    if isinstance(page, PageObject):
        embedded = extract_text_from_images(page)
    if embedded.strip():
        return embedded
    return extract_text_from_rendered_page(pdf_bytes, page_num)


def extract_text_from_rendered_page(pdf_bytes: bytes, page_num: int) -> str:
    """Render one PDF page and run Tesseract. Returns empty text if Poppler is missing."""
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
    except ImportError:
        logger.warning("pdf2image is not installed; skipping full-page OCR.")
        return ""
    try:
        images = convert_from_bytes(
            pdf_bytes,
            first_page=page_num + 1,
            last_page=page_num + 1,
        )
    except Exception as e:
        logger.error("Full-page render failed on page %s: %s", page_num, e)
        return ""
    text = ""
    for image in images:
        try:
            text += pytesseract.image_to_string(image)
            logger.info("Extracted text from rendered page %s.", page_num)
        except Exception as e:
            logger.error("Full-page OCR failed on page %s: %s", page_num, e)
    return text


def extract_text_from_images(page: object) -> str:
    """Extracts text from images on a page using OCR."""
    import pytesseract
    from PIL import Image
    from PyPDF2 import PageObject

    if not isinstance(page, PageObject):
        return ""
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
