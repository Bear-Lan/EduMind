import io
from typing import List
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """Extract raw text from a PDF or TXT file."""
    if filename.lower().endswith('.pdf'):
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) is not installed.")
        
        # Open PDF from bytes
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for page in doc:
            text = page.get_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)
        
    elif filename.lower().endswith('.txt') or filename.lower().endswith('.md'):
        return file_bytes.decode('utf-8', errors='replace')
        
    else:
        raise ValueError(f"Unsupported file format for {filename}")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into chunks of `chunk_size` characters, with `overlap` characters.
    This is a basic chunking strategy.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # Try to find a natural break (newline or period) near the end to avoid breaking words
        if end < text_len:
            # Look backwards up to 100 chars for a newline
            newline_idx = text.rfind('\n', max(start, end - 100), end)
            if newline_idx != -1:
                end = newline_idx + 1
            else:
                # Look backwards for a period
                period_idx = text.rfind('.', max(start, end - 100), end)
                if period_idx != -1:
                    end = period_idx + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
            
        start = end - overlap

    return chunks


def process_document(file_bytes: bytes, filename: str, chunk_size: int = 500) -> List[str]:
    """Complete pipeline: Extract text and chunk it."""
    raw_text = extract_text_from_bytes(file_bytes, filename)
    chunks = chunk_text(raw_text, chunk_size=chunk_size)
    return chunks
