import re

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge_models import (
    Document,
    KnowledgeEntity,
    KnowledgeRelation,
)
from app.services.text_processing import normalize_text, tokenize_text

CAPITALIZED_TERM = re.compile(r"\b[A-Z][A-Za-z0-9_-]{2,}(?:\s+[A-Z][A-Za-z0-9_-]{2,})?\b")


def extract_entity_names(document: Document) -> list[str]:
    names: list[str] = []
    names.extend(CAPITALIZED_TERM.findall(document.title))
    names.extend(tag.name for tag in document.tags)
    names.extend(CAPITALIZED_TERM.findall(document.content[:5000]))
    for token in tokenize_text(document.title):
        if len(token) >= 3:
            names.append(token)
    unique = []
    seen = set()
    for name in names:
        cleaned = normalize_text(name).strip(".,;:()[]{}")
        key = cleaned.lower()
        if len(cleaned) >= 2 and key not in seen:
            unique.append(cleaned[:255])
            seen.add(key)
    return unique[:12]


async def get_or_create_entity(
    db: AsyncSession, name: str, entity_type: str = "concept"
) -> KnowledgeEntity:
    entity = await db.scalar(
        select(KnowledgeEntity).where(
            func.lower(KnowledgeEntity.name) == name.lower(),
            KnowledgeEntity.entity_type == entity_type,
        )
    )
    if entity:
        return entity
    entity = KnowledgeEntity(name=name, entity_type=entity_type, entity_metadata={})
    db.add(entity)
    await db.flush()
    return entity


async def extract_graph_for_document(db: AsyncSession, document: Document) -> tuple[int, int]:
    await db.execute(delete(KnowledgeRelation).where(KnowledgeRelation.document_id == document.id))
    names = extract_entity_names(document)
    if not names:
        await db.commit()
        return 0, 0
    document_entity = await get_or_create_entity(db, document.title, "document")
    concept_entities = [
        await get_or_create_entity(db, name)
        for name in names
        if name != document.title
    ]
    relation_count = 0
    for entity in concept_entities:
        db.add(
            KnowledgeRelation(
                source_entity_id=document_entity.id,
                target_entity_id=entity.id,
                relation_type="mentions",
                document_id=document.id,
                confidence=0.75,
                evidence=document.content[:500] or document.title,
                relation_metadata={},
            )
        )
        relation_count += 1
    for left, right in zip(concept_entities, concept_entities[1:], strict=False):
        db.add(
            KnowledgeRelation(
                source_entity_id=left.id,
                target_entity_id=right.id,
                relation_type="related_to",
                document_id=document.id,
                confidence=0.55,
                evidence=document.title,
                relation_metadata={},
            )
        )
        relation_count += 1
    await db.commit()
    return len(concept_entities) + 1, relation_count
