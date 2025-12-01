from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from sqlmodel import SQLModel, Field


class ProductCategory(BaseModel):
    id: int
    name: str
    order: int


class ServiceCategory(BaseModel):
    id: int
    name: str
    order: int

class ProductCategoryTable(SQLModel, table=True):
    __tablename__ = "product_categories"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    order: int


class ServiceCategoryTable(SQLModel, table=True):
    __tablename__ = "service_categories"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    order: int


__all__ = [
    "ProductCategory",
    "ServiceCategory",
    "ProductCategoryTable",
    "ServiceCategoryTable",
]