from __future__ import annotations
"""
File Reader Service
-------------------
Reads user-uploaded documents and extracts text content.
Supports: TXT, DOCX, PDF

Used when user sends a document instead of a topic — AI reads the material
and generates presentation content based on it.
"""

import io
import os
import logging
import tempfile

logger = logging.getLogger(__name__)


def read_txt(file_bytes: bytes, encoding: str = "utf-8") -> str:
    """Read plain text file."""
    try:
        return file_bytes.decode(encoding)
    except UnicodeDecodeError:
        try:
            return file_bytes.decode("cp1251")
        except:
            return file_bytes.decode("utf-8", errors="ignore")


def read_docx(file_bytes: bytes) -> str:
    """Read DOCX file using python-docx."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)
        return "\n\n".join(paragraphs)
    except ImportError:
        logger.error("python-docx not installed")
        return ""
    except Exception as e:
        logger.error(f"DOCX read error: {e}")
        return ""


def read_pdf(file_bytes: bytes) -> str:
    """Read PDF file using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n\n".join(pages)
    except ImportError:
        logger.error("PyPDF2 not installed")
        return ""
    except Exception as e:
        logger.error(f"PDF read error: {e}")
        return ""


# Extension → reader mapping
_READERS = {
    ".txt": read_txt,
    ".md": read_txt,
    ".docx": read_docx,
    ".doc": read_docx,
    ".pdf": read_pdf,
}


def read_document(file_bytes: bytes, filename: str) -> str:
    """
    Read a document and return its text content.
    
    Args:
        file_bytes: raw bytes of the file
        filename: original filename (used to detect format)
    
    Returns:
        Extracted text content as a string
    """
    ext = os.path.splitext(filename.lower())[1]
    reader = _READERS.get(ext)

    if reader is None:
        logger.warning(f"Unsupported file format: {ext}")
        # Try to read as plain text
        try:
            return file_bytes.decode("utf-8", errors="ignore")
        except:
            return ""

    text = reader(file_bytes)
    logger.info(f"Read document '{filename}': {len(text)} chars extracted")
    return text


def summarize_for_prompt(text: str, max_chars: int = 8000) -> str:
    """
    Truncate/summarize text to fit into AI prompt context.
    Tries to cut at paragraph boundaries.
    """
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    # Cut at last paragraph boundary
    last_double_newline = truncated.rfind("\n\n")
    if last_double_newline > max_chars * 0.5:
        truncated = truncated[:last_double_newline]
    else:
        last_newline = truncated.rfind("\n")
        if last_newline > max_chars * 0.5:
            truncated = truncated[:last_newline]

    return truncated + "\n\n[... matn qisqartirildi ...]"
