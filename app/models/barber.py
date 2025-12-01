from __future__ import annotations

from datetime import time
from enum import IntEnum
from typing import Optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON


class DayOfWeek(IntEnum):
    Sunday = 0
    Monday = 1
    Tuesday = 2
    Wednesday = 3
    Thursday = 4
    Friday = 5
    Saturday = 6


class Barber(BaseModel):
    id: int
    barbershopId: int
    name: str
    specialty: Optional[str] = None
    photoUrl: Optional[str] = None
    isActive: bool = True


class BarberSchedule(BaseModel):
    id: int
    barberId: int
    dayOfWeek: DayOfWeek
    openAt: Optional[time] = None
    closeAt: Optional[time] = None
    isClosed: bool = False

class BarberTable(SQLModel, table=True):
    __tablename__ = "barbers"
    id: Optional[int] = Field(default=None, primary_key=True)
    barbershopId: int = Field(foreign_key="barbershops.id")
    name: str
    specialty: Optional[str] = None
    photoUrl: Optional[str] = None
    isActive: bool = True
    # Compatibilidad para disponibilidad y filtros
    workingHours: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    servicesOffered: Optional[list[int]] = Field(default=None, sa_column=Column(JSON))


__all__ = ["Barber", "BarberSchedule", "DayOfWeek", "BarberTable"]