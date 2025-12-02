import sys
from pathlib import Path
import sys
import logging
import os

# Permite ejecutar este archivo directamente (python app/main.py) añadiendo la raíz del proyecto al sys.path.
# Raíz del proyecto = carpeta que contiene "app/"
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent  # .../TFG
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
import asyncio
from datetime import datetime
from sqlmodel import Session

from app.db import engine
from app.models.booking import BookingTable as BookingDB
from app.endpoints.bookings import persist_completed_bookings, CANCELLED_STATES, COMPLETED_STATES
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.endpoints import register_routers
from app.db import create_db_and_tables
# NUEVO: importar seeding
from app.helpers.seed import seed_memory_data, ensure_admin_user
from pathlib import Path as _P

app = FastAPI(
    title="API Barbería 💈",
    version="1.0.0",
    description="API Barbería para la gestión de citas en peluquerías Fast API + SQLModel + PostgreSQL."
)

# CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
register_routers(app)

# Archivos estáticos (fotos de usuario, etc.)
app.mount("/static", StaticFiles(directory="static", check_dir=False), name="static")

# Crear tablas al arrancar
@app.on_event("startup")
def on_startup():
    # DB init + seed
    create_db_and_tables()

    # Lanzar tarea en segundo plano para ir marcando reservas completadas.
    interval = int(os.getenv("AUTO_COMPLETE_INTERVAL_SECONDS", "300"))  # 5 min por defecto

    async def _auto_complete_loop():
        while True:
            try:
                with Session(engine) as session:
                    changed = persist_completed_bookings(session)
                # (Opcional) podrías añadir logging aquí
            except Exception:
                pass
            await asyncio.sleep(interval)

    try:
        asyncio.create_task(_auto_complete_loop())
    except RuntimeError:
        # Si no hay loop (ejecución síncrona directa), ignoramos.
        pass
    try:
        seed_memory_data()
    except Exception:
        logging.getLogger(__name__).exception("Error durante seed_memory_data")

    # Crear usuario admin: admin/admin si no existe
    try:
        ensure_admin_user()
    except Exception:
        logging.getLogger(__name__).exception("Error creando usuario admin por defecto")

    # Asegurar carpeta estática de fotos
    static_dir = _P(__file__).resolve().parents[1] / "static" / "user-photos"
    static_dir.mkdir(parents=True, exist_ok=True)

    # Chequeo de Pillow
    log = logging.getLogger(__name__)
    try:
        import PIL  # type: ignore
        ver = getattr(PIL, "__version__", "unknown")
        log.info("Pillow disponible: %s (python=%s)", ver, sys.executable)
    except Exception:
        log.warning("Pillow NO disponible. Instala dependencia en este intérprete: %s", sys.executable)

# Permitir arrancar con: python app/main.py
if __name__ == "__main__":
    import uvicorn
    # Nota: este target usa la ruta de módulo para que el autoreload funcione bien.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)