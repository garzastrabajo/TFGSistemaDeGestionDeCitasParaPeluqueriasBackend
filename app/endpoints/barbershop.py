from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.helpers.db_memory import DB
from app.models.barbershop import Barbershop, BarbershopTable as BarbershopDB

router = APIRouter(prefix="/barbershop", tags=["barbershop"])


def _to_pydantic(b: BarbershopDB) -> Barbershop:
    return Barbershop(
        id=b.id,
        name=b.name,
        phone=b.phone,
        email=b.email,
        address=b.address,
        city=b.city,
        country=b.country,
        latitude=b.latitude,
        longitude=b.longitude,
        isActive=b.isActive,
        timezone=b.timezone,
        images=b.images or [],
        about=b.about,
        social=b.social,
        openingHours=b.openingHours,
    )


@router.get("", summary="Información de la barbería", response_model=Barbershop)
def get_barbershop(session: Session = Depends(get_session)):
    row = session.exec(select(BarbershopDB)).first()
    if row:
        return _to_pydantic(row)
    # Fallback a memoria
    return Barbershop(**DB["barbershop"])


@router.post("", summary="Actualizar datos de la barbería (POST upsert, solo SQL)", response_model=Barbershop)
def upsert_barbershop(payload: BarbershopDB, session: Session = Depends(get_session)):
    """
    Si existe, actualiza el registro único de barbershop. Si no existe, lo crea.
    """
    row = session.exec(select(BarbershopDB)).first()
    fields = [
        "name", "phone", "email", "address", "city", "country",
        "latitude", "longitude", "isActive", "timezone",
        "images", "about", "social", "openingHours",
    ]

    if row:
        for f in fields:
            setattr(row, f, getattr(payload, f))
        session.add(row)
        session.commit()
        session.refresh(row)
        return _to_pydantic(row)

    # Crear si no existía
    payload.id = None
    session.add(payload)
    session.commit()
    session.refresh(payload)
    return _to_pydantic(payload)