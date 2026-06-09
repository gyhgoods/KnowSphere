from app.services.storage import safe_file_name


def test_safe_file_name_removes_paths_and_null_bytes() -> None:
    assert safe_file_name("../../unsafe.txt") == "unsafe.txt"
    assert safe_file_name("report\x00.pdf") == "report.pdf"
