from app.services.search_ranking import fuse_and_rerank, lexical_relevance


def test_lexical_relevance_prefers_title_phrase() -> None:
    title_score, title_reasons = lexical_relevance(
        "vector search",
        "Vector search guide",
        "A short introduction.",
    )
    content_score, content_reasons = lexical_relevance(
        "vector search",
        "Search guide",
        "This document explains vector search.",
    )

    assert title_score > content_score
    assert "title_phrase" in title_reasons
    assert "content_phrase" in content_reasons


def test_fusion_reranks_exact_title_match() -> None:
    ranked = fuse_and_rerank(
        semantic_score=0.7,
        lexical_score=0.8,
        semantic_weight=0.6,
        lexical_reasons=["title_phrase", "content_terms"],
        is_document_source=True,
    )

    assert ranked.fused == 0.74
    assert ranked.rerank > ranked.fused
    assert ranked.explanations == (
        "semantic_match",
        "title_phrase",
        "content_terms",
        "primary_document",
    )
