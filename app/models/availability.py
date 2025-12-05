from __future__ import annotations
from typing import List
from pydantic import BaseModel

# Respuesta de disponibilidad
class AvailabilityResponse(BaseModel):
    barberId: int
    date: str
    timezone: str
    slotMinutes: int
    available: List[str]