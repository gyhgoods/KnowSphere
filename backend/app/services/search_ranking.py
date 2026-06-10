from dataclasses import dataclass

from app.services.text_processing import normalize_text, tokenize_text


@dataclass(frozen=True, slots=True)
class RankedScore:
    lexical: float
    fused: float
    rerank: float
    explanations: tuple[str, ...]


def lexical_relevance(query: str, title: str, content: str) -> tuple[float, list[str]]:
    normalized_query = normalize_text(query).lower()
    normalized_title = normalize_text(title).lower()
    normalized_content = normalize_text(content).lower()
    query_tokens = list(dict.fromkeys(tokenize_text(normalized_query)))
    if not normalized_query or not query_tokens:
        return 0.0, []

    title_hits = sum(token in normalized_title for token in query_tokens)
    content_hits = sum(token in normalized_content for token in query_tokens)
    title_coverage = title_hits / len(query_tokens)
    content_coverage = content_hits / len(query_tokens)
    title_phrase = normalized_query in normalized_title
    content_phrase = normalized_query in normalized_content

    score = min(
        1.0,
        title_coverage * 0.55
        + content_coverage * 0.35
        + (0.25 if title_phrase else 0.0)
        + (0.15 if content_phrase else 0.0),
    )
    reasons: list[str] = []
    if title_phrase:
        reasons.append("title_phrase")
    elif title_hits:
        reasons.append("title_terms")
    if content_phrase:
        reasons.append("content_phrase")
    elif content_hits:
        reasons.append("content_terms")
    return score, reasons


def fuse_and_rerank(
    *,
    semantic_score: float,
    lexical_score: float,
    semantic_weight: float,
    lexical_reasons: list[str],
    is_document_source: bool,
) -> RankedScore:
    fused = semantic_score * semantic_weight + lexical_score * (1 - semantic_weight)
    boost = 0.0
    explanations: list[str] = []
    if semantic_score >= 0.7:
        explanations.append("semantic_match")
    explanations.extend(lexical_reasons)
    if "title_phrase" in lexical_reasons:
        boost += 0.08
    elif "title_terms" in lexical_reasons:
        boost += 0.04
    if "content_phrase" in lexical_reasons:
        boost += 0.03
    if is_document_source and fused > 0:
        boost += 0.01
        explanations.append("primary_document")
    rerank = min(1.0, fused + boost)
    return RankedScore(
        lexical=round(lexical_score, 6),
        fused=round(fused, 6),
        rerank=round(rerank, 6),
        explanations=tuple(dict.fromkeys(explanations)),
    )
