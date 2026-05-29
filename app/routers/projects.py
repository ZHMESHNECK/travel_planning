from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.schemas.schemas import ProjectCreate, ProjectListResponse, ProjectResponse, ProjectUpdate
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=list[ProjectListResponse], summary="List all travel projects")
async def list_projects(db: AsyncSession = Depends(get_db)):
    """Return all travel projects with aggregated place counts."""
    projects = await project_service.list_projects(db)
    return [
        ProjectListResponse(
            **{col: getattr(p, col) for col in [
                "id", "name", "description", "start_date",
                "is_completed", "created_at", "updated_at",
            ]},
            places_count=len(p.places),
            visited_count=sum(1 for pl in p.places if pl.is_visited),
        )
        for p in projects
    ]


@router.post("/", response_model=ProjectResponse, status_code=201, summary="Create a travel project")
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a travel project. Optionally include an array of place IDs (artworks)
    to add to the project at creation time. Each place is validated against the
    Art Institute of Chicago API.
    """
    return await project_service.create_project(db, data)


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get a single travel project")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a single project with all its associated places."""
    return await project_service.get_project_or_404(db, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse, summary="Update a travel project")
async def update_project(project_id: int, data: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    """Update project name, description, or start date."""
    return await project_service.update_project(db, project_id, data)


@router.delete("/{project_id}", status_code=204, summary="Delete a travel project")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a project. Returns 409 if any of the project's places
    have already been marked as visited.
    """
    await project_service.delete_project(db, project_id)