from __future__ import annotations
from datetime import time
from typing import List, Optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON

from .barber import DayOfWeek


class SocialLinks(BaseModel):
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    web: Optional[str] = None
    tiktok: Optional[str] = None


class DayHours(BaseModel):
    open: str = ""   # "09:00"
    close: str = ""  # "20:00"


class OpeningHours(BaseModel):
    monday: Optional[DayHours] = None
    tuesday: Optional[DayHours] = None
    wednesday: Optional[DayHours] = None
    thursday: Optional[DayHours] = None
    friday: Optional[DayHours] = None
    saturday: Optional[DayHours] = None
    sunday: Optional[DayHours] = None


class Barbershop(BaseModel):
    id: int
    name: str
    phone: str
    email: str
    address: str
    city: str
    country: str
    latitude: float
    longitude: float
    isActive: bool = True

    timezone: str = "Europe/Madrid"
    images: List[str] = []
    about: Optional[str] = None
    social: Optional[SocialLinks] = None
    openingHours: Optional[OpeningHours] = None


class BarbershopSchedule(BaseModel):
    id: int
    barbershopId: int
    dayOfWeek: DayOfWeek
    openAt: time
    closeAt: time
    isClosed: bool = False

class BarbershopTable(SQLModel, table=True):
    __tablename__ = "barbershops"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    phone: str
    email: str
    address: str
    city: str
    country: str
    latitude: float
    longitude: float
    isActive: bool = True
    timezone: str = "Europe/Madrid"
    images: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    about: Optional[str] = None
    social: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    openingHours: Optional[dict] = Field(default=None, sa_column=Column(JSON))


__all__ = [
    "Barbershop",
    "BarbershopSchedule",
    "SocialLinks",
    "OpeningHours",
    "DayHours",
    "BarbershopTable",
]