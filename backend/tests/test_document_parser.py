from io import BytesIO

import pytest
from docx import Document as WordDocument
from openpyxl import Workbook
from pypdf import PdfWriter

from app.services.document_parser import (
    UnsupportedDocumentTypeError,
    parse_document,
)


def test_parse_plain_text_csv_and_json() -> None:
    assert parse_document("guide.txt", "text/plain", "知识 文档".encode()) == "知识 文档"
    assert parse_document("data.csv", "text/csv", b"name,value\nalpha,1") == (
        "name\tvalue\nalpha\t1"
    )
    assert '"name": "KnowSphere"' in parse_document(
        "data.json", "application/json", b'{"name":"KnowSphere"}'
    )


def test_parse_word_document() -> None:
    stream = BytesIO()
    document = WordDocument()
    document.add_heading("KnowSphere", level=1)
    document.add_paragraph("Enterprise knowledge")
    document.save(stream)

    result = parse_document(
        "guide.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        stream.getvalue(),
    )
    assert "KnowSphere" in result
    assert "Enterprise knowledge" in result


def test_parse_excel_workbook() -> None:
    stream = BytesIO()
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Knowledge"
    worksheet.append(["title", "status"])
    worksheet.append(["Guide", "published"])
    workbook.save(stream)
    workbook.close()

    result = parse_document(
        "guide.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        stream.getvalue(),
    )
    assert "[Knowledge]" in result
    assert "Guide\tpublished" in result


def test_parse_pdf_document() -> None:
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(stream)

    assert parse_document("guide.pdf", "application/pdf", stream.getvalue()) == ""


def test_reject_unsupported_document() -> None:
    with pytest.raises(UnsupportedDocumentTypeError):
        parse_document("archive.zip", "application/zip", b"not a document")
