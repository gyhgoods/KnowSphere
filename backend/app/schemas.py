from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import GrantEffect, UserStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    parent_id: int | None = None
    sort: int = 0


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: int | None = None
    sort: int | None = None
    is_active: bool | None = None


class DepartmentRead(ORMModel):
    id: int
    parent_id: int | None
    name: str
    sort: int
    is_active: bool
    children: list["DepartmentRead"] = Field(default_factory=list)


class RoleSummary(ORMModel):
    id: int
    code: str
    name: str


class UserCreate(BaseModel):
    username: str = Field(pattern=r"^[a-zA-Z0-9_.-]+$", min_length=3, max_length=64)
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    department_id: int | None = None
    role_ids: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    department_id: int | None = None
    status: UserStatus | None = None
    role_ids: list[int] | None = None


class PasswordReset(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class UserRead(ORMModel):
    id: int
    username: str
    email: str
    display_name: str
    department_id: int | None
    status: UserStatus
    is_superuser: bool
    roles: list[RoleSummary]
    created_at: datetime


class SessionUserRead(UserRead):
    permission_codes: list[str]


class PermissionCreate(BaseModel):
    code: str = Field(pattern=r"^[a-z0-9_.:-]+$", max_length=100)
    name: str = Field(min_length=1, max_length=100)
    resource_type: str = Field(min_length=1, max_length=64)
    action: str = Field(min_length=1, max_length=32)
    description: str | None = None


class PermissionRead(ORMModel):
    id: int
    code: str
    name: str
    resource_type: str
    action: str
    description: str | None


class RoleCreate(BaseModel):
    code: str = Field(pattern=r"^[a-z0-9_.:-]+$", max_length=64)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    permission_ids: list[int] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    permission_ids: list[int] | None = None


class RoleRead(ORMModel):
    id: int
    code: str
    name: str
    description: str | None
    is_system: bool
    permissions: list[PermissionRead]


class GrantCreate(BaseModel):
    subject_type: str = Field(pattern=r"^(user|role|department)$")
    subject_id: int
    resource_type: str = Field(pattern=r"^(space|project|document)$")
    resource_id: str = Field(min_length=1, max_length=64)
    action: str = Field(min_length=1, max_length=32)
    effect: GrantEffect = GrantEffect.ALLOW


class GrantRead(ORMModel):
    id: int
    subject_type: str
    subject_id: int
    resource_type: str
    resource_id: str
    action: str
    effect: GrantEffect
