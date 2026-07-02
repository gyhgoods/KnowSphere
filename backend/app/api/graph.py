from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.ai_schemas import (
    GraphEntityRead,
    GraphExtractRequest,
    GraphExtractResponse,
    GraphRelationFilter,
    GraphRelationRead,
    GraphResponse,
)
from app.api.dependencies import DB, CurrentUser
from app.api.knowledge import ensure_document_access, get_document
from app.common.exceptions import AppError
from app.knowledge_models import Document, KnowledgeEntity, KnowledgeRelation
from app.services.knowledge_graph import extract_graph_for_document

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


@router.post("/extract", response_model=GraphExtractResponse)
async def extract_graph(
    payload: GraphExtractRequest, db: DB, user: CurrentUser
) -> GraphExtractResponse:
    document = await get_document(db, payload.document_id)
    await ensure_document_access(db, user, document, "view")
    entity_count, relation_count = await extract_graph_for_document(db, document)
    return GraphExtractResponse(
        document_id=document.id,
        entity_count=entity_count,
        relation_count=relation_count,
    )


@router.get("", response_model=GraphResponse)
async def read_graph(
    db: DB,
    user: CurrentUser,
    space_id: int | None = None,
    relation_filter: GraphRelationFilter = GraphRelationFilter.ALL,
    limit: int = 80,
) -> GraphResponse:
    filters = [Document.id == KnowledgeRelation.document_id, Document.is_deleted.is_(False)]
    if space_id is not None:
        filters.append(Document.space_id == space_id)
    if relation_filter == GraphRelationFilter.STRONG:
        filters.append(KnowledgeRelation.confidence >= 0.7)
    rows = (
        await db.execute(
            select(KnowledgeRelation)
            .join(Document, Document.id == KnowledgeRelation.document_id)
            .where(*filters)
            .options(
                selectinload(KnowledgeRelation.source_entity),
                selectinload(KnowledgeRelation.target_entity),
                selectinload(KnowledgeRelation.document),
            )
            .order_by(KnowledgeRelation.confidence.desc(), KnowledgeRelation.updated_at.desc())
            .limit(min(max(limit, 1), 200))
        )
    ).scalars()

    relations: list[GraphRelationRead] = []
    entity_map: dict[int, KnowledgeEntity] = {}
    for relation in rows:
        try:
            await ensure_document_access(db, user, relation.document, "view")
        except AppError:
            continue
        entity_map[relation.source_entity.id] = relation.source_entity
        entity_map[relation.target_entity.id] = relation.target_entity
        relations.append(
            GraphRelationRead(
                id=relation.id,
                source_entity_id=relation.source_entity_id,
                source_name=relation.source_entity.name,
                target_entity_id=relation.target_entity_id,
                target_name=relation.target_entity.name,
                relation_type=relation.relation_type,
                document_id=relation.document_id,
                document_title=relation.document.title,
                confidence=relation.confidence,
                evidence=relation.evidence,
            )
        )
    return GraphResponse(
        entities=[
            GraphEntityRead(
                id=entity.id,
                name=entity.name,
                entity_type=entity.entity_type,
                description=entity.description,
            )
            for entity in entity_map.values()
        ],
        relations=relations,
    )
