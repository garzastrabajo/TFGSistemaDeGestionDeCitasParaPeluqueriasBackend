from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField

# ---------- Nuevo (alineado con C#) ----------
# Si en el futuro migras tu DB a este shape, usa ReviewNew en los endpoints.
class ReviewNew(BaseModel):
    id: int
    userId: int
    appointmentId: int
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ServiceReview(BaseModel):
    id: int
    userId: int
    appointmentId: int
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------- Legacy (shape actual de tu DB) ----------
class ReviewLegacy(BaseModel):
    id: int
    barberId: Optional[int] = None
    serviceId: Optional[int] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    userName: Optional[str] = None
    createdAt: str  # ISO string
    userPhotoUrl: Optional[str] = None  # NUEVO


class CreateReviewLegacy(BaseModel):
    barberId: Optional[int] = None
    serviceId: Optional[int] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    userName: Optional[str] = None
    userPhotoUrl: Optional[str] = None  # NUEVO


# ---------- Aliases para mantener endpoints existentes ----------
# Tus endpoints hacen: from app.models.review import Review, CreateReview
# Esto los hace apuntar al modelo legacy actual.
Review = ReviewLegacy
CreateReview = CreateReviewLegacy


class ReviewTable(SQLModel, table=True):
    __tablename__ = "reviews"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    barberId: Optional[int] = SQLField(default=None, foreign_key="barbers.id")
    serviceId: Optional[int] = SQLField(default=None, foreign_key="services.id")
    rating: int
    comment: Optional[str] = SQLField(default=None)
    userName: Optional[str] = SQLField(default=None)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    userPhotoUrl: Optional[str] = SQLField(default=None)  # NUEVO
    userId: Optional[int] = SQLField(default=None, foreign_key="user.id")  # NUEVO

__all__ = [
    # Nuevo
    "ReviewNew",
    "ServiceReview",
    # Legacy + aliases
    "ReviewLegacy",
    "CreateReviewLegacy",
    "Review",
    "CreateReview",
    "ReviewTable",
]