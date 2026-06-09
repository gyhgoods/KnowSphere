from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.exceptions import AppError
from app.core.database import get_db
from app.core.security import decode_token
from app.models import Role, User, UserStatus

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
DB = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(db: DB, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    try:
        payload = decode_token(token, "access")
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise AppError("invalid_token", "Authentication token is invalid", 401) from exc

    result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )
    user = result.scalar_one_or_none()
    if not user or user.status != UserStatus.ACTIVE:
        raise AppError("inactive_user", "User is inactive or does not exist", 401)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def has_permission(user: User, code: str) -> bool:
    if user.is_superuser:
        return True
    return any(permission.code == code for role in user.roles for permission in role.permissions)


def require_permission(code: str) -> Callable:
    async def dependency(user: CurrentUser) -> User:
        if not has_permission(user, code):
            raise AppError("permission_denied", f"Permission '{code}' is required", 403)
        return user

    return dependency
