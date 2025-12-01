from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional

from app.helpers.db_memory import DB
from app.helpers.scheduling import parse_hhmm, daterange_times, get_weekly_hours, is_slot_booked
from app.models.availability import AvailabilityResponse
from sqlmodel import Session, select, col
from app.db import get_session
from app.models.booking import BookingTable as BookingDB
from app.models.service import ServiceTable as ServiceDB
from app.models.barber import BarberTable as BarberDB

# Estados a ignorar en disponibilidad
CANCELLED_STATES = {"cancelled", "canceled"}

router = APIRouter(prefix="/availability", tags=["availability"])


class AvailabilityRequest(BaseModel):
    barberId: int
    dateStr: str
    slotMinutes: int = Field(default=30, ge=5, le=60)
    serviceId: Optional[int] = None


def _compute_availability(barber_id: int, date_str: str, slot_minutes: int, service_id: Optional[int], session: Session) -> AvailabilityResponse:
    # Buscar primero en SQL; si no existe, caer a memoria para compatibilidad
    b_sql = session.get(BarberDB, barber_id)
    if b_sql:
        barber = {
            "id": b_sql.id,
            "workingHours": b_sql.workingHours or {},
        }
    else:
        barber = next((x for x in DB.get("barbers", []) if x.get("id") == barber_id), None)
        if not barber:
            raise HTTPException(status_code=404, detail="No existe un barbero con ese id")

    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD")

    wh = get_weekly_hours(barber, d)
    tz = barber.get("workingHours", {}).get("timezone", "Europe/Madrid")
    if not wh:
        return AvailabilityResponse(barberId=barber_id, date=date_str, timezone=tz, slotMinutes=slot_minutes, available=[])

    open_t = parse_hhmm(wh["open"])
    close_t = parse_hhmm(wh["close"])

    # Determinar duración efectiva a bloquear: si hay serviceId, usar su duración; si no, usar slotMinutes o 30.
    duration_minutes = slot_minutes
    if service_id is not None:
        svc = session.get(ServiceDB, service_id)
        if svc and getattr(svc, "durationMinutes", None):
            try:
                duration_minutes = int(svc.durationMinutes)
            except Exception:
                duration_minutes = max(5, slot_minutes)
    duration_minutes = max(5, duration_minutes)

    slots = daterange_times(open_t, close_t, slot_minutes)
    available = []
    # Cargar reservas existentes para el barbero y fecha (SQL + memoria) y construir intervalos
    existing_intervals: list[tuple[datetime, datetime]] = []
    sql_rows = session.exec(select(BookingDB).where(col(BookingDB.barberId) == barber_id)).all()
    for r in sql_rows:
        # Ignorar canceladas
        if getattr(r, "status", None) and r.status.lower() in CANCELLED_STATES:
            continue
        if r.start and r.end and isinstance(r.start, str) and r.start.startswith(f"{date_str}T"):
            try:
                sdt = datetime.strptime(r.start, "%Y-%m-%dT%H:%M")
                edt = datetime.strptime(r.end, "%Y-%m-%dT%H:%M")
                existing_intervals.append((sdt, edt))
            except Exception:
                pass
    for r in DB.get("bookings", []):
        if r.get("status", "").lower() in CANCELLED_STATES:
            continue
        if r.get("barberId") == barber_id and isinstance(r.get("start"), str) and r["start"].startswith(f"{date_str}T"):
            try:
                sdt = datetime.strptime(r["start"], "%Y-%m-%dT%H:%M")
                edt = datetime.strptime(r["end"], "%Y-%m-%dT%H:%M")
                existing_intervals.append((sdt, edt))
            except Exception:
                pass

    close_dt = datetime.strptime(f"{date_str}T{close_t.strftime('%H:%M')}", "%Y-%m-%dT%H:%M")

    for hhmm in slots:
        start_iso = f"{date_str}T{hhmm}"
        try:
            start_dt = datetime.strptime(start_iso, "%Y-%m-%dT%H:%M")
        except ValueError:
            continue
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        # Debe caber dentro del horario de cierre
        if end_dt > close_dt:
            continue

        # Comprobar solape de intervalos: [start_dt, end_dt) con cualquier reserva existente
        overlaps = any(not (end_dt <= s or start_dt >= e) for (s, e) in existing_intervals)
        if overlaps:
            continue

        available.append(hhmm)

    return AvailabilityResponse(barberId=barber_id, date=date_str, timezone=tz, slotMinutes=slot_minutes, available=available)


@router.get("", summary="Obtener disponibilidad (GET retrocompatible)", response_model=AvailabilityResponse)
def get_availability(
    barberId: int = Query(..., description="Id del barbero"),
    dateStr: str = Query(..., description="Fecha YYYY-MM-DD"),
    slotMinutes: int = Query(30, ge=5, le=60, description="Granularidad del slot (por defecto 30 minutos)"),
    serviceId: Optional[int] = Query(None, description="Opcional: id de servicio"),
    session: Session = Depends(get_session),
):
    return _compute_availability(barberId, dateStr, slotMinutes, serviceId, session)


@router.post("", summary="Obtener disponibilidad (POST recomendado)", response_model=AvailabilityResponse)
def post_availability(payload: AvailabilityRequest, session: Session = Depends(get_session)):
    return _compute_availability(payload.barberId, payload.dateStr, payload.slotMinutes, payload.serviceId, session)