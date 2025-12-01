from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.helpers.db_memory import DB
from app.models.gallery import GalleryItem as GalleryModel
from app.models.gallery import GalleryItemTable as GalleryDB

router = APIRouter(prefix="/gallery", tags=["gallery"])


def _to_pydantic(g: GalleryDB) -> GalleryModel:
    return GalleryModel(
        id=g.id,
        barbershopId=g.barbershopId,
        title=g.title,
        description=g.description,
        imageUrl=g.imageUrl,
        date=g.date,
        isVisible=g.isVisible,
        order=g.order,
        serviceId=g.serviceId,
        barberId=g.barberId,
    )


def _from_mem(x: dict) -> GalleryModel:
    return GalleryModel(
        id=x.get("id"),
        barbershopId=x.get("barbershopId"),
        title=x.get("title"),
        description=x.get("description"),
        imageUrl=x.get("imageUrl"),
        date=x.get("date"),
        isVisible=x.get("isVisible", True),
        order=x.get("order", 0),
        serviceId=x.get("serviceId"),
        barberId=x.get("barberId"),
    )


@router.get("", summary="Listado de items de galería", response_model=list[GalleryModel])
def get_gallery(session: Session = Depends(get_session)):
    items_db = session.exec(select(GalleryDB)).all()
    if items_db:
        return [_to_pydantic(x) for x in sorted(items_db, key=lambda i: i.order)]
    items_mem = sorted(DB.get("gallery", []), key=lambda i: i.get("order", 0))
    return [_from_mem(x) for x in items_mem]


@router.get("/{item_id}", summary="Detalle de item de galería", response_model=GalleryModel)
def get_gallery_item(item_id: int, session: Session = Depends(get_session)):
    g = session.get(GalleryDB, item_id)
    if g:
        return _to_pydantic(g)
    m = next((x for x in DB.get("gallery", []) if x.get("id") == item_id), None)
    if not m:
        raise HTTPException(status_code=404, detail="No existe el item")
    return _from_mem(m)


@router.post("", summary="Crear item de galería (solo SQL)", response_model=GalleryModel, status_code=201)
def create_gallery_item(payload: GalleryDB, session: Session = Depends(get_session)):
    payload.id = None
    session.add(payload)
    session.commit()
    session.refresh(payload)
    return _to_pydantic(payload)


@router.put("/{item_id}", summary="Actualizar item de galería (solo SQL)", response_model=GalleryModel)
def update_gallery_item(item_id: int, payload: GalleryDB, session: Session = Depends(get_session)):
    g = session.get(GalleryDB, item_id)
    if not g:
        raise HTTPException(status_code=404, detail="No existe el item (SQL)")
    for field in [
        "barbershopId", "title", "description", "imageUrl", "date",
        "isVisible", "order", "serviceId", "barberId",
    ]:
        val = getattr(payload, field, None)
        if val is not None:
            setattr(g, field, val)
    session.add(g)
    session.commit()
    session.refresh(g)
    return _to_pydantic(g)


@router.delete("/{item_id}", summary="Eliminar item de galería (solo SQL)", status_code=204)
def delete_gallery_item(item_id: int, session: Session = Depends(get_session)):
    g = session.get(GalleryDB, item_id)
    if not g:
        raise HTTPException(status_code=404, detail="No existe el item (SQL)")
    session.delete(g)
    session.commit()
    return None