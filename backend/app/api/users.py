from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.api.dependencies import DB, require_permission
from app.common.exceptions import AppError
from app.common.pagination import Page
from app.core.security import hash_password
from app.models import Department, Role, User
from app.schemas import PasswordReset, UserCreate, UserRead, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(require_permission("user.manage"))],
)


async def load_roles(db: DB, role_ids: list[int]) -> list[Role]:
    if not role_ids:
        return []
    result = await db.execute(select(Role).where(Role.id.in_(role_ids)))
    roles = list(result.scalars())
    if len(roles) != len(set(role_ids)):
        raise AppError("role_not_found", "One or more roles do not exist", 404)
    return roles


@router.get("", response_model=Page[UserRead])
async def list_users(
    db: DB,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    department_id: int | None = None,
) -> Page[UserRead]:
    filters = []
    if keyword:
        pattern = f"%{keyword}%"
        filters.append(
            or_(
                User.username.ilike(pattern),
                User.email.ilike(pattern),
                User.display_name.ilike(pattern),
            )
        )
    if department_id:
        filters.append(User.department_id == department_id)

    total = await db.scalar(select(func.count()).select_from(User).where(*filters))
    result = await db.execute(
        select(User)
        .where(*filters)
        .options(selectinload(User.roles))
        .order_by(User.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return Page(
        items=[UserRead.model_validate(item) for item in result.scalars()],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: DB) -> User:
    duplicate = await db.scalar(
        select(User.id).where(or_(User.username == payload.username, User.email == payload.email))
    )
    if duplicate:
        raise AppError("user_exists", "Username or email already exists", 409)
    if payload.department_id and not await db.get(Department, payload.department_id):
        raise AppError("department_not_found", "Department does not exist", 404)
    user = User(
        username=payload.username,
        email=str(payload.email),
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
        department_id=payload.department_id,
        roles=await load_roles(db, payload.role_ids),
    )
    db.add(user)
    await db.commit()
    result = await db.execute(
        select(User).where(User.id == user.id).options(selectinload(User.roles))
    )
    return result.scalar_one()


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, payload: UserUpdate, db: DB) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.roles))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise AppError("user_not_found", "User does not exist", 404)
    values = payload.model_dump(exclude_unset=True)
    role_ids = values.pop("role_ids", None)
    if role_ids is not None:
        user.roles = await load_roles(db, role_ids)
    if "department_id" in values and values["department_id"]:
        if not await db.get(Department, values["department_id"]):
            raise AppError("department_not_found", "Department does not exist", 404)
    if "email" in values:
        values["email"] = str(values["email"])
    for key, value in values.items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/{user_id}/reset-password", status_code=204)
async def reset_password(user_id: int, payload: PasswordReset, db: DB) -> Response:
    user = await db.get(User, user_id)
    if not user:
        raise AppError("user_not_found", "User does not exist", 404)
    user.password_hash = hash_password(payload.password)
    await db.commit()
    return Response(status_code=204)

