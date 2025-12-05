from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField

# Modelos nuevos
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


# Modelos legacy
class ReviewLegacy(BaseModel):
    id: int
    barberId: Optional[int] = None
    serviceId: Optional[int] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    userName: Optional[str] = None
    createdAt: str  # ISO string
    userPhotoUrl: Optional[str] = None


class CreateReviewLegacy(BaseModel):
    barberId: Optional[int] = None
    serviceId: Optional[int] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    userName: Optional[str] = None
    userPhotoUrl: Optional[str] = None


# Alias para compatibilidad con endpoints actuales
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
    userPhotoUrl: Optional[str] = SQLField(default=None)
    userId: Optional[int] = SQLField(default=None, foreign_key="user.id")

__all__ = [
    "ReviewNew",
    "ServiceReview",
    "ReviewLegacy",
    "CreateReviewLegacy",
    "Review",
    "CreateReview",
    "ReviewTable",
]