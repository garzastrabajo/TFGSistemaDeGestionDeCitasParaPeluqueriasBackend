"""Configuración de base de datos (SQLModel).

Lee `DATABASE_URL` del entorno (por defecto, SQLite local) y expone:
- `engine`
- `create_db_and_tables()`
- `get_session()`
"""

from __future__ import annotations
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import os
from dotenv import load_dotenv

# Carga .env si existe; si está corrupto, continúa con valores por defecto.
try:
    load_dotenv()
except ValueError:
    # Log mínimo; en producción usar logging.
    print("[WARN] .env corrupto, usando valores por defecto.")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")

# Si DATABASE_URL parece un ejemplo, usar SQLite local
if any(token in DATABASE_URL for token in [
    "usuario:password@host:5432/dbname",
    "usuario:password@host",
    "@host:5432",
]):
    print("[WARN] DATABASE_URL parece un ejemplo; usando SQLite (./data.db).")
    DATABASE_URL = "sqlite:///./data.db"

# Para SQLite conviene activar check_same_thread=False para uso con FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)


def create_db_and_tables() -> None:
    """Crear todas las tablas definidas en los modelos SQLModel.

    Importa cada módulo de modelos que define una clase *Table para que se
    registren en el metadata antes de crear las tablas.
    """
    global engine
    import app.models.barber          # BarberTable
    import app.models.barbershop      # BarbershopTable
    import app.models.service         # ServiceTable
    import app.models.category        # ProductCategoryTable & ServiceCategoryTable
    import app.models.product         # ProductTable
    import app.models.gallery         # GalleryItemTable
    import app.models.review          # ReviewTable
    import app.models.booking         # BookingTable
    import app.models.user            # UserTable
    try:
        SQLModel.metadata.create_all(engine)
        # Migración ligera: añadir columnas si faltan (SQLite/PostgreSQL)
        if engine.url.drivername.startswith("sqlite"):
            with engine.connect() as conn:
                cols = [row[1] for row in conn.execute(text("PRAGMA table_info('user')"))]
                changed = False
                if "phone" not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN phone VARCHAR(30)"))
                    changed = True
                if "birth_date" not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN birth_date DATE"))
                    changed = True
                if "photo_url" not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN photo_url VARCHAR(255)"))
                    changed = True
                review_cols = [row[1] for row in conn.execute(text("PRAGMA table_info('reviews')"))]
                if "userPhotoUrl" not in review_cols:
                    conn.execute(text("ALTER TABLE reviews ADD COLUMN userPhotoUrl VARCHAR(255)"))
                    changed = True
                if "userId" not in review_cols:
                    conn.execute(text("ALTER TABLE reviews ADD COLUMN userId INTEGER"))
                    changed = True
                if changed:
                    conn.commit()
        elif engine.url.drivername.startswith("postgresql"):
            # Soporte básico de migración para Postgres en despliegues con esa BD
            with engine.connect() as conn:
                changed = False
                # Columnas de user
                user_cols = [row[0] for row in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'user'"))]
                if "phone" not in user_cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN phone VARCHAR(30)"))
                    changed = True
                if "birth_date" not in user_cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN birth_date DATE"))
                    changed = True
                if "photo_url" not in user_cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN photo_url VARCHAR(255)"))
                    changed = True
                # Columnas de reviews
                review_cols = [row[0] for row in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'reviews'"))]
                if "userPhotoUrl" not in review_cols:
                    conn.execute(text("ALTER TABLE reviews ADD COLUMN \"userPhotoUrl\" VARCHAR(255)"))
                    changed = True
                if "userId" not in review_cols:
                    conn.execute(text("ALTER TABLE reviews ADD COLUMN \"userId\" INTEGER"))
                    changed = True
                if changed:
                    conn.commit()
    except OperationalError as e:
        # Si falla (p. ej. Postgres sin credenciales), usar SQLite local
        if DATABASE_URL.startswith("postgresql"):
            print(f"[WARN] Conexión BD falló: {e}. Fallback a SQLite ./data.db")
            fallback_url = "sqlite:///./data.db"
            engine = create_engine(
                fallback_url,
                connect_args={"check_same_thread": False},
            )
            SQLModel.metadata.create_all(engine)
        else:
            raise


def get_session() -> Generator[Session, None, None]:
    """Dependencia FastAPI para obtener una sesión de BD."""
    with Session(engine) as session:
        yield session
