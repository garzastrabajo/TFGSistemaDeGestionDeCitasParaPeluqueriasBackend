"""Backfill de userPhotoUrl en reviews a partir de users.photo_url (username coincidente).

- Completa solo registros con userPhotoUrl vacío (idempotente).
- Muestra un breve resumen al finalizar.

Uso (PowerShell, desde la raíz del proyecto):
    .\.venv\Scripts\python.exe .\scripts\backfill_user_photo_urls.py
"""
from __future__ import annotations
import sys
from pathlib import Path
from sqlmodel import Session, select

# Asegurar que la raíz del proyecto (carpeta que contiene 'app/') está en sys.path
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import engine, create_db_and_tables  # type: ignore
from app.models.review import ReviewTable  # type: ignore
from app.models.user import UserTable  # type: ignore


def run() -> None:
    create_db_and_tables()  # asegura metadata cargada
    updated = 0
    total_candidates = 0
    with Session(engine) as session:
        reviews = session.exec(select(ReviewTable)).all()
        for r in reviews:
            if getattr(r, "userPhotoUrl", None):
                continue
            total_candidates += 1
            if not r.userName:
                continue
            user = session.exec(select(UserTable).where(UserTable.username == r.userName)).first()
            if user and getattr(user, "photo_url", None):
                r.userPhotoUrl = user.photo_url
                session.add(r)
                updated += 1
        if updated:
            session.commit()
    print(f"Candidatos sin foto: {total_candidates}")
    print(f"Actualizados con foto: {updated}")
    print("Backfill completado.")


if __name__ == "__main__":
    run()
