from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.helpers.db_memory import DB
from app.models.category import ProductCategory as ProductCategoryModel
from app.models.category import ProductCategoryTable as ProductCategoryDB

router = APIRouter(prefix="/product-categories", tags=["product-categories"])


def _to_pydantic(c: ProductCategoryDB) -> ProductCategoryModel:
    return ProductCategoryModel(id=c.id, name=c.name, order=c.order)


def _from_mem(x: dict) -> ProductCategoryModel:
    return ProductCategoryModel(id=x.get("id"), name=x.get("name"), order=x.get("order", 0))


@router.get("", summary="Listado de categorías de productos", response_model=list[ProductCategoryModel])
def get_product_categories(session: Session = Depends(get_session)):
    items_db = session.exec(select(ProductCategoryDB)).all()
    if items_db:
        return [_to_pydantic(x) for x in sorted(items_db, key=lambda i: i.order)]
    cats = sorted(DB.get("productCategories", []), key=lambda c: c.get("order", 0))
    return [_from_mem(x) for x in cats]


@router.get("/{category_id}", summary="Detalle de categoría de productos", response_model=ProductCategoryModel)
def get_product_category(category_id: int, session: Session = Depends(get_session)):
    c = session.get(ProductCategoryDB, category_id)
    if c:
        return _to_pydantic(c)
    m = next((x for x in DB.get("productCategories", []) if x.get("id") == category_id), None)
    if not m:
        raise HTTPException(status_code=404, detail="No existe la categoría")
    return _from_mem(m)


@router.post("", summary="Crear categoría de productos (solo SQL)", response_model=ProductCategoryModel, status_code=201)
def create_product_category(payload: ProductCategoryDB, session: Session = Depends(get_session)):
    payload.id = None
    session.add(payload)
    session.commit()
    session.refresh(payload)
    return _to_pydantic(payload)


@router.put("/{category_id}", summary="Actualizar categoría de productos (solo SQL)", response_model=ProductCategoryModel)
def update_product_category(category_id: int, payload: ProductCategoryDB, session: Session = Depends(get_session)):
    c = session.get(ProductCategoryDB, category_id)
    if not c:
        raise HTTPException(status_code=404, detail="No existe la categoría (SQL)")
    for field in ["name", "order"]:
        val = getattr(payload, field, None)
        if val is not None:
            setattr(c, field, val)
    session.add(c)
    session.commit()
    session.refresh(c)
    return _to_pydantic(c)


@router.delete("/{category_id}", summary="Eliminar categoría de productos (solo SQL)", status_code=204)
def delete_product_category(category_id: int, session: Session = Depends(get_session)):
    c = session.get(ProductCategoryDB, category_id)
    if not c:
        raise HTTPException(status_code=404, detail="No existe la categoría (SQL)")
    session.delete(c)
    session.commit()
    return None