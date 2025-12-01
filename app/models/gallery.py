from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field


class GalleryItem(BaseModel):
    id: int
    barbershopId: int
    title: str
    description: Optional[str] = None
    imageUrl: str
    date: str
    isVisible: bool = True
    order: int
    serviceId: Optional[int] = None
    barberId: Optional[int] = None

class GalleryItemTable(SQLModel, table=True):
    __tablename__ = "gallery_items"
    id: Optional[int] = Field(default=None, primary_key=True)
    barbershopId: int = Field(foreign_key="barbershops.id")
    title: str
    description: Optional[str] = None
    imageUrl: str
    date: str
    isVisible: bool = True
    order: int
    serviceId: Optional[int] = Field(default=None, foreign_key="services.id")
    barberId: Optional[int] = Field(default=None, foreign_key="barbers.id")


__all__ = ["GalleryItem", "GalleryItemTable"]