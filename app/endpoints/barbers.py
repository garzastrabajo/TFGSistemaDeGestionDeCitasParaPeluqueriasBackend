from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models.barber import BarberTable as BarberDB
from app.models.barber import Barber
from app.helpers.db_memory import DB  # <-- añadido

router = APIRouter(prefix="/barbers", tags=["barbers"])


def _to_pydantic(b: BarberDB) -> Barber:
    return Barber(
        id=b.id,
        barbershopId=b.barbershopId,
        name=b.name,
        specialty=b.specialty,
        photoUrl=b.photoUrl,
        isActive=b.isActive,
    )


def _from_mem(x: dict) -> Barber:
    return Barber(
        id=x.get("id"),
        barbershopId=x.get("barbershopId"),
        name=x.get("name"),
        specialty=x.get("specialty"),
        photoUrl=x.get("photoUrl"),
        isActive=x.get("isActive", True),
    )


@router.get("", summary="Listado de barberos", response_model=list[Barber])
def get_barbers(session: Session = Depends(get_session)):
    items_db = session.exec(select(BarberDB)).all()
    if items_db:                 # Si hay datos en la tabla, usar DB SQL
        return [_to_pydantic(x) for x in items_db]
    # Fallback a memoria
    return [_from_mem(x) for x in DB.get("barbers", [])]


@router.get("/{barber_id}", summary="Detalle de un barbero", response_model=Barber)
def get_barber(barber_id: int, session: Session = Depends(get_session)):
    b = session.get(BarberDB, barber_id)
    if b:
        return _to_pydantic(b)
    # Fallback memoria
    m = next((x for x in DB.get("barbers", []) if x.get("id") == barber_id), None)
    if not m:
        raise HTTPException(status_code=404, detail="No existe un barbero con ese id")
    return _from_mem(m)


@router.get("/by-service/{service_id}", summary="Barberos que ofrecen un servicio", response_model=list[Barber])
def get_barbers_by_service(service_id: int, session: Session = Depends(get_session)):
    items_db = session.exec(select(BarberDB)).all()
    if items_db:
        filtered = [b for b in items_db if b.isActive and (b.servicesOffered and int(service_id) in b.servicesOffered)]
        return [_to_pydantic(b) for b in filtered]
    # Fallback memoria
    items_mem = DB.get("barbers", [])
    filtered_mem = [
        x for x in items_mem
        if x.get("isActive", True) and int(service_id) in (x.get("servicesOffered") or [])
    ]
    return [_from_mem(x) for x in filtered_mem]


@router.post("", summary="Crear barbero (solo SQL)", response_model=Barber, status_code=201)
def create_barber(payload: BarberDB, session: Session = Depends(get_session)):
    payload.id = None
    session.add(payload)
    session.commit()
    session.refresh(payload)
    return _to_pydantic(payload)


@router.put("/{barber_id}", summary="Actualizar barbero (solo SQL)", response_model=Barber)
def update_barber(barber_id: int, payload: BarberDB, session: Session = Depends(get_session)):
    b = session.get(BarberDB, barber_id)
    if not b:
        raise HTTPException(status_code=404, detail="No existe un barbero con ese id (SQL)")
    for field in ["barbershopId", "name", "specialty", "photoUrl", "isActive", "workingHours", "servicesOffered"]:
        val = getattr(payload, field, None)
        if val is not None:
            setattr(b, field, val)
    session.add(b)
    session.commit()
    session.refresh(b)
    return _to_pydantic(b)


@router.delete("/{barber_id}", summary="Eliminar barbero (solo SQL)", status_code=204)
def delete_barber(barber_id: int, session: Session = Depends(get_session)):
    b = session.get(BarberDB, barber_id)
    if not b:
        raise HTTPException(status_code=404, detail="No existe un barbero con ese id (SQL)")
    session.delete(b)
    session.commit()
    return None