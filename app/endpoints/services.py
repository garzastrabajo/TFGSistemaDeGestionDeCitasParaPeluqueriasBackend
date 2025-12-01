from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.helpers.db_memory import DB
from app.models.service import Service as ServiceModel
from app.models.service import ServiceTable as ServiceDB

router = APIRouter(prefix="/services", tags=["services"])


def _to_pydantic(s: ServiceDB) -> ServiceModel:
    return ServiceModel(
        id=s.id,
        barbershopId=s.barbershopId,
        categoryId=s.categoryId,
        name=s.name,
        description=s.description,
        price=s.price,
        durationMinutes=s.durationMinutes,
        isActive=s.isActive,
    )


def _from_mem(x: dict) -> ServiceModel:
    return ServiceModel(
        id=x.get("id"),
        barbershopId=x.get("barbershopId"),
        categoryId=x.get("categoryId"),
        name=x.get("name"),
        description=x.get("description"),
        price=x.get("price"),
        durationMinutes=x.get("durationMinutes"),
        isActive=x.get("isActive", True),
    )


@router.get("", summary="Listado de servicios", response_model=list[ServiceModel])
def get_services(session: Session = Depends(get_session)):
    items_db = session.exec(select(ServiceDB)).all()
    if items_db:
        return [_to_pydantic(x) for x in items_db]
    return [_from_mem(x) for x in DB.get("services", [])]


@router.get("/by-category/{category_id}", summary="Servicios por categoría", response_model=list[ServiceModel])
def get_services_by_category(category_id: int, session: Session = Depends(get_session)):
    items_db = session.exec(select(ServiceDB).where(ServiceDB.categoryId == category_id)).all()
    if items_db:
        return [_to_pydantic(x) for x in items_db]
    items_mem = [s for s in DB.get("services", []) if s.get("categoryId") == category_id]
    return [_from_mem(x) for x in items_mem]


@router.get("/{service_id}", summary="Detalle de servicio", response_model=ServiceModel)
def get_service(service_id: int, session: Session = Depends(get_session)):
    s = session.get(ServiceDB, service_id)
    if s:
        return _to_pydantic(s)
    m = next((x for x in DB.get("services", []) if x.get("id") == service_id), None)
    if not m:
        raise HTTPException(status_code=404, detail="No existe un servicio con ese id")
    return _from_mem(m)


@router.post("", summary="Crear servicio (solo SQL)", response_model=ServiceModel, status_code=201)
def create_service(payload: ServiceDB, session: Session = Depends(get_session)):
    payload.id = None
    session.add(payload)
    session.commit()
    session.refresh(payload)
    return _to_pydantic(payload)


@router.put("/{service_id}", summary="Actualizar servicio (solo SQL)", response_model=ServiceModel)
def update_service(service_id: int, payload: ServiceDB, session: Session = Depends(get_session)):
    s = session.get(ServiceDB, service_id)
    if not s:
        raise HTTPException(status_code=404, detail="No existe un servicio con ese id (SQL)")
    for field in ["barbershopId", "categoryId", "name", "description", "price", "durationMinutes", "isActive"]:
        val = getattr(payload, field, None)
        if val is not None:
            setattr(s, field, val)
    session.add(s)
    session.commit()
    session.refresh(s)
    return _to_pydantic(s)


@router.delete("/{service_id}", summary="Eliminar servicio (solo SQL)", status_code=204)
def delete_service(service_id: int, session: Session = Depends(get_session)):
    s = session.get(ServiceDB, service_id)
    if not s:
        raise HTTPException(status_code=404, detail="No existe un servicio con ese id (SQL)")
    session.delete(s)
    session.commit()
    return None