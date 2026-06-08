from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import DB, require_permission
from app.common.exceptions import AppError
from app.models import Permission, ResourceGrant, Role
from app.schemas import (
    GrantCreate,
    GrantRead,
    PermissionCreate,
    PermissionRead,
    RoleCreate,
    RoleRead,
    RoleUpdate,
)

router = APIRouter(
    prefix="/rbac",
    tags=["RBAC"],
    dependencies=[Depends(require_permission("rbac.manage"))],
)


async def permissions_by_ids(db: DB, ids: list[int]) -> list[Permission]:
    if not ids:
        return []
    result = await db.execute(select(Permission).where(Permission.id.in_(ids)))
    permissions = list(result.scalars())
    if len(permissions) != len(set(ids)):
        raise AppError("permission_not_found", "One or more permissions do not exist", 404)
    return permissions


@router.get("/permissions", response_model=list[PermissionRead])
async def list_permissions(db: DB) -> list[Permission]:
    return list((await db.execute(select(Permission).order_by(Permission.code))).scalars())


@router.post(
    "/permissions", response_model=PermissionRead, status_code=status.HTTP_201_CREATED
)
async def create_permission(payload: PermissionCreate, db: DB) -> Permission:
    if await db.scalar(select(Permission.id).where(Permission.code == payload.code)):
        raise AppError("permission_exists", "Permission code already exists", 409)
    permission = Permission(**payload.model_dump())
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    return permission


@router.get("/roles", response_model=list[RoleRead])
async def list_roles(db: DB) -> list[Role]:
    result = await db.execute(
        select(Role).options(selectinload(Role.permissions)).order_by(Role.id)
    )
    return list(result.scalars())


@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(payload: RoleCreate, db: DB) -> Role:
    if await db.scalar(select(Role.id).where(Role.code == payload.code)):
        raise AppError("role_exists", "Role code already exists", 409)
    role = Role(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        permissions=await permissions_by_ids(db, payload.permission_ids),
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


@router.patch("/roles/{role_id}", response_model=RoleRead)
async def update_role(role_id: int, payload: RoleUpdate, db: DB) -> Role:
    result = await db.execute(
        select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
    )
    role = result.scalar_one_or_none()
    if not role:
        raise AppError("role_not_found", "Role does not exist", 404)
    values = payload.model_dump(exclude_unset=True)
    permission_ids = values.pop("permission_ids", None)
    if permission_ids is not None:
        role.permissions = await permissions_by_ids(db, permission_ids)
    for key, value in values.items():
        setattr(role, key, value)
    await db.commit()
    await db.refresh(role)
    return role


@router.get("/grants", response_model=list[GrantRead])
async def list_grants(db: DB) -> list[ResourceGrant]:
    return list((await db.execute(select(ResourceGrant).order_by(ResourceGrant.id))).scalars())


@router.post("/grants", response_model=GrantRead, status_code=status.HTTP_201_CREATED)
async def create_grant(payload: GrantCreate, db: DB) -> ResourceGrant:
    grant = ResourceGrant(**payload.model_dump())
    db.add(grant)
    try:
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise AppError("grant_exists", "The resource grant already exists", 409) from exc
    await db.refresh(grant)
    return grant


@router.delete("/grants/{grant_id}", status_code=204)
async def delete_grant(grant_id: int, db: DB) -> Response:
    grant = await db.get(ResourceGrant, grant_id)
    if not grant:
        raise AppError("grant_not_found", "Resource grant does not exist", 404)
    await db.delete(grant)
    await db.commit()
    return Response(status_code=204)

