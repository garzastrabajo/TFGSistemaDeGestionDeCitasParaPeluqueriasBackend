from __future__ import annotations
from typing import List
from pydantic import BaseModel

# Modelo sin equivalente directo en C# (lo conservamos).
class AvailabilityResponse(BaseModel):
    barberId: int
    date: str
    timezone: str
    slotMinutes: int
    available: List[str]