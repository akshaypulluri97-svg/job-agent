import pdfplumber


def extract_text_from_pdf(uploaded_file) -> str:
    """Extract text from a PDF file. Accepts Streamlit UploadedFile or file path."""
    with pdfplumber.open(uploaded_file) as pdf:
        text = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        )
    return text.strip()
