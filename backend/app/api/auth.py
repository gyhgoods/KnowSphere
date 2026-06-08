from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.api.dependencies import DB, CurrentUser
from app.common.exceptions import AppError
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    token_fingerprint,
    verify_password,
)
from app.models import RefreshToken, Role, User, UserStatus
from app.schemas import RefreshRequest, SessionUserRead, TokenPair, UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def issue_tokens(db: DB, user: User) -> TokenPair:
    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_fingerprint(refresh),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    await db.commit()
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenPair)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB) -> TokenPair:
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()
    if (
        not user
        or user.status != UserStatus.ACTIVE
        or not verify_password(form.password, user.password_hash)
    ):
        raise AppError("invalid_credentials", "Incorrect username or password", 401)
    return await issue_tokens(db, user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: DB) -> TokenPair:
    try:
        claims = decode_token(payload.refresh_token, "refresh")
        user_id = int(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise AppError("invalid_refresh_token", "Refresh token is invalid", 401) from exc

    fingerprint = token_fingerprint(payload.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == fingerprint,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(UTC),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise AppError("invalid_refresh_token", "Refresh token is expired or revoked", 401)

    stored.revoked_at = datetime.now(UTC)
    user = await db.get(User, user_id)
    if not user or user.status != UserStatus.ACTIVE:
        raise AppError("inactive_user", "User is inactive or does not exist", 401)
    return await issue_tokens(db, user)


@router.post("/logout", status_code=204)
async def logout(payload: RefreshRequest, db: DB) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_fingerprint(payload.refresh_token))
        .values(revoked_at=datetime.now(UTC))
    )
    await db.commit()


@router.get("/me", response_model=SessionUserRead)
async def me(user: CurrentUser, db: DB) -> SessionUserRead:
    result = await db.execute(
        select(User)
        .where(User.id == user.id)
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )
    loaded_user = result.scalar_one()
    permission_codes = sorted(
        {permission.code for role in loaded_user.roles for permission in role.permissions}
    )
    if loaded_user.is_superuser:
        permission_codes.append("*")
    base_user = UserRead.model_validate(loaded_user)
    return SessionUserRead(**base_user.model_dump(), permission_codes=permission_codes)
