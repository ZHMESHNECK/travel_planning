from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.schemas.schemas import PlaceCreate, PlaceResponse, PlaceUpdate
from app.services import project_service

router = APIRouter(prefix="/projects/{project_id}/places", tags=["Places"])


@router.get("/", response_model=list[PlaceResponse], summary="List all places in a project")
async def list_places(project_id: int, db: AsyncSession = Depends(get_db)):
    """Return all places associated with the given travel project."""
    return await project_service.list_places(db, project_id)


@router.post("/", response_model=PlaceResponse, status_code=201, summary="Add a place to a project")
async def add_place(project_id: int, data: PlaceCreate, db: AsyncSession = Depends(get_db)):
    """
    Add a new place (artwork) to an existing project.
    The artwork must exist in the Art Institute of Chicago API.
    A project may have at most 10 places; duplicate artworks are rejected.
    """
    return await project_service.add_place_to_project(db, project_id, data)


@router.get("/{place_id}", response_model=PlaceResponse, summary="Get a single place in a project")
async def get_place(project_id: int, place_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a single place from the given project."""
    return await project_service.get_place_or_404(db, project_id, place_id)


@router.patch("/{place_id}", response_model=PlaceResponse, summary="Update a place in a project")
async def update_place(
    project_id: int, place_id: int, data: PlaceUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Update notes or visited status for a place.
    When all places in the project are marked as visited,
    the project is automatically marked as completed.
    """
    return await project_service.update_place(db, project_id, place_id, data)