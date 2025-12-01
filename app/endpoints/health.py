from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("", summary="Chequeo de salud de la API")
def health():
    return {"status": "ok"}