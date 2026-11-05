"""Child process for bounded synthetic document extraction."""
import io
import json
import sys
import zipfile

from core import MAX_BYTES

MAX_PAGES = 30
MAX_CHARS = 120_000


def extract(data, kind):
    if kind == "text":
        parts = [("section 1", data.decode("utf-8").strip())]
    elif kind == "pdf":
        from pypdf import PdfReader
        pdf = PdfReader(io.BytesIO(data))
        if pdf.is_encrypted or len(pdf.pages) > MAX_PAGES:
            raise ValueError("encrypted or too many pages")
        parts = [(f"page {i}", page.extract_text().strip()) for i, page in enumerate(pdf.pages, 1)]
    elif kind == "docx":
        from docx import Document
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > 300 or sum(x.file_size for x in entries) > 8 * MAX_BYTES:
                raise ValueError("DOCX archive too large")
        document = Document(io.BytesIO(data))
        parts = [(f"paragraph {i}", p.text.strip()) for i, p in enumerate(document.paragraphs, 1)]
        for table_index, table in enumerate(document.tables, 1):
            parts.append((f"table {table_index}", "\n".join(
                " | ".join(cell.text for cell in row.cells) for row in table.rows)))
    else:
        raise ValueError("unsupported format")
    if sum(len(text) for _, text in parts) > MAX_CHARS:
        raise ValueError("extracted text too large")
    return parts


if __name__ == "__main__":
    data = sys.stdin.buffer.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        raise SystemExit("invalid upload size")
    print(json.dumps(extract(data, sys.argv[1])))
