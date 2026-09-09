"""Core domain entities for GAIA OS v0.1."""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utc_now_iso() -> str:
    """Returns the current UTC time as an ISO 8601 formatted string."""
    return datetime.now(UTC).isoformat()


def _new_id() -> str:
    """Generates a UUIDv4 string."""
    return str(uuid.uuid4())


class DomainBase(BaseModel):
    """Base model with shared configuration and timestamp handling."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    id: str = Field(default_factory=_new_id)
    created_at: str = Field(default_factory=_utc_now_iso)
    updated_at: str = Field(default_factory=_utc_now_iso)


class Project(DomainBase):
    """Represents an active or archived project in GAIA."""

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    status: str = Field(default="active", pattern="^(active|archived|paused|completed)$")

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Project name cannot be empty or whitespace.")
        return v.strip()


class Task(DomainBase):
    """Represents a tangible work item or action item."""

    project_id: str | None = None
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=5000)
    status: str = Field(default="todo", pattern="^(todo|in_progress|done|cancelled)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Task title cannot be empty or whitespace.")
        return v.strip()


class Idea(DomainBase):
    """Represents a raw thought, concept, or potential direction."""

    project_id: str | None = None
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=5000)
    tags: list[str] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Idea title cannot be empty or whitespace.")
        return v.strip()


class Note(DomainBase):
    """Represents persistent written knowledge or documentation."""

    project_id: str | None = None
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Note title cannot be empty or whitespace.")
        return v.strip()


class Decision(DomainBase):
    """Represents an architectural, product, or personal decision."""

    project_id: str | None = None
    title: str = Field(min_length=1, max_length=300)
    rationale: str = Field(min_length=1)
    status: str = Field(default="proposed", pattern="^(proposed|accepted|superseded|rejected)$")
