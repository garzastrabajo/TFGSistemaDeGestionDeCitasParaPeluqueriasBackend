from fastapi import APIRouter, HTTPException, Query, Depends, Request
from datetime import datetime, timezone
from sqlmodel import Session, select

from app.db import get_session
from app.helpers.db_memory import DB
from app.models.review import Review, CreateReview
from app.models.review import ReviewTable as ReviewDB
from app.models.user import UserTable
from app.helpers.urls import ensure_absolute
from app.endpoints.auth import get_current_user, UserInfo

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_legacy(r: ReviewDB) -> Review:
    return Review(
        id=r.id,
        barberId=r.barberId,
        serviceId=r.serviceId,
        rating=r.rating,
        comment=r.comment,
        userName=r.userName,
        createdAt=_iso_z(r.createdAt),
        userPhotoUrl=getattr(r, "userPhotoUrl", None),
    )

def _abs(request: Request, review: Review) -> Review:
    # Normaliza userPhotoUrl a absoluta si es relativa
    review.userPhotoUrl = ensure_absolute(review.userPhotoUrl, str(request.base_url)) if review.userPhotoUrl else review.userPhotoUrl
    return review


def _normalize_fk(value: int | None) -> int | None:
    # Algunas UIs envían 0 para "sin seleccionar"; convertirlo a None para evitar violar FKs
    if value is None:
        return None
    return value if value != 0 else None


@router.get("", summary="Listado de reviews (filtradas opcionalmente)", response_model=list[Review])
def get_reviews(
    request: Request,
    barberId: int | None = Query(None),
    serviceId: int | None = Query(None),
    session: Session = Depends(get_session),
):
    items_db = session.exec(select(ReviewDB)).all()
    if items_db:
        reviews = items_db
        if barberId is not None:
            reviews = [r for r in reviews if r.barberId == barberId]
        if serviceId is not None:
            reviews = [r for r in reviews if r.serviceId == serviceId]
        reviews = sorted(reviews, key=lambda r: r.createdAt, reverse=True)
        # Componer SIEMPRE nombre y foto desde perfil del usuario si hay userId
        user_ids = {r.userId for r in reviews if getattr(r, "userId", None)}
        users_by_id: dict[int, UserTable] = {}
        if user_ids:
            users = session.exec(select(UserTable).where(UserTable.id.in_(list(user_ids)))).all()
            users_by_id = {u.id: u for u in users if u and u.id is not None}

        base = str(request.base_url)
        result: list[Review] = []
        for r in reviews:
            legacy = _to_legacy(r)
            uid = getattr(r, "userId", None)
            u = users_by_id.get(uid) if uid else None
            if u:
                legacy.userName = u.name or u.username
                photo = getattr(u, "photo_url", None)
                legacy.userPhotoUrl = ensure_absolute(photo, base) if photo else None
            else:
                legacy.userPhotoUrl = ensure_absolute(legacy.userPhotoUrl, base) if legacy.userPhotoUrl else None
            result.append(legacy)
        return result

    reviews_mem = DB["reviews"]
    if barberId is not None:
        reviews_mem = [r for r in reviews_mem if r["barberId"] == barberId]
    if serviceId is not None:
        reviews_mem = [r for r in reviews_mem if r["serviceId"] == serviceId]
    reviews_mem = sorted(reviews_mem, key=lambda r: r.get("createdAt", ""), reverse=True)
    result: list[Review] = []
    base = str(request.base_url)
    for rm in reviews_mem:
        photo = rm.get("userPhotoUrl") or rm.get("photoUrl")  # distintos seeds posibles
        if photo and not (photo.startswith("http://") or photo.startswith("https://")):
            rm = {**rm, "userPhotoUrl": ensure_absolute(photo, base)}
        result.append(rm)  # tipo dict compatible con response_model
    return result


@router.get("/{review_id}", summary="Detalle de review", response_model=Review)
def get_review(review_id: int, request: Request, session: Session = Depends(get_session)):
    r = session.get(ReviewDB, review_id)
    if r:
        legacy = _to_legacy(r)
        uid = getattr(r, "userId", None)
        if uid:
            u = session.get(UserTable, uid)
            if u:
                legacy.userName = u.name or u.username
                photo = getattr(u, "photo_url", None)
                legacy.userPhotoUrl = ensure_absolute(photo, str(request.base_url)) if photo else None
            else:
                legacy.userPhotoUrl = ensure_absolute(legacy.userPhotoUrl, str(request.base_url)) if legacy.userPhotoUrl else None
        else:
            legacy.userPhotoUrl = ensure_absolute(legacy.userPhotoUrl, str(request.base_url)) if legacy.userPhotoUrl else None
        return legacy
    m = next((x for x in DB["reviews"] if x["id"] == review_id), None)
    if not m:
        raise HTTPException(status_code=404, detail="No existe la review")
    photo = m.get("userPhotoUrl") or m.get("photoUrl")
    if photo and not (photo.startswith("http://") or photo.startswith("https://")):
        m = {**m, "userPhotoUrl": ensure_absolute(photo, str(request.base_url))}
    return m


@router.post("", status_code=201, summary="Crear review (solo SQL)", response_model=Review)
def create_review(
    payload: CreateReview,
    request: Request,
    session: Session = Depends(get_session),
    current: UserInfo = Depends(get_current_user),
):
    # Obtener datos del usuario actual desde la BD para rellenar identidad
    user = session.exec(select(UserTable).where(UserTable.username == current.username)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario actual no válido")

    r = ReviewDB(
        barberId=_normalize_fk(payload.barberId),
        serviceId=_normalize_fk(payload.serviceId),
        rating=payload.rating,
        comment=payload.comment,
        # No persistir snapshot de nombre/foto; siempre se resolverán al leer
        userName=None,
        userPhotoUrl=None,
        createdAt=datetime.now(timezone.utc),
        userId=user.id,
    )
    session.add(r)
    session.commit()
    session.refresh(r)
    # Responder con nombre/foto actuales del perfil
    legacy = _to_legacy(r)
    legacy.userName = user.name or user.username
    photo = getattr(user, "photo_url", None)
    legacy.userPhotoUrl = ensure_absolute(photo, str(request.base_url)) if photo else None
    return legacy


@router.put("/{review_id}", summary="Actualizar review (solo SQL)", response_model=Review)
def update_review(review_id: int, payload: ReviewDB, request: Request, session: Session = Depends(get_session)):
    r = session.get(ReviewDB, review_id)
    if not r:
        raise HTTPException(status_code=404, detail="No existe la review (SQL)")
    for field in ["barberId", "serviceId", "rating", "comment", "userName", "userPhotoUrl"]:
        val = getattr(payload, field, None)
        if field in ("barberId", "serviceId"):
            val = _normalize_fk(val)
        if val is not None:
            setattr(r, field, val)
    session.add(r)
    session.commit()
    session.refresh(r)
    return _abs(request, _to_legacy(r))


@router.delete("/{review_id}", summary="Eliminar review (solo SQL)", status_code=204)
def delete_review(review_id: int, session: Session = Depends(get_session)):
    r = session.get(ReviewDB, review_id)
    if not r:
        raise HTTPException(status_code=404, detail="No existe la review (SQL)")
    session.delete(r)
    session.commit()
    return None