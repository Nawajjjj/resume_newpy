import os
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import logging

# Configure logging
logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path):
    text = ""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    # First, try extracting text using pdfplumber (for text-based PDFs)
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()

    # If the text extraction is empty or not sufficient, fall back to OCR
    if not text.strip():
        logger.info("Text extraction failed, attempting OCR...")
        images = convert_from_path(file_path)
        for image in images:
            text += pytesseract.image_to_string(image)
        if not text.strip():
            logger.error("OCR failed to extract any text from the PDF.")
            raise Exception("OCR failed to extract any text from the PDF.")

    logger.info("Text extraction successful")
    return text


def extract_information(text):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\+?\d{1,4}?[-.\s]??(?:\d{1,3}?[-.\s]?){6,}\d{1,4}'
    date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'

    extracted_info = {
        'description': text.strip(),
        'email': re.search(email_pattern, text).group() if re.search(email_pattern, text) else None,
        'phone': re.search(phone_pattern, text).group() if re.search(phone_pattern, text) else None,
        'date': re.search(date_pattern, text).group() if re.search(date_pattern, text) else None,
    }

    logger.info(f"Extracted Information: {extracted_info}")
    return extracted_info


def create_resume_pdf(user, data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, f"Resume for {user.username}")

    # Content
    y_position = height - 100
    styles = getSampleStyleSheet()
    style = styles["Normal"]

    for idx, item in enumerate(data, start=1):
        if y_position < 100:  # Start a new page if space runs out
            c.showPage()
            y_position = height - 50

        text = f"{idx}. {item.get('description', 'No Description')}"
        para = Paragraph(text, style)
        para.wrapOn(c, width - 100, 200)
        para.drawOn(c, 50, y_position)
        y_position -= 50

    # Save PDF
    c.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="resume_{user.username}.pdf"'
    return response
