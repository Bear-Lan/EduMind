"""
Document text extraction and structure-aware chunking for RAG ingestion.

Each chunk carries parent_doc / chapter / section metadata so retrieval
citations can point back to the logical textbook location.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


_HEADING_RE = re.compile(
    r"^(?:"
    r"#{1,3}\s+(.+?)\s*$"  # Markdown # ## ###
    r"|第[一二三四五六七八九十百零0-9]+[章节部篇]\s*[、.．:]?\s*(.*)$"
    r"|§\s*([\d.]+)\s*(.*)$"
    r"|(\d+(?:\.\d+){0,3})\s+(.{2,40})$"  # 1.2 Title / 1.2.3 Title
    r")",
    re.MULTILINE,
)


@dataclass
class TextChunk:
    text: str
    chapter: str | None = None
    section: str | None = None
    chunk_index: int = 0


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """Extract raw text from a PDF or TXT file."""
    if filename.lower().endswith(".pdf"):
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) is not installed.")
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for page in doc:
            text = page.get_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)

    if filename.lower().endswith(".txt") or filename.lower().endswith(".md"):
        return file_bytes.decode("utf-8", errors="replace")

    raise ValueError(f"Unsupported file format for {filename}")


def _classify_heading(line: str) -> tuple[str | None, str | None]:
    """
    Return (chapter, section) update from a heading line.
    chapter-level headings clear section; section-level keep chapter.
    """
    raw = line.strip()
    if not raw:
        return None, None

    md = re.match(r"^(#{1,3})\s+(.+?)\s*$", raw)
    if md:
        level = len(md.group(1))
        title = md.group(2).strip()
        if level <= 1:
            return title, None
        return None, title  # caller merges with current chapter

    cn = re.match(
        r"^第[一二三四五六七八九十百零0-9]+([章节部篇])\s*[、.．:]?\s*(.*)$",
        raw,
    )
    if cn:
        kind, rest = cn.group(1), (cn.group(2) or "").strip()
        label = raw if not rest else f"{raw.split(rest)[0].strip()} {rest}".strip()
        if kind in ("章", "部", "篇"):
            return label, None
        return None, label

    sec = re.match(r"^§\s*([\d.]+)\s*(.*)$", raw)
    if sec:
        num, rest = sec.group(1), (sec.group(2) or "").strip()
        label = f"§{num}" + (f" {rest}" if rest else "")
        # §1 / §1.0 → chapter-ish; §1.2 → section
        if "." not in num.rstrip(".0") and num.count(".") == 0:
            return label, None
        if num.count(".") == 0:
            return label, None
        return None, label

    num_h = re.match(r"^(\d+(?:\.\d+){0,3})\s+(.{2,60})$", raw)
    if num_h:
        num, rest = num_h.group(1), num_h.group(2).strip()
        label = f"{num} {rest}"
        depth = num.count(".")
        if depth == 0:
            return label, None
        return None, label

    return None, None


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p and p.strip()]


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Backward-compatible plain string chunker."""
    return [c.text for c in chunk_document(text, chunk_size=chunk_size, overlap=overlap)]


def chunk_document(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
    default_chapter: str | None = None,
    default_section: str | None = None,
) -> list[TextChunk]:
    """
    Structure-aware chunking.

    - Tracks chapter / section from markdown & textbook-style headings.
    - Packs paragraphs into windows of ~chunk_size with overlap.
    - Short docs become a single chunk (still tagged).
    """
    if not text or not text.strip():
        return []

    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    paragraphs = _split_paragraphs(cleaned)
    if not paragraphs:
        paragraphs = [cleaned]

    chapter = default_chapter
    section = default_section
    units: list[tuple[str, str | None, str | None]] = []  # text, chapter, section

    for para in paragraphs:
        first_line = para.split("\n", 1)[0].strip()
        ch_upd, sec_upd = _classify_heading(first_line)

        # Heading-only paragraph → update context, keep text for indexing too
        if ch_upd is not None:
            chapter = ch_upd
            section = None
        elif sec_upd is not None:
            section = sec_upd
            # If heading line is alone, still index it with body if any
            body = para.split("\n", 1)[1].strip() if "\n" in para else ""
            if not body and len(para) < 80:
                # tiny heading-only: attach as context marker unit (skip empty)
                continue
            if body:
                para = body

        units.append((para, chapter, section))

    if not units:
        return [
            TextChunk(
                text=cleaned,
                chapter=default_chapter,
                section=default_section,
                chunk_index=0,
            )
        ]

    # Pack units into sized windows (never merge across chapter change)
    chunks: list[TextChunk] = []
    buf: list[str] = []
    buf_chapter = units[0][1]
    buf_section = units[0][2]
    buf_len = 0

    def flush() -> None:
        nonlocal buf, buf_len
        if not buf:
            return
        text_out = "\n\n".join(buf).strip()
        if text_out:
            chunks.append(
                TextChunk(
                    text=text_out,
                    chapter=buf_chapter,
                    section=buf_section,
                    chunk_index=len(chunks),
                )
            )
        buf = []
        buf_len = 0

    for para, ch, sec in units:
        # New chapter boundary → flush
        if buf and ch != buf_chapter:
            flush()
            buf_chapter, buf_section = ch, sec

        # Oversized single paragraph → hard-split with overlap
        if len(para) > chunk_size * 1.5:
            flush()
            buf_chapter, buf_section = ch, sec
            start = 0
            while start < len(para):
                end = min(start + chunk_size, len(para))
                if end < len(para):
                    cut = para.rfind("。", start, end)
                    if cut < start + chunk_size // 2:
                        cut = para.rfind("\n", start, end)
                    if cut >= start + chunk_size // 3:
                        end = cut + 1
                piece = para[start:end].strip()
                if piece:
                    chunks.append(
                        TextChunk(
                            text=piece,
                            chapter=ch,
                            section=sec,
                            chunk_index=len(chunks),
                        )
                    )
                if end >= len(para):
                    break
                start = max(end - overlap, start + 1)
            buf_chapter, buf_section = ch, sec
            continue

        tentative = buf_len + (2 if buf else 0) + len(para)
        if buf and tentative > chunk_size:
            # Keep overlap: last overlap chars from buffer as prefix of next
            overlap_text = ""
            joined = "\n\n".join(buf)
            if overlap > 0 and len(joined) > overlap:
                overlap_text = joined[-overlap:].lstrip()
            flush()
            buf_chapter, buf_section = ch, sec
            if overlap_text:
                buf = [overlap_text]
                buf_len = len(overlap_text)

        if not buf:
            buf_chapter, buf_section = ch, sec
        buf.append(para)
        buf_len += len(para) + (2 if len(buf) > 1 else 0)
        buf_section = sec if sec is not None else buf_section

    flush()

    if not chunks:
        return [
            TextChunk(
                text=cleaned,
                chapter=default_chapter,
                section=default_section,
                chunk_index=0,
            )
        ]

    # Re-number indexes
    for i, c in enumerate(chunks):
        c.chunk_index = i
    return chunks


def process_document(
    file_bytes: bytes,
    filename: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[TextChunk]:
    """Complete pipeline: extract text and structure-aware chunk it."""
    raw_text = extract_text_from_bytes(file_bytes, filename)
    return chunk_document(raw_text, chunk_size=chunk_size, overlap=overlap)
