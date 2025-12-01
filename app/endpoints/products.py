from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.helpers.db_memory import DB
from app.models.product import Product as ProductModel
from app.models.product import ProductTable as ProductDB

router = APIRouter(prefix="/products", tags=["products"])


def _to_pydantic(p: ProductDB) -> ProductModel:
    return ProductModel(
        id=p.id,
        categoryId=p.categoryId,
        name=p.name,
        brand=p.brand,
        description=p.description,
        price=p.price,
        displayedPrice=p.displayedPrice,
        stock=p.stock,
        imageUrl=p.imageUrl,
        isActive=p.isActive,
    )


def _from_mem(x: dict) -> ProductModel:
    return ProductModel(
        id=x.get("id"),
        categoryId=x.get("categoryId"),
        name=x.get("name"),
        brand=x.get("brand"),
        description=x.get("description"),
        price=x.get("price"),
        displayedPrice=x.get("displayedPrice"),
        stock=x.get("stock"),
        imageUrl=x.get("imageUrl"),
        isActive=x.get("isActive", True),
    )


@router.get("", summary="Listado de productos", response_model=list[ProductModel])
def get_products(session: Session = Depends(get_session)):
    items_db = session.exec(select(ProductDB)).all()
    if items_db:
        return [_to_pydantic(x) for x in items_db]
    # Fallback a memoria
    return [_from_mem(x) for x in DB.get("products", [])]


@router.get("/by-category/{category_id}", summary="Productos por categoría", response_model=list[ProductModel])
def get_products_by_category(category_id: int, session: Session = Depends(get_session)):
    items_db = session.exec(select(ProductDB).where(ProductDB.categoryId == category_id)).all()
    if items_db:
        return [_to_pydantic(x) for x in items_db]
    # Fallback memoria
    items_mem = [p for p in DB.get("products", []) if p.get("categoryId") == category_id]
    return [_from_mem(x) for x in items_mem]


@router.get("/{product_id}", summary="Detalle de producto", response_model=ProductModel)
def get_product(product_id: int, session: Session = Depends(get_session)):
    p = session.get(ProductDB, product_id)
    if p:
        return _to_pydantic(p)
    # Fallback memoria
    m = next((x for x in DB.get("products", []) if x.get("id") == product_id), None)
    if not m:
        raise HTTPException(status_code=404, detail="No existe un producto con ese id")
    return _from_mem(m)


@router.post("", summary="Crear producto (solo SQL)", response_model=ProductModel, status_code=201)
def create_product(payload: ProductDB, session: Session = Depends(get_session)):
    payload.id = None
    session.add(payload)
    session.commit()
    session.refresh(payload)
    return _to_pydantic(payload)


@router.put("/{product_id}", summary="Actualizar producto (solo SQL)", response_model=ProductModel)
def update_product(product_id: int, payload: ProductDB, session: Session = Depends(get_session)):
    p = session.get(ProductDB, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="No existe un producto con ese id (SQL)")
    for field in [
        "categoryId",
        "name",
        "brand",
        "description",
        "price",
        "displayedPrice",
        "stock",
        "imageUrl",
        "isActive",
    ]:
        val = getattr(payload, field, None)
        if val is not None:
            setattr(p, field, val)
    session.add(p)
    session.commit()
    session.refresh(p)
    return _to_pydantic(p)


@router.delete("/{product_id}", summary="Eliminar producto (solo SQL)", status_code=204)
def delete_product(product_id: int, session: Session = Depends(get_session)):
    p = session.get(ProductDB, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="No existe un producto con ese id (SQL)")
    session.delete(p)
    session.commit()
    return None