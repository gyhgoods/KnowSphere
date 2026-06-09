from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import DB, CurrentUser, has_permission, require_permission
from app.common.exceptions import AppError
from app.common.pagination import Page
from app.knowledge_models import (
    Category,
    Document,
    DocumentFile,
    DocumentStatus,
    DocumentVersion,
    KnowledgeSpace,
    SpaceVisibility,
    Tag,
)
from app.knowledge_schemas import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    DocumentCreate,
    DocumentRead,
    DocumentUpdate,
    ReviewRequest,
    SpaceCreate,
    SpaceRead,
    SpaceUpdate,
    TagCreate,
    TagRead,
    VersionRead,
)
from app.models import Department
from app.services.authorization import can_access_resource
from app.services.storage import get_storage
from app.tasks.document_index_task import enqueue_document_index

router = APIRouter(tags=["Knowledge"])


def category_tree(rows: list[Category]) -> list[CategoryRead]:
    nodes = {
        row.id: CategoryRead(
            id=row.id,
            space_id=row.space_id,
            parent_id=row.parent_id,
            name=row.name,
            sort=row.sort,
            children=[],
        )
        for row in rows
    }
    roots: list[CategoryRead] = []
    for row in rows:
        node = nodes[row.id]
        if row.parent_id and row.parent_id in nodes:
            nodes[row.parent_id].children.append(node)
        else:
            roots.append(node)

    def sort_nodes(items: list[CategoryRead]) -> None:
        items.sort(key=lambda item: (item.sort, item.id))
        for item in items:
            sort_nodes(item.children)

    sort_nodes(roots)
    return roots


def category_read(category: Category) -> CategoryRead:
    return CategoryRead(
        id=category.id,
        space_id=category.space_id,
        parent_id=category.parent_id,
        name=category.name,
        sort=category.sort,
        children=[],
    )


async def get_space(db: AsyncSession, space_id: int) -> KnowledgeSpace:
    space = await db.get(KnowledgeSpace, space_id)
    if not space or not space.is_active:
        raise AppError("space_not_found", "Knowledge space does not exist", 404)
    return space


async def can_use_space(
    db: AsyncSession, user: CurrentUser, space: KnowledgeSpace, action: str
) -> bool:
    if user.is_superuser or space.created_by == user.id:
        return True
    if action == "view":
        if space.visibility == SpaceVisibility.PUBLIC:
            return True
        if (
            space.visibility == SpaceVisibility.DEPARTMENT
            and user.department_id
            and user.department_id == space.department_id
        ):
            return True
    return await can_access_resource(db, user, "space", str(space.id), action)


async def ensure_space_access(
    db: AsyncSession, user: CurrentUser, space: KnowledgeSpace, action: str
) -> None:
    if not await can_use_space(db, user, space, action):
        raise AppError("space_access_denied", "You cannot access this knowledge space", 403)


async def get_document(db: AsyncSession, document_id: int) -> Document:
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id, Document.is_deleted.is_(False))
        .options(selectinload(Document.tags), selectinload(Document.files))
    )
    document = result.scalar_one_or_none()
    if not document:
        raise AppError("document_not_found", "Document does not exist", 404)
    return document


async def ensure_document_access(
    db: AsyncSession, user: CurrentUser, document: Document, action: str
) -> None:
    if user.is_superuser or document.author_id == user.id:
        return
    space = await get_space(db, document.space_id)
    if action == "view" and await can_use_space(db, user, space, "view"):
        return
    if await can_access_resource(db, user, "document", str(document.id), action):
        return
    if await can_access_resource(db, user, "space", str(document.space_id), action):
        return
    raise AppError("document_access_denied", "You cannot access this document", 403)


async def tags_by_ids(db: AsyncSession, ids: list[int]) -> list[Tag]:
    if not ids:
        return []
    tags = list((await db.execute(select(Tag).where(Tag.id.in_(ids)))).scalars())
    if len(tags) != len(set(ids)):
        raise AppError("tag_not_found", "One or more tags do not exist", 404)
    return tags


async def validate_category(
    db: AsyncSession, space_id: int, category_id: int | None
) -> Category | None:
    if category_id is None:
        return None
    category = await db.get(Category, category_id)
    if not category or category.space_id != space_id:
        raise AppError("category_not_found", "Category does not belong to this space", 404)
    return category


def add_version(document: Document, user_id: int) -> DocumentVersion:
    document.version_no += 1
    return DocumentVersion(
        document_id=document.id,
        version_no=document.version_no,
        title=document.title,
        content=document.content,
        content_format=document.content_format,
        created_by=user_id,
    )


async def enqueue_index(document_id: int) -> None:
    try:
        await run_in_threadpool(enqueue_document_index, document_id)
    except Exception:
        # Document persistence must not fail when the async worker is unavailable.
        return


@router.get("/spaces", response_model=list[SpaceRead])
async def list_spaces(db: DB, user: CurrentUser) -> list[KnowledgeSpace]:
    spaces = list(
        (
            await db.execute(
                select(KnowledgeSpace).where(KnowledgeSpace.is_active.is_(True))
            )
        ).scalars()
    )
    return [space for space in spaces if await can_use_space(db, user, space, "view")]


@router.post(
    "/spaces",
    response_model=SpaceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("space.manage"))],
)
async def create_space(payload: SpaceCreate, db: DB, user: CurrentUser) -> KnowledgeSpace:
    if await db.scalar(select(KnowledgeSpace.id).where(KnowledgeSpace.code == payload.code)):
        raise AppError("space_exists", "Knowledge space code already exists", 409)
    if payload.department_id and not await db.get(Department, payload.department_id):
        raise AppError("department_not_found", "Department does not exist", 404)
    space = KnowledgeSpace(**payload.model_dump(), created_by=user.id)
    db.add(space)
    await db.commit()
    await db.refresh(space)
    return space


@router.patch(
    "/spaces/{space_id}",
    response_model=SpaceRead,
    dependencies=[Depends(require_permission("space.manage"))],
)
async def update_space(
    space_id: int, payload: SpaceUpdate, db: DB, user: CurrentUser
) -> KnowledgeSpace:
    space = await get_space(db, space_id)
    await ensure_space_access(db, user, space, "manage")
    values = payload.model_dump(exclude_unset=True)
    if values.get("department_id") and not await db.get(Department, values["department_id"]):
        raise AppError("department_not_found", "Department does not exist", 404)
    for key, value in values.items():
        setattr(space, key, value)
    await db.commit()
    await db.refresh(space)
    return space


async def delete_stored_files(db: AsyncSession, document_filter) -> None:
    object_names = list(
        (
            await db.execute(
                select(DocumentFile.object_name)
                .join(Document, Document.id == DocumentFile.document_id)
                .where(document_filter)
            )
        ).scalars()
    )
    if object_names:
        await run_in_threadpool(get_storage().delete_many, object_names)


@router.delete(
    "/spaces/{space_id}",
    status_code=204,
    dependencies=[Depends(require_permission("space.manage"))],
)
async def delete_space(space_id: int, db: DB, user: CurrentUser) -> Response:
    space = await get_space(db, space_id)
    await ensure_space_access(db, user, space, "manage")
    await delete_stored_files(db, Document.space_id == space_id)
    await db.delete(space)
    await db.commit()
    return Response(status_code=204)


@router.get("/spaces/{space_id}/categories", response_model=list[CategoryRead])
async def list_categories(space_id: int, db: DB, user: CurrentUser) -> list[CategoryRead]:
    space = await get_space(db, space_id)
    await ensure_space_access(db, user, space, "view")
    rows = list(
        (
            await db.execute(
                select(Category)
                .where(Category.space_id == space_id)
                .order_by(Category.sort, Category.id)
            )
        ).scalars()
    )
    return category_tree(rows)


@router.post(
    "/spaces/{space_id}/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("category.manage"))],
)
async def create_category(
    space_id: int, payload: CategoryCreate, db: DB, user: CurrentUser
) -> CategoryRead:
    space = await get_space(db, space_id)
    await ensure_space_access(db, user, space, "manage")
    if payload.parent_id:
        await validate_category(db, space_id, payload.parent_id)
    category = Category(space_id=space_id, **payload.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category_read(category)


async def category_is_descendant(
    db: AsyncSession, category_id: int, candidate_parent_id: int
) -> bool:
    current = await db.get(Category, candidate_parent_id)
    while current:
        if current.id == category_id:
            return True
        current = await db.get(Category, current.parent_id) if current.parent_id else None
    return False


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryRead,
    dependencies=[Depends(require_permission("category.manage"))],
)
async def update_category(
    category_id: int, payload: CategoryUpdate, db: DB, user: CurrentUser
) -> CategoryRead:
    category = await db.get(Category, category_id)
    if not category:
        raise AppError("category_not_found", "Category does not exist", 404)
    space = await get_space(db, category.space_id)
    await ensure_space_access(db, user, space, "manage")
    values = payload.model_dump(exclude_unset=True)
    if "parent_id" in values and values["parent_id"] is not None:
        parent = await validate_category(db, category.space_id, values["parent_id"])
        if parent and (
            parent.id == category.id
            or await category_is_descendant(db, category.id, parent.id)
        ):
            raise AppError("category_cycle", "Category hierarchy cannot contain a cycle")
    for key, value in values.items():
        setattr(category, key, value)
    await db.commit()
    await db.refresh(category)
    return category_read(category)


@router.delete(
    "/categories/{category_id}",
    status_code=204,
    dependencies=[Depends(require_permission("category.manage"))],
)
async def delete_category(category_id: int, db: DB, user: CurrentUser) -> Response:
    category = await db.get(Category, category_id)
    if not category:
        raise AppError("category_not_found", "Category does not exist", 404)
    space = await get_space(db, category.space_id)
    await ensure_space_access(db, user, space, "manage")
    descendant_ids = (
        select(Category.id)
        .where(Category.id == category_id)
        .cte(name="category_descendants", recursive=True)
    )
    descendant_ids = descendant_ids.union_all(
        select(Category.id).where(Category.parent_id == descendant_ids.c.id)
    )
    category_ids = select(descendant_ids.c.id)
    await delete_stored_files(db, Document.category_id.in_(category_ids))
    await db.delete(category)
    await db.commit()
    return Response(status_code=204)


@router.get("/tags", response_model=list[TagRead])
async def list_tags(db: DB, user: CurrentUser) -> list[Tag]:
    result = await db.execute(select(Tag).order_by(Tag.usage_count.desc(), Tag.name))
    return list(result.scalars())


@router.post(
    "/tags",
    response_model=TagRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("tag.manage"))],
)
async def create_tag(payload: TagCreate, db: DB) -> Tag:
    if await db.scalar(select(Tag.id).where(func.lower(Tag.name) == payload.name.lower())):
        raise AppError("tag_exists", "Tag already exists", 409)
    tag = Tag(**payload.model_dump())
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete(
    "/tags/{tag_id}",
    status_code=204,
    dependencies=[Depends(require_permission("tag.manage"))],
)
async def delete_tag(tag_id: int, db: DB) -> Response:
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise AppError("tag_not_found", "Tag does not exist", 404)
    await db.delete(tag)
    await db.commit()
    return Response(status_code=204)


@router.get("/documents", response_model=Page[DocumentRead])
async def list_documents(
    db: DB,
    user: CurrentUser,
    space_id: int,
    category_id: int | None = None,
    status_filter: Annotated[DocumentStatus | None, Query(alias="status")] = None,
    keyword: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[DocumentRead]:
    space = await get_space(db, space_id)
    await ensure_space_access(db, user, space, "view")
    filters = [Document.space_id == space_id, Document.is_deleted.is_(False)]
    if category_id:
        filters.append(Document.category_id == category_id)
    if status_filter:
        filters.append(Document.status == status_filter)
    if keyword:
        pattern = f"%{keyword}%"
        filters.append(or_(Document.title.ilike(pattern), Document.content.ilike(pattern)))
    total = await db.scalar(select(func.count()).select_from(Document).where(*filters))
    result = await db.execute(
        select(Document)
        .where(*filters)
        .options(selectinload(Document.tags))
        .order_by(Document.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return Page(
        items=[DocumentRead.model_validate(item) for item in result.scalars()],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("document.create"))],
)
async def create_document(
    payload: DocumentCreate, db: DB, user: CurrentUser
) -> Document:
    space = await get_space(db, payload.space_id)
    await ensure_space_access(db, user, space, "edit")
    await validate_category(db, payload.space_id, payload.category_id)
    tags = await tags_by_ids(db, payload.tag_ids)
    document = Document(
        **payload.model_dump(exclude={"tag_ids"}),
        author_id=user.id,
        tags=tags,
    )
    db.add(document)
    await db.flush()
    db.add(
        DocumentVersion(
            document_id=document.id,
            version_no=1,
            title=document.title,
            content=document.content,
            content_format=document.content_format,
            created_by=user.id,
        )
    )
    for tag in tags:
        tag.usage_count += 1
    await db.commit()
    await db.refresh(document)
    await enqueue_index(document.id)
    return document


@router.get("/documents/{document_id}", response_model=DocumentRead)
async def read_document(document_id: int, db: DB, user: CurrentUser) -> Document:
    document = await get_document(db, document_id)
    await ensure_document_access(db, user, document, "view")
    return document


@router.patch(
    "/documents/{document_id}",
    response_model=DocumentRead,
    dependencies=[Depends(require_permission("document.edit"))],
)
async def update_document(
    document_id: int, payload: DocumentUpdate, db: DB, user: CurrentUser
) -> Document:
    document = await get_document(db, document_id)
    await ensure_document_access(db, user, document, "edit")
    if document.status == DocumentStatus.IN_REVIEW:
        raise AppError("document_locked", "Document cannot be edited while in review", 409)
    values = payload.model_dump(exclude_unset=True)
    tag_ids = values.pop("tag_ids", None)
    if "category_id" in values:
        await validate_category(db, document.space_id, values["category_id"])
    changed_content = any(
        key in values and values[key] != getattr(document, key)
        for key in ("title", "content", "content_format")
    )
    for key, value in values.items():
        setattr(document, key, value)
    if tag_ids is not None:
        old_tags = {tag.id: tag for tag in document.tags}
        new_tags = await tags_by_ids(db, tag_ids)
        new_ids = {tag.id for tag in new_tags}
        for tag in old_tags.values():
            if tag.id not in new_ids:
                tag.usage_count = max(0, tag.usage_count - 1)
        for tag in new_tags:
            if tag.id not in old_tags:
                tag.usage_count += 1
        document.tags = new_tags
    if changed_content:
        db.add(add_version(document, user.id))
    if document.status in (DocumentStatus.REJECTED, DocumentStatus.PUBLISHED):
        document.status = DocumentStatus.DRAFT
        document.review_comment = None
    await db.commit()
    await db.refresh(document)
    if changed_content:
        await enqueue_index(document.id)
    return document


@router.delete(
    "/documents/{document_id}",
    status_code=204,
    dependencies=[Depends(require_permission("document.delete"))],
)
async def delete_document(document_id: int, db: DB, user: CurrentUser) -> Response:
    document = await get_document(db, document_id)
    await ensure_document_access(db, user, document, "delete")
    document.is_deleted = True
    await db.commit()
    return Response(status_code=204)


@router.post("/documents/{document_id}/submit", response_model=DocumentRead)
async def submit_document(document_id: int, db: DB, user: CurrentUser) -> Document:
    if not has_permission(user, "document.edit"):
        raise AppError("permission_denied", "Permission 'document.edit' is required", 403)
    document = await get_document(db, document_id)
    await ensure_document_access(db, user, document, "edit")
    if document.status not in (DocumentStatus.DRAFT, DocumentStatus.REJECTED):
        raise AppError("invalid_document_state", "Only drafts can be submitted", 409)
    document.status = DocumentStatus.IN_REVIEW
    document.review_comment = None
    await db.commit()
    await db.refresh(document)
    return document


@router.post(
    "/documents/{document_id}/approve",
    response_model=DocumentRead,
    dependencies=[Depends(require_permission("document.review"))],
)
async def approve_document(
    document_id: int, payload: ReviewRequest, db: DB, user: CurrentUser
) -> Document:
    document = await get_document(db, document_id)
    if document.status != DocumentStatus.IN_REVIEW:
        raise AppError("invalid_document_state", "Document is not in review", 409)
    document.status = DocumentStatus.PUBLISHED
    document.reviewer_id = user.id
    document.review_comment = payload.comment
    await db.commit()
    await db.refresh(document)
    return document


@router.post(
    "/documents/{document_id}/reject",
    response_model=DocumentRead,
    dependencies=[Depends(require_permission("document.review"))],
)
async def reject_document(
    document_id: int, payload: ReviewRequest, db: DB, user: CurrentUser
) -> Document:
    document = await get_document(db, document_id)
    if document.status != DocumentStatus.IN_REVIEW:
        raise AppError("invalid_document_state", "Document is not in review", 409)
    document.status = DocumentStatus.REJECTED
    document.reviewer_id = user.id
    document.review_comment = payload.comment
    await db.commit()
    await db.refresh(document)
    return document


@router.post(
    "/documents/{document_id}/archive",
    response_model=DocumentRead,
    dependencies=[Depends(require_permission("document.review"))],
)
async def archive_document(document_id: int, db: DB, user: CurrentUser) -> Document:
    document = await get_document(db, document_id)
    if document.status != DocumentStatus.PUBLISHED:
        raise AppError("invalid_document_state", "Only published documents can be archived", 409)
    document.status = DocumentStatus.ARCHIVED
    document.reviewer_id = user.id
    await db.commit()
    await db.refresh(document)
    return document


@router.get("/documents/{document_id}/versions", response_model=list[VersionRead])
async def list_versions(document_id: int, db: DB, user: CurrentUser) -> list[DocumentVersion]:
    document = await get_document(db, document_id)
    await ensure_document_access(db, user, document, "view")
    return list(
        (
            await db.execute(
                select(DocumentVersion)
                .where(DocumentVersion.document_id == document_id)
                .order_by(DocumentVersion.version_no.desc())
            )
        ).scalars()
    )


@router.post(
    "/documents/{document_id}/versions/{version_id}/restore",
    response_model=DocumentRead,
    dependencies=[Depends(require_permission("document.edit"))],
)
async def restore_version(
    document_id: int, version_id: int, db: DB, user: CurrentUser
) -> Document:
    document = await get_document(db, document_id)
    await ensure_document_access(db, user, document, "edit")
    version = await db.get(DocumentVersion, version_id)
    if not version or version.document_id != document_id:
        raise AppError("version_not_found", "Document version does not exist", 404)
    document.title = version.title
    document.content = version.content
    document.content_format = version.content_format
    document.status = DocumentStatus.DRAFT
    db.add(add_version(document, user.id))
    await db.commit()
    await db.refresh(document)
    await enqueue_index(document.id)
    return document
