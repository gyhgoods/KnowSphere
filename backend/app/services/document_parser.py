import csv
import json
from io import BytesIO, StringIO
from pathlib import Path

from docx import Document as WordDocument
from openpyxl import load_workbook
from pypdf import PdfReader

from app.services.text_processing import normalize_text


class UnsupportedDocumentTypeError(ValueError):
    pass


TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".log", ".xml", ".yaml", ".yml"}


def clean_text(parts: list[str]) -> str:
    return normalize_text("\n".join(part for part in parts if part))


def decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def parse_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return clean_text([page.extract_text() or "" for page in reader.pages])


def parse_word(content: bytes) -> str:
    document = WordDocument(BytesIO(content))
    parts = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.append("\t".join(cell.text.strip() for cell in row.cells))
    return clean_text(parts)


def parse_excel(content: bytes) -> str:
    workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    parts: list[str] = []
    try:
        for worksheet in workbook.worksheets:
            parts.append(f"[{worksheet.title}]")
            for row in worksheet.iter_rows(values_only=True):
                values = ["" if value is None else str(value) for value in row]
                if any(values):
                    parts.append("\t".join(values))
    finally:
        workbook.close()
    return clean_text(parts)


def parse_csv(content: bytes) -> str:
    text = decode_text(content)
    return clean_text(["\t".join(row) for row in csv.reader(StringIO(text))])


def parse_json(content: bytes) -> str:
    value = json.loads(decode_text(content))
    return json.dumps(value, ensure_ascii=False, indent=2)


def parse_document(file_name: str, mime_type: str, content: bytes) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".pdf" or mime_type == "application/pdf":
        return parse_pdf(content)
    if suffix == ".docx":
        return parse_word(content)
    if suffix == ".xlsx":
        return parse_excel(content)
    if suffix == ".csv" or mime_type == "text/csv":
        return parse_csv(content)
    if suffix == ".json" or mime_type == "application/json":
        return parse_json(content)
    if suffix in TEXT_SUFFIXES or mime_type.startswith("text/"):
        return clean_text(decode_text(content).splitlines())
    raise UnsupportedDocumentTypeError(f"Unsupported document type: {suffix or mime_type}")
