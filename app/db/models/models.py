from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.engine import Base


class Project(Base):
    """Travel project that groups multiple places a traveller wants to visit."""

    __tablename__ = "projects"

    row_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False
    )

    places: Mapped[list["ProjectPlace"]] = relationship(
        "ProjectPlace", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectPlace(Base):
    """A place (artwork from Art Institute of Chicago) attached to a travel project."""

    __tablename__ = "project_places"

    row_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.row_id"), nullable=False)

    # External identifier from the Art Institute of Chicago API
    external_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Artwork metadata cached from the external API
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    artist: Mapped[str | None] = mapped_column(String(512), nullable=True)
    place_of_origin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_visited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False
    )

    # Each artwork can appear only once per project
    __table_args__ = (
        UniqueConstraint("project_id", "external_id", name="uq_project_external_id"),
    )

    project: Mapped["Project"] = relationship("Project", back_populates="places")