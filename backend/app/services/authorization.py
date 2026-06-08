from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GrantEffect, ResourceGrant, User


async def can_access_resource(
    db: AsyncSession,
    user: User,
    resource_type: str,
    resource_id: str,
    action: str,
) -> bool:
    if user.is_superuser:
        return True

    role_ids = [role.id for role in user.roles]
    subject_predicates = [
        (ResourceGrant.subject_type == "user") & (ResourceGrant.subject_id == user.id)
    ]
    if user.department_id:
        subject_predicates.append(
            (ResourceGrant.subject_type == "department")
            & (ResourceGrant.subject_id == user.department_id)
        )
    if role_ids:
        subject_predicates.append(
            (ResourceGrant.subject_type == "role") & ResourceGrant.subject_id.in_(role_ids)
        )

    result = await db.execute(
        select(ResourceGrant).where(
            or_(*subject_predicates),
            ResourceGrant.resource_type == resource_type,
            ResourceGrant.resource_id.in_([resource_id, "*"]),
            ResourceGrant.action.in_([action, "*"]),
        )
    )
    grants = result.scalars().all()
    if any(grant.effect == GrantEffect.DENY for grant in grants):
        return False
    return any(grant.effect == GrantEffect.ALLOW for grant in grants)
