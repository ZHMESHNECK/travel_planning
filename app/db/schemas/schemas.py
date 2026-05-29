from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    total: int
    limit: int
    offset: int


class PlaceBase(BaseModel):
    external_id: int = Field(..., description="Artwork ID from the Art Institute of Chicago API")


class PlaceCreate(PlaceBase):
    pass


class PlaceUpdate(BaseModel):
    notes: str | None = Field(None, description="Traveller notes for this place")
    is_visited: bool | None = Field(None, description="Mark place as visited")


class PlaceResponse(BaseModel):
    row_id: int
    project_id: int
    external_id: int
    title: str
    artist: str | None
    place_of_origin: str | None
    image_url: str | None
    notes: str | None
    is_visited: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: str | None = Field(None, description="Optional project description")
    start_date: date | None = Field(None, description="Optional trip start date")
    places: list[PlaceCreate] = Field(
        default_factory=list,
        max_length=10,
        description="Optional list of place IDs to add at creation (max 10)",
    )


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    start_date: date | None = None


class ProjectResponse(BaseModel):
    row_id: int
    name: str
    description: str | None
    start_date: date | None
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    places: list[PlaceResponse] = []

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    row_id: int
    name: str
    description: str | None
    start_date: date | None
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    places_count: int = 0
    visited_count: int = 0

    model_config = {"from_attributes": True}