from app.services.embedding import EmbeddingService
from app.services.text_processing import normalize_text, split_text


def test_normalize_text_removes_noise_and_normalizes_unicode() -> None:
    value = "ＡＩ\u0000  knowledge \r\n\r\n\r\n  platform"

    assert normalize_text(value) == "AI knowledge\n\nplatform"


def test_split_text_creates_ordered_overlapping_chunks() -> None:
    text = " ".join(f"section-{index}" for index in range(100))

    chunks = split_text(text, chunk_size=160, chunk_overlap=30)

    assert len(chunks) > 1
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk.content and chunk.token_count > 0 for chunk in chunks)
    assert chunks[1].start_offset < chunks[0].end_offset


def test_hash_embedding_is_deterministic_and_normalized() -> None:
    service = EmbeddingService(provider="hash", dimension=1024)

    first, second = service.embed(["enterprise knowledge", "enterprise knowledge"])

    assert first == second
    assert len(first) == 1024
    assert abs(sum(value * value for value in first) - 1.0) < 0.000001
