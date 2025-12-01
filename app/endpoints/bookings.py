from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, timedelta
from typing import Optional, List
from sqlmodel import Session, select, col

from app.db import get_session
from app.helpers.db_memory import DB
from app.helpers.scheduling import parse_hhmm, get_weekly_hours
from app.models.booking import Booking, CreateBooking
from app.models.booking import BookingTable as BookingDB
from app.models.barber import BarberTable as BarberDB
from app.models.service import ServiceTable as ServiceDB
from app.models.user import UserTable
from app.endpoints.auth import get_current_user, UserInfo

router = APIRouter(prefix="/bookings", tags=["bookings"])

# Conjunto de estados que representan cancelación (normalizamos a minúsculas)
CANCELLED_STATES = {"cancelled", "canceled"}
COMPLETED_STATES = {"completed", "completada"}

# Helper para persistir estados 'completed' en la base de datos.
# Marca como 'completed' todas las reservas cuyo end <= ahora y cuyo status
# no esté en CANCELLED_STATES ni COMPLETED_STATES. Devuelve el número de filas afectadas.
def persist_completed_bookings(session: Session) -> int:
    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M")
    rows = session.exec(
        select(BookingDB).where(
            (col(BookingDB.end) <= now_iso)
            & (~(col(BookingDB.status).in_(list(CANCELLED_STATES | COMPLETED_STATES))))
        )
    ).all()
    changed = 0
    for r in rows:
        r.status = "completed"
        session.add(r)
        changed += 1
    if changed:
        session.commit()
    return changed


def _to_model(b: BookingDB, session: Optional[Session] = None) -> Booking:
    barber_name = None
    service_name = None

    if session is not None:
        bar = session.get(BarberDB, b.barberId)
        svc = session.get(ServiceDB, b.serviceId)
        if bar is not None and getattr(bar, "name", None):
            barber_name = bar.name
        if svc is not None and getattr(svc, "name", None):
            service_name = svc.name

    # fallback memoria
    if barber_name is None:
        mem_bar = next((x for x in DB.get("barbers", []) if x["id"] == b.barberId), None)
        barber_name = mem_bar.get("name") if mem_bar else None

    if service_name is None:
        mem_svc = next((x for x in DB.get("services", []) if x["id"] == b.serviceId), None)
        service_name = mem_svc.get("name") if mem_svc else None

    # Normalizar status y marcar como 'completed' si la cita ya terminó.
    # No persiste el cambio, solo lo refleja en la respuesta.
    status = (getattr(b, "status", None) or "").strip()
    status_norm = status.lower()

    try:
        # Intentar usar 'end' y si no existe, fallback a 'start'
        end_str = getattr(b, "end", None) or getattr(b, "start", None)
        end_dt = datetime.strptime(end_str, "%Y-%m-%dT%H:%M") if end_str else None
    except Exception:
        end_dt = None

    if end_dt is not None and status_norm not in CANCELLED_STATES and status_norm not in COMPLETED_STATES:
        if end_dt <= datetime.now():
            status = "completed"  # literal en inglés para consistencia

    return Booking(
        id=b.id,
        barberId=b.barberId,
        serviceId=b.serviceId,
        customerName=b.customerName,
        customerPhone=b.customerPhone,
        start=b.start,
        end=getattr(b, "end", None),
        status=status,
        barberName=barber_name,
        serviceName=service_name,
    )


def _is_slot_booked_sql(session: Session, barber_id: int, start_iso: str, exclude_booking_id: Optional[int] = None) -> bool:
    """Devuelve True si existe una reserva NO cancelada para ese barbero y start.
    Ignora reservas cuyo status esté en CANCELLED_STATES.
    """
    stmt = select(BookingDB).where(
        (col(BookingDB.barberId) == barber_id)
        & (col(BookingDB.start) == start_iso)
        & (~(col(BookingDB.status).in_(list(CANCELLED_STATES))))  # ignorar canceladas
    )
    if exclude_booking_id is not None:
        stmt = stmt.where(col(BookingDB.id) != exclude_booking_id)
    return session.exec(stmt).first() is not None


def _find_barber(session: Session, barber_id: int) -> Optional[dict]:
    b = session.get(BarberDB, barber_id)
    if b:
        return {
            "id": b.id,
            "workingHours": b.workingHours or {},
        }
    return next((x for x in DB["barbers"] if x["id"] == barber_id), None)


def _find_service(session: Session, service_id: int) -> Optional[dict]:
    s = session.get(ServiceDB, service_id)
    if s:
        return {
            "id": s.id,
            "durationMinutes": s.durationMinutes,
        }
    return next((x for x in DB["services"] if x["id"] == service_id), None)


@router.get("", summary="Listado de reservas (filtros opcionales)", response_model=list[Booking])
def list_bookings(
    barberId: Optional[int] = Query(None),
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    session: Session = Depends(get_session),
):
    items_db = session.exec(select(BookingDB)).all()
    if items_db:
        rows = items_db
        if barberId is not None:
            rows = [r for r in rows if r.barberId == barberId]
        if date is not None:
            rows = [r for r in rows if r.start.startswith(f"{date}T")]
        return [_to_model(r, session) for r in rows]

    # Fallback memoria
    rows_mem = DB.get("bookings", [])
    if barberId is not None:
        rows_mem = [r for r in rows_mem if r["barberId"] == barberId]
    if date is not None:
        rows_mem = [r for r in rows_mem if r["start"].startswith(f"{date}T")]
    return rows_mem


@router.get("/me", summary="Listado de reservas del usuario autenticado", response_model=list[Booking])
def list_my_bookings(
    session: Session = Depends(get_session),
    current: UserInfo = Depends(get_current_user),
):
    user_rec = session.exec(select(UserTable).where(UserTable.username == current.username)).first()
    if not user_rec:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Primero: por userId (una vez migrada la columna)
    rows = session.exec(select(BookingDB).where(col(BookingDB.userId) == user_rec.id)).all()

    # Fallback compatibilidad: por nombre/username en reservas antiguas
    if not rows:
        rows = session.exec(
            select(BookingDB).where((col(BookingDB.customerName) == (user_rec.name or "")) | (col(BookingDB.customerName) == user_rec.username))
        ).all()

    return [_to_model(r, session) for r in rows]


@router.get("/me/upcoming", summary="Próximas reservas del usuario autenticado", response_model=list[Booking])
def list_my_upcoming_bookings(
    limit: int = Query(10, ge=1, le=50, description="Máximo de elementos a devolver"),
    states: List[str] = Query(["confirmed"], description="Estados a incluir (minúsculas)"),
    session: Session = Depends(get_session),
    current: UserInfo = Depends(get_current_user),
):
    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M")
    states_norm = [s.lower() for s in states]

    user_rec = session.exec(select(UserTable).where(UserTable.username == current.username)).first()
    if not user_rec:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Prioridad SQL por userId + start >= ahora + estado en lista
    stmt = (
        select(BookingDB)
        .where(
            (col(BookingDB.userId) == user_rec.id)
            & (col(BookingDB.start) >= now_iso)
            & (col(BookingDB.status).in_(states_norm))
        )
        .order_by(col(BookingDB.start).asc())
        .limit(limit)
    )
    rows = session.exec(stmt).all()
    if rows:
        return [_to_model(r, session) for r in rows]

    # Fallback a memoria en caso de tablas vacías o datos legacy
    name_candidates = set(filter(None, [getattr(user_rec, "name", None), current.username]))
    rows_mem = [
        r
        for r in DB.get("bookings", [])
        if r.get("start", "") >= now_iso
        and r.get("status", "confirmed").lower() in states_norm
        and r.get("customerName") in name_candidates
    ]
    rows_mem.sort(key=lambda r: r.get("start", ""))
    return rows_mem[:limit]


@router.get("/{booking_id}", summary="Detalle de reserva", response_model=Booking)
def get_booking(booking_id: int, session: Session = Depends(get_session)):
    b = session.get(BookingDB, booking_id)
    if b:
        return _to_model(b, session)
    m = next((x for x in DB["bookings"] if x["id"] == booking_id), None)
    if not m:
        raise HTTPException(status_code=404, detail="No existe la reserva")
    return m


@router.post("", status_code=201, summary="Crear reserva (SQL con validación)", response_model=Booking)
def create_booking(
    payload: CreateBooking,
    session: Session = Depends(get_session),
    current: UserInfo = Depends(get_current_user),
):
    # Validar barber y service
    barber = _find_barber(session, payload.barberId)
    service = _find_service(session, payload.serviceId)
    if not barber:
        raise HTTPException(status_code=400, detail="BarberId inválido")
    if not service:
        raise HTTPException(status_code=400, detail="ServiceId inválido")

    start_iso = f"{payload.date}T{payload.time}"

    # Validar horario de trabajo
    try:
        d = datetime.strptime(payload.date, "%Y-%m-%d").date()
        wh = get_weekly_hours(barber, d)
        if not wh:
            raise HTTPException(status_code=400, detail="El barbero no trabaja ese día")
        t = parse_hhmm(payload.time)
        if not (parse_hhmm(wh["open"]) <= t < parse_hhmm(wh["close"])):
            raise HTTPException(status_code=400, detail="Hora fuera del horario de atención")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha/hora inválido")

    # Validar solape
    if _is_slot_booked_sql(session, payload.barberId, start_iso):
        raise HTTPException(status_code=409, detail="El horario ya fue reservado")

    # Calcular fin por duración del servicio
    duration = int(service.get("durationMinutes", 30))
    end_dt = datetime.strptime(start_iso, "%Y-%m-%dT%H:%M") + timedelta(minutes=duration)

    # Tomar usuario autenticado desde la BD para obtener su id y nombre
    user_rec = session.exec(select(UserTable).where(UserTable.username == current.username)).first()
    customer_name = payload.customerName or (user_rec.name if user_rec and user_rec.name else current.username)
    user_id = user_rec.id if user_rec else None

    row = BookingDB(
        barberId=payload.barberId,
        serviceId=payload.serviceId,
        userId=user_id,
        customerName=customer_name,
        customerPhone=payload.customerPhone,
        start=start_iso,
        end=end_dt.strftime("%Y-%m-%dT%H:%M"),
        status="confirmed",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _to_model(row, session)


@router.post("/{booking_id}/cancel", summary="Cancelar reserva (marca como cancelled)", response_model=Booking)
def cancel_booking(
    booking_id: int,
    session: Session = Depends(get_session),
    current: UserInfo = Depends(get_current_user),
):
    """Marca una reserva futura como cancelada sin eliminarla.
    Regla: no se puede cancelar si ya inició o está en el pasado.
    Propiedad: por userId (migrado) o por coincidencia de nombre/username legacy.
    """
    b = session.get(BookingDB, booking_id)
    if not b:
        raise HTTPException(status_code=404, detail="No existe la reserva (SQL)")

    # Obtener registro de usuario
    user_rec = session.exec(select(UserTable).where(UserTable.username == current.username)).first()
    if user_rec:
        is_owner = (getattr(b, "userId", None) == user_rec.id) or (
            b.customerName in {user_rec.name or "", user_rec.username}
        )
    else:
        # Fallback si no se encontró user_rec (caso muy raro)
        is_owner = b.customerName == current.username

    if not is_owner:
        raise HTTPException(status_code=403, detail="No puedes cancelar esta reserva")

    # Evitar recancelar
    if b.status and b.status.lower() in CANCELLED_STATES:
        return _to_model(b, session)

    # Validar que la reserva es futura
    try:
        start_dt = datetime.strptime(b.start, "%Y-%m-%dT%H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha/hora interno inválido")

    now = datetime.now()
    if start_dt <= now:
        raise HTTPException(status_code=400, detail="No se puede cancelar una reserva iniciada o pasada")

    # Marcar como cancelada
    b.status = "cancelled"
    session.add(b)
    session.commit()
    session.refresh(b)
    return _to_model(b, session)


# (El endpoint /bookings/me se movió arriba para evitar conflicto con /{booking_id})


@router.put("/{booking_id}", summary="Actualizar reserva (solo SQL)", response_model=Booking)
def update_booking(booking_id: int, payload: BookingDB, session: Session = Depends(get_session)):
    b = session.get(BookingDB, booking_id)
    if not b:
        raise HTTPException(status_code=404, detail="No existe la reserva (SQL)")

    # Si cambian barberId o start, validar solape
    new_barber_id = payload.barberId if payload.barberId is not None else b.barberId
    new_start = payload.start if payload.start is not None else b.start
    if (new_barber_id != b.barberId) or (new_start != b.start):
        if _is_slot_booked_sql(session, new_barber_id, new_start, exclude_booking_id=b.id):
            raise HTTPException(status_code=409, detail="El horario ya fue reservado")

    for field in ["barberId", "serviceId", "customerName", "customerPhone", "start", "end", "status"]:
        val = getattr(payload, field, None)
        if val is not None:
            setattr(b, field, val)

    session.add(b)
    session.commit()
    session.refresh(b)
    return _to_model(b, session)


@router.delete("/{booking_id}", summary="Eliminar reserva (solo SQL)", status_code=204)
def delete_booking(booking_id: int, session: Session = Depends(get_session)):
    b = session.get(BookingDB, booking_id)
    if not b:
        raise HTTPException(status_code=404, detail="No existe la reserva (SQL)")
    session.delete(b)
    session.commit()
    return None