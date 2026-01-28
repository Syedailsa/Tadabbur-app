import io
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
from docx import Document

MAX_PAGES = 3

async def process_uploaded_file(file: UploadFile) -> str:
    """Reads file, checks page limit, and returns extracted text."""

    # Route based on content type
    if file.content_type == "application/pdf":
        return await _process_pdf(file)
    elif file.content_type == "text/plain":
        return await _process_txt(file)
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return await _process_docx(file)
    else:
        raise HTTPException(status_code=400, detail="Only PDF, TXT, and DOCX files are supported.")

async def _process_pdf(file: UploadFile) -> str:
    content = await file.read()
    pdf_file = io.BytesIO(content)
    
    try:
        reader = PdfReader(pdf_file)
        
        if len(reader.pages) > MAX_PAGES:
            raise HTTPException(
                status_code=400,
                detail=f"PDF too long! This document has {len(reader.pages)} pages, but we only accept PDFs with maximum {MAX_PAGES} pages. Please upload a shorter document or split this PDF into smaller parts."
            )

        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        return text.strip()
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing PDF: {str(e)}")

async def _process_txt(file: UploadFile) -> str:
    content = await file.read()
    return content.decode("utf-8")

async def _process_docx(file: UploadFile) -> str:
    content = await file.read()
    docx_file = io.BytesIO(content)

    try:
        doc = Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing DOCX: {str(e)}")