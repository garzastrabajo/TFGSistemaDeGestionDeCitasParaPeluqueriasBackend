from __future__ import annotations
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict
from sqlmodel import SQLModel, Field as SQLField


class Product(BaseModel):
    id: int
    categoryId: int
    name: str
    brand: Optional[str] = None
    description: Optional[str] = None

    # Campos de precio (legacy y nuevo)
    price: Optional[Decimal] = Field(default=None)
    displayedPrice: Optional[Decimal] = Field(default=None)

    stock: Optional[int] = None  # Campo legacy que estaba en tu dict
    imageUrl: Optional[str] = None
    isActive: bool = True

    # Permitimos poblar por nombre o alias
    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="before")
    def unify_prices(cls, values):
        # Si sólo viene 'price', copiamos a displayedPrice
        if values.get("price") is not None and values.get("displayedPrice") is None:
            values["displayedPrice"] = values["price"]
        # Si sólo viene 'displayedPrice', copiamos a price
        if values.get("displayedPrice") is not None and values.get("price") is None:
            values["price"] = values["displayedPrice"]
        return values

    def model_dump(self, *args, **kwargs):
        """
        Sobrescribimos para garantizar que ambas claves aparecen en la respuesta,
        manteniendo compatibilidad con frontends que esperan 'price' mientras
        el dominio nuevo usa 'displayedPrice'.
        """
        data = super().model_dump(*args, **kwargs)
        # Asegurar sincronización final
        if data.get("price") is None and data.get("displayedPrice") is not None:
            data["price"] = data["displayedPrice"]
        if data.get("displayedPrice") is None and data.get("price") is not None:
            data["displayedPrice"] = data["price"]
        return data


class InventoryItem(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    description: Optional[str] = None
    price: Decimal
    stock: int
    imageUrl: Optional[str] = None


class InventoryRecord(BaseModel):
    barbershopId: int
    productId: int
    stock: int
    isVisible: bool = True
    order: int


class ProductTable(SQLModel, table=True):
    __tablename__ = "products"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    categoryId: int = SQLField(foreign_key="product_categories.id")
    name: str
    brand: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    displayedPrice: Optional[Decimal] = None
    stock: Optional[int] = None
    imageUrl: Optional[str] = None
    isActive: bool = True


__all__ = ["Product", "InventoryItem", "InventoryRecord", "ProductTable"]