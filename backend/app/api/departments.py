from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import func, select

from app.api.dependencies import DB, require_permission
from app.common.exceptions import AppError
from app.models import Department
from app.schemas import DepartmentCreate, DepartmentRead, DepartmentUpdate

router = APIRouter(
    prefix="/departments",
    tags=["Departments"],
    dependencies=[Depends(require_permission("department.manage"))],
)


def build_tree(rows: list[Department]) -> list[DepartmentRead]:
    nodes = {
        row.id: DepartmentRead(
            id=row.id,
            parent_id=row.parent_id,
            name=row.name,
            sort=row.sort,
            is_active=row.is_active,
            children=[],
        )
        for row in rows
    }
    roots: list[DepartmentRead] = []
    for row in rows:
        node = nodes[row.id]
        if row.parent_id and row.parent_id in nodes:
            nodes[row.parent_id].children.append(node)
        else:
            roots.append(node)

    def sort_nodes(items: list[DepartmentRead]) -> None:
        items.sort(key=lambda item: (item.sort, item.id))
        for item in items:
            sort_nodes(item.children)

    sort_nodes(roots)
    return roots


async def ensure_parent(db: DB, parent_id: int | None) -> None:
    if parent_id is not None and not await db.get(Department, parent_id):
        raise AppError("parent_not_found", "Parent department does not exist", 404)


async def is_descendant(db: DB, department_id: int, candidate_parent_id: int) -> bool:
    current = await db.get(Department, candidate_parent_id)
    while current:
        if current.id == department_id:
            return True
        current = await db.get(Department, current.parent_id) if current.parent_id else None
    return False


@router.get("", response_model=list[DepartmentRead])
async def list_departments(db: DB) -> list[DepartmentRead]:
    result = await db.execute(select(Department).order_by(Department.sort, Department.id))
    return build_tree(list(result.scalars()))


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
async def create_department(payload: DepartmentCreate, db: DB) -> Department:
    await ensure_parent(db, payload.parent_id)
    department = Department(**payload.model_dump())
    db.add(department)
    await db.commit()
    await db.refresh(department)
    return department


@router.patch("/{department_id}", response_model=DepartmentRead)
async def update_department(
    department_id: int, payload: DepartmentUpdate, db: DB
) -> Department:
    department = await db.get(Department, department_id)
    if not department:
        raise AppError("department_not_found", "Department does not exist", 404)
    values = payload.model_dump(exclude_unset=True)
    if "parent_id" in values:
        parent_id = values["parent_id"]
        await ensure_parent(db, parent_id)
        if parent_id == department_id or (
            parent_id is not None and await is_descendant(db, department_id, parent_id)
        ):
            raise AppError("department_cycle", "Department hierarchy cannot contain a cycle")
    for key, value in values.items():
        setattr(department, key, value)
    await db.commit()
    await db.refresh(department)
    return department


@router.delete("/{department_id}", status_code=204)
async def delete_department(department_id: int, db: DB) -> Response:
    department = await db.get(Department, department_id)
    if not department:
        raise AppError("department_not_found", "Department does not exist", 404)
    child_count = await db.scalar(
        select(func.count()).select_from(Department).where(Department.parent_id == department_id)
    )
    if child_count:
        raise AppError("department_not_empty", "Move or delete child departments first", 409)
    await db.delete(department)
    await db.commit()
    return Response(status_code=204)

