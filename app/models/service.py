from __future__ import annotations
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field


class ServiceOffering(BaseModel):
    id: int
    barbershopId: int
    categoryId: int
    name: str
    description: Optional[str] = None
    price: Decimal
    durationMinutes: int
    isActive: bool = True


# Alias retrocompatible (endpoints que siguen usando Service)
Service = ServiceOffering

class ServiceTable(SQLModel, table=True):
    __tablename__ = "services"
    id: Optional[int] = Field(default=None, primary_key=True)
    barbershopId: int = Field(foreign_key="barbershops.id")
    categoryId: int = Field(foreign_key="service_categories.id")
    name: str
    description: Optional[str] = None
    price: Decimal
    durationMinutes: int
    isActive: bool = True


__all__ = ["ServiceOffering", "Service", "ServiceTable"]