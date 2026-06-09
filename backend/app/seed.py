import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Permission, Role, User

DEFAULT_PERMISSIONS = [
    ("user.manage", "Manage users", "user", "manage"),
    ("department.manage", "Manage departments", "department", "manage"),
    ("rbac.manage", "Manage roles and permissions", "rbac", "manage"),
    ("resource.grant", "Manage resource grants", "resource", "grant"),
    ("space.manage", "Manage knowledge spaces", "space", "manage"),
    ("category.manage", "Manage knowledge categories", "category", "manage"),
    ("tag.manage", "Manage knowledge tags", "tag", "manage"),
    ("document.view", "View documents", "document", "view"),
    ("document.create", "Create documents", "document", "create"),
    ("document.edit", "Edit documents", "document", "edit"),
    ("document.delete", "Delete documents", "document", "delete"),
    ("document.review", "Review and publish documents", "document", "review"),
    ("document.download", "Download document files", "document", "download"),
    ("file.manage", "Upload and remove document files", "file", "manage"),
]


async def seed() -> None:
    async with SessionLocal() as db:
        permissions: list[Permission] = []
        for code, name, resource_type, action in DEFAULT_PERMISSIONS:
            permission = await db.scalar(select(Permission).where(Permission.code == code))
            if not permission:
                permission = Permission(
                    code=code, name=name, resource_type=resource_type, action=action
                )
                db.add(permission)
            permissions.append(permission)
        await db.flush()

        result = await db.execute(
            select(Role).where(Role.code == "super_admin").options(selectinload(Role.permissions))
        )
        role = result.scalar_one_or_none()
        if not role:
            role = Role(
                code="super_admin",
                name="Super Administrator",
                description="Built-in platform administrator",
                is_system=True,
                permissions=permissions,
            )
            db.add(role)
        else:
            role.permissions = permissions

        user = await db.scalar(
            select(User).where(User.username == settings.first_superuser_username)
        )
        if not user:
            user = User(
                username=settings.first_superuser_username,
                email=str(settings.first_superuser_email),
                display_name="System Administrator",
                password_hash=hash_password(settings.first_superuser_password),
                is_superuser=True,
                roles=[role],
            )
            db.add(user)
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
