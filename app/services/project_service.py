from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.db.models.models import Project, ProjectPlace
from app.db.schemas.schemas import ProjectCreate, ProjectUpdate, PlaceCreate, PlaceUpdate
from app.services.artic_service import fetch_artwork
from config import MAX_PLACES_PER_PROJECT


async def get_project_or_404(db: AsyncSession, project_id: int) -> Project:
    """Fetch a project (with places eagerly loaded) by ID or raise 404."""
    result = await db.execute(
        select(Project)
        .where(Project.row_id == project_id)
        .options(selectinload(Project.places))  # Avoid lazy-load in async context
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
    return project


async def list_projects(
    db: AsyncSession,
    is_completed: bool | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Return a filtered, paginated list of projects with place count metadata."""
    count_query = select(func.count()).select_from(Project)
    select_query = select(Project).options(selectinload(Project.places)).order_by(Project.created_at.desc())

    if is_completed is not None:
        count_query = count_query.where(Project.is_completed == is_completed)
        select_query = select_query.where(Project.is_completed == is_completed)

    if search:
        search_term = f"%{search}%"
        count_query = count_query.where(Project.name.ilike(search_term))
        select_query = select_query.where(Project.name.ilike(search_term))

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(select_query.limit(limit).offset(offset))
    return {
        "data": result.scalars().all(),
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
    """
    Create a new project, optionally pre-populating it with places.
    Each place ID is validated against the Art Institute of Chicago API.
    """
    if len(data.places) > MAX_PLACES_PER_PROJECT:
        raise HTTPException(
            status_code=422,
            detail=f"A project can have at most {MAX_PLACES_PER_PROJECT} places.",
        )

    # Detect duplicate external IDs within the same request
    external_ids = [p.external_id for p in data.places]
    if len(external_ids) != len(set(external_ids)):
        raise HTTPException(status_code=422, detail="Duplicate place IDs in the request.")

    project = Project(
        name=data.name,
        description=data.description,
        start_date=data.start_date,
    )
    db.add(project)
    await db.flush()  # Obtain project.row_id before inserting places

    for place_data in data.places:
        artwork = await fetch_artwork(place_data.external_id)
        db.add(ProjectPlace(project_id=project.row_id, **artwork))

    await db.commit()

    # Re-fetch with relationships loaded so the response serialises correctly
    return await get_project_or_404(db, project.row_id)


async def update_project(db: AsyncSession, project_id: int, data: ProjectUpdate) -> Project:
    """Update mutable project fields (name, description, start_date)."""
    project = await get_project_or_404(db, project_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    await db.commit()
    return await get_project_or_404(db, project_id)


async def delete_project(db: AsyncSession, project_id: int) -> None:
    """
    Delete a project.
    Raises 409 if any of its places have already been marked as visited.
    """
    project = await get_project_or_404(db, project_id)

    visited = [p for p in project.places if p.is_visited]
    if visited:
        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot delete a project that has visited places. "
                f"{len(visited)} place(s) are already marked as visited."
            ),
        )

    await db.delete(project)
    await db.commit()


async def get_place_or_404(db: AsyncSession, project_id: int, place_id: int) -> ProjectPlace:
    """Fetch a project place by ID, ensuring it belongs to the given project."""
    result = await db.execute(
        select(ProjectPlace).where(
            ProjectPlace.row_id == place_id,
            ProjectPlace.project_id == project_id,
        )
    )
    place = result.scalar_one_or_none()
    if not place:
        raise HTTPException(
            status_code=404,
            detail=f"Place {place_id} not found in project {project_id}.",
        )
    return place


async def list_places(
    db: AsyncSession,
    project_id: int,
    is_visited: bool | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """List places for a project with optional visited filter and pagination."""
    await get_project_or_404(db, project_id)  # Ensure the project exists

    base_filter = [ProjectPlace.project_id == project_id]
    if is_visited is not None:
        base_filter.append(ProjectPlace.is_visited == is_visited)

    select_query = (
        select(ProjectPlace)
        .where(*base_filter)
        .order_by(ProjectPlace.created_at.asc())
    )
    count_query = select(func.count()).select_from(ProjectPlace).where(*base_filter)

    if search:
        search_term = f"%{search}%"
        search_filter = or_(
            ProjectPlace.title.ilike(search_term),
            ProjectPlace.artist.ilike(search_term),
            ProjectPlace.place_of_origin.ilike(search_term),
        )
        select_query = select_query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(select_query.limit(limit).offset(offset))
    return {
        "data": result.scalars().all(),
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def add_place_to_project(
    db: AsyncSession, project_id: int, data: PlaceCreate
) -> ProjectPlace:
    """
    Add a new place to an existing project.
    Validates the place in the Art Institute API before storing.
    """
    project = await get_project_or_404(db, project_id)

    if len(project.places) >= MAX_PLACES_PER_PROJECT:
        raise HTTPException(
            status_code=422,
            detail=f"Project already has the maximum of {MAX_PLACES_PER_PROJECT} places.",
        )

    # Prevent duplicate artwork in the same project
    dup = await db.execute(
        select(ProjectPlace).where(
            ProjectPlace.project_id == project_id,
            ProjectPlace.external_id == data.external_id,
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Artwork {data.external_id} is already in this project.",
        )

    artwork = await fetch_artwork(data.external_id)
    place = ProjectPlace(project_id=project_id, **artwork)
    db.add(place)
    await db.commit()
    await db.refresh(place)
    return place


async def update_place(
    db: AsyncSession, project_id: int, place_id: int, data: PlaceUpdate
) -> ProjectPlace:
    """
    Update notes and/or visited status for a place.
    When all places in a project become visited the project is auto-completed.
    """
    place = await get_place_or_404(db, project_id, place_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(place, field, value)

    await db.flush()

    # Auto-complete the project when every place is visited
    project = await get_project_or_404(db, project_id)
    if project.places and all(p.is_visited for p in project.places):
        project.is_completed = True

    await db.commit()
    await db.refresh(place)
    return place