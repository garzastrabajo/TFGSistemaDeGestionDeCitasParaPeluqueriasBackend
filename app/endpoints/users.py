from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models.user import UserTable
from app.endpoints.auth import get_current_user, UserInfo
from app.helpers.urls import ensure_absolute

from pathlib import Path
from io import BytesIO
import logging
import traceback


router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None  # cambiado: EmailStr -> str para evitar dependencia email-validator
    name: Optional[str] = None
    phone: Optional[str] = None
    birthDate: Optional[date] = None
    photoUrl: Optional[str] = None
    createdAt: datetime


class UpdateUserProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None  # EmailStr -> str
    phone: Optional[str] = None
    birthDate: Optional[date] = None
    photoUrl: Optional[str] = None


@router.get("/me", response_model=UserProfileResponse)
def get_me(
    request: Request,
    current: UserInfo = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user = session.exec(select(UserTable).where(UserTable.username == current.username)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    photo = getattr(user, "photo_url", None)
    photo_abs = ensure_absolute(photo, str(request.base_url)) if photo else None
    return UserProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        name=user.name,
        phone=getattr(user, "phone", None),
        birthDate=getattr(user, "birth_date", None),
        photoUrl=photo_abs,
        createdAt=user.created_at,
    )


@router.put("/me", status_code=status.HTTP_204_NO_CONTENT)
def update_me(
    req: UpdateUserProfileRequest,
    request: Request,
    current: UserInfo = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    user = session.exec(select(UserTable).where(UserTable.username == current.username)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    prev_name = user.name
    if req.name is not None:
        user.name = req.name

    if req.email is not None:
        exists = session.exec(
            select(UserTable).where(UserTable.email == req.email, UserTable.username != current.username)
        ).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado")
        user.email = req.email

    if hasattr(user, "phone") and req.phone is not None:
        user.phone = req.phone

    # Validación y actualización de birthDate
    if req.birthDate is not None:
        today = date.today()
        if req.birthDate > today:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="birthDate no puede ser futura")
        min_allowed = date(today.year - 120, today.month, today.day)
        if req.birthDate < min_allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="birthDate fuera de rango (más de 120 años)")
        if hasattr(user, "birth_date"):
            user.birth_date = req.birthDate

    if req.photoUrl is not None and hasattr(user, "photo_url"):
        user.photo_url = req.photoUrl

    session.add(user)
    session.commit()

    return None


class PhotoUploadResponse(BaseModel):
    photoUrl: str


@router.post("/me/photo", response_model=PhotoUploadResponse)
async def upload_my_photo(
    request: Request,
    file: UploadFile = File(...),
    current: UserInfo = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # Obtener usuario actual desde la BD (necesitamos su id)
    user = session.exec(select(UserTable).where(UserTable.username == current.username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        # Leer datos en memoria y validar tamaño
        data = await file.read()
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Archivo demasiado grande (máx. 5 MB)")

        # Validar contenido real de imagen (no solo cabeceras del cliente)
        try:
            from PIL import Image, UnidentifiedImageError  # type: ignore
        except Exception:
            logger.exception("Pillow no disponible")
            raise HTTPException(status_code=500, detail="Validación de imagen no disponible en el servidor")

        detected_ext = None
        try:
            bio = BytesIO(data)
            img = Image.open(bio)
            img.verify()  # valida integridad
            fmt = img.format.upper() if img.format else ""
            if fmt == "JPEG":
                detected_ext = ".jpg"
            elif fmt == "PNG":
                detected_ext = ".png"
            elif fmt == "WEBP":
                detected_ext = ".webp"
            else:
                raise HTTPException(status_code=400, detail="Formato de imagen no soportado (use JPG, PNG o WEBP)")
        except UnidentifiedImageError:
            raise HTTPException(status_code=400, detail="El archivo no es una imagen válida")
        except HTTPException:
            raise
        except Exception:
            logger.exception("Error validando la imagen")
            raise HTTPException(status_code=400, detail="El archivo no es una imagen válida")

        ext = detected_ext
        # Ruta absoluta: .../TFG/static/user-photos
        project_root = Path(__file__).resolve().parents[2]
        folder = project_root / "static" / "user-photos"
        folder.mkdir(parents=True, exist_ok=True)

        filename = f"user-{user.id}-{int(datetime.utcnow().timestamp())}{ext}"
        path = folder / filename

        try:
            # Re-abrimos y guardamos para normalizar el archivo
            img2 = Image.open(BytesIO(data))
            save_params = {}
            if ext == ".jpg":
                save_params = {"quality": 90, "optimize": True}
            img2.save(str(path), **save_params)
        except Exception:
            logger.exception("Error guardando la imagen en disco: %s", path)
            raise HTTPException(status_code=500, detail="No se pudo guardar la imagen en el servidor")

        base = str(request.base_url)
        public_url = ensure_absolute(f"static/user-photos/{filename}", base)

        user.photo_url = public_url
        session.add(user)
        session.commit()

        return PhotoUploadResponse(photoUrl=public_url)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error imprevisto al subir foto:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error interno al subir la foto. Comprueba logs del servidor para más detalles.")
