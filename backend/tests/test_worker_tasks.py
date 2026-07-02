from app.core.database import Base
from app.tasks import document_index_task, document_parse_task


def test_worker_tasks_import_all_foreign_key_tables() -> None:
    assert document_parse_task.update_file
    assert document_index_task.index_document_source
    assert "sys_user" in Base.metadata.tables
    assert "kb_document_file" in Base.metadata.tables
