import fitz  # PyMuPDF
import docx
import re

def extract_text_from_pdf(file_stream):
    """Extracts text from a PDF file stream."""
    text = ""
    try:
        with fitz.open(stream=file_stream.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"Error processing PDF: {e}")
    return text

def extract_text_from_docx(file_stream):
    """Extracts text from a DOCX file stream."""
    text = ""
    try:
        doc = docx.Document(file_stream)
        text = "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error processing DOCX: {e}")
    return text

def clean_text(text):
    """Cleans raw text by removing extra whitespace."""
    return re.sub(r'\s+', ' ', text).strip().lower()

def extract_skills(text, skills_list):
    """Finds which skills from a list are present in the text."""
    found_skills = set()
    text_lower = text.lower()
    for skill in skills_list:
        if re.search(r"\b" + re.escape(skill.lower()) + r"\b", text_lower):
            found_skills.add(skill)
    return list(found_skills)