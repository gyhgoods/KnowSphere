import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.tasks.document_index_task import index_document
from app.tasks.document_parse_task import parse_document_file


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "ChangeMe123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_knowledge_document_review_and_file_flow() -> None:
    suffix = uuid.uuid4().hex[:8]
    with TestClient(app) as client:
        headers = auth_headers(client)

        space_response = client.post(
            "/api/v1/spaces",
            headers=headers,
            json={
                "name": f"Integration Space {suffix}",
                "code": f"integration-{suffix}",
                "visibility": "private",
            },
        )
        assert space_response.status_code == 201, space_response.text
        space_id = space_response.json()["id"]

        category_response = client.post(
            f"/api/v1/spaces/{space_id}/categories",
            headers=headers,
            json={"name": "Guides", "sort": 1},
        )
        assert category_response.status_code == 201, category_response.text
        category_id = category_response.json()["id"]

        child_category_response = client.post(
            f"/api/v1/spaces/{space_id}/categories",
            headers=headers,
            json={"name": "Nested Guides", "parent_id": category_id, "sort": 1},
        )
        assert child_category_response.status_code == 201, child_category_response.text
        child_category_id = child_category_response.json()["id"]

        tag_response = client.post(
            "/api/v1/tags",
            headers=headers,
            json={"name": f"tag-{suffix}", "color": "#087f61"},
        )
        assert tag_response.status_code == 201, tag_response.text
        tag_id = tag_response.json()["id"]

        document_response = client.post(
            "/api/v1/documents",
            headers=headers,
            json={
                "space_id": space_id,
                "category_id": child_category_id,
                "title": "Getting started",
                "content": "Version one",
                "content_format": "markdown",
                "tag_ids": [tag_id],
            },
        )
        assert document_response.status_code == 201, document_response.text
        document_id = document_response.json()["id"]

        update_response = client.patch(
            f"/api/v1/documents/{document_id}",
            headers=headers,
            json={"content": "Version two"},
        )
        assert update_response.status_code == 200, update_response.text
        assert update_response.json()["version_no"] == 2

        index_result = index_document.run(document_id)
        assert index_result["chunk_count"] >= 1

        chunks = client.get(
            f"/api/v1/documents/{document_id}/chunks", headers=headers
        )
        assert chunks.status_code == 200, chunks.text
        assert any("Version two" in item["content"] for item in chunks.json())

        semantic = client.post(
            "/api/v1/search/semantic",
            headers=headers,
            json={"query": "Version two", "space_id": space_id, "limit": 5},
        )
        assert semantic.status_code == 200, semantic.text
        assert semantic.json()["items"][0]["document_id"] == document_id

        hybrid = client.post(
            "/api/v1/search/hybrid",
            headers=headers,
            json={
                "query": "Version two",
                "space_id": space_id,
                "category_id": child_category_id,
                "tag_ids": [tag_id],
                "source_type": "document",
                "mode": "hybrid",
                "limit": 5,
            },
        )
        assert hybrid.status_code == 200, hybrid.text
        assert hybrid.json()["items"][0]["document_id"] == document_id
        assert hybrid.json()["items"][0]["score"]["rerank"] > 0
        assert "content_phrase" in hybrid.json()["items"][0]["explanations"]

        versions = client.get(
            f"/api/v1/documents/{document_id}/versions", headers=headers
        )
        assert versions.status_code == 200
        assert [item["version_no"] for item in versions.json()] == [2, 1]

        submitted = client.post(
            f"/api/v1/documents/{document_id}/submit", headers=headers
        )
        assert submitted.status_code == 200
        assert submitted.json()["status"] == "in_review"

        approved = client.post(
            f"/api/v1/documents/{document_id}/approve",
            headers=headers,
            json={"comment": "Ready to publish"},
        )
        assert approved.status_code == 200
        assert approved.json()["status"] == "published"

        uploaded = client.post(
            f"/api/v1/files/documents/{document_id}",
            headers=headers,
            files={"file": ("guide.txt", b"KnowSphere integration file", "text/plain")},
        )
        assert uploaded.status_code == 201, uploaded.text
        file_id = uploaded.json()["id"]
        assert uploaded.json()["parse_status"] in {
            "queued",
            "processing",
            "completed",
            "failed",
        }

        task_result = parse_document_file.run(file_id)
        assert task_result["status"] == "completed"
        file_index_result = index_document.run(document_id, file_id)
        assert file_index_result["chunk_count"] == 1

        parse_status = client.get(f"/api/v1/files/{file_id}/parse", headers=headers)
        assert parse_status.status_code == 200
        assert parse_status.json()["parse_status"] == "completed"
        assert parse_status.json()["parsed_text"] == "KnowSphere integration file"

        preview = client.get(f"/api/v1/files/{file_id}/preview", headers=headers)
        download = client.get(f"/api/v1/files/{file_id}/download", headers=headers)
        assert preview.status_code == 200, preview.text
        assert preview.json()["previewable"] is True
        assert download.status_code == 200
        assert download.json()["url"].startswith("http")

        deleted = client.delete(f"/api/v1/files/{file_id}", headers=headers)
        assert deleted.status_code == 204

        deleted_category = client.delete(
            f"/api/v1/categories/{category_id}", headers=headers
        )
        assert deleted_category.status_code == 204
        missing_document = client.get(
            f"/api/v1/documents/{document_id}", headers=headers
        )
        assert missing_document.status_code == 404

        deleted_tag = client.delete(f"/api/v1/tags/{tag_id}", headers=headers)
        assert deleted_tag.status_code == 204

        deleted_space = client.delete(f"/api/v1/spaces/{space_id}", headers=headers)
        assert deleted_space.status_code == 204
