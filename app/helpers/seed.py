from sqlmodel import Session, select
from app.db import engine
from app.helpers.db_memory import DB

from app.models.barbershop import BarbershopTable
from app.models.barber import BarberTable
from app.models.category import ServiceCategoryTable, ProductCategoryTable
from app.models.service import ServiceTable
from app.models.product import ProductTable
from app.models.gallery import GalleryItemTable
from app.models.review import ReviewTable
from app.models.booking import BookingTable
from app.models.user import UserTable
from app.endpoints.auth import pwd_context

from datetime import datetime, timezone  # <-- añadido


def _to_dt(value):  # <-- añadido
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)
    return datetime.now(timezone.utc)


def seed_memory_data() -> None:
    """
    Inserta los datos de DB (memoria) en las tablas SQL SOLO si están vacías.
    No pisa registros existentes.
    """
    with Session(engine) as session:
        # Barbershop (uno)
        if DB.get("barbershop") and not session.exec(select(BarbershopTable)).first():
            session.add(BarbershopTable(**DB["barbershop"]))
            session.commit()

        # Service Categories
        if DB.get("serviceCategories") and not session.exec(select(ServiceCategoryTable)).first():
            for sc in DB["serviceCategories"]:
                session.add(ServiceCategoryTable(**sc))
            session.commit()

        # Product Categories
        if DB.get("productCategories") and not session.exec(select(ProductCategoryTable)).first():
            for pc in DB["productCategories"]:
                session.add(ProductCategoryTable(**pc))
            session.commit()

        # Services
        if DB.get("services") and not session.exec(select(ServiceTable)).first():
            for s in DB["services"]:
                session.add(ServiceTable(**s))
            session.commit()

        # Products
        if DB.get("products") and not session.exec(select(ProductTable)).first():
            for p in DB["products"]:
                session.add(ProductTable(**p))
            session.commit()

        # Barbers
        if DB.get("barbers") and not session.exec(select(BarberTable)).first():
            for b in DB["barbers"]:
                session.add(BarberTable(**b))
            session.commit()

        # Gallery
        if DB.get("gallery") and not session.exec(select(GalleryItemTable)).first():
            for g in DB["gallery"]:
                session.add(GalleryItemTable(**g))
            session.commit()

        # Reviews  (convertimos createdAt a datetime)
        if DB.get("reviews") and not session.exec(select(ReviewTable)).first():
            for r in DB["reviews"]:
                session.add(ReviewTable(
                    barberId=r["barberId"],
                    serviceId=r["serviceId"],
                    rating=r["rating"],
                    comment=r["comment"],
                    userName=r["userName"],
                    createdAt=_to_dt(r.get("createdAt")),
                ))
            session.commit()

        # Bookings
        if DB.get("bookings") and not session.exec(select(BookingTable)).first():
            for bk in DB["bookings"]:
                session.add(BookingTable(**bk))
            session.commit()

        print("[SEED] Datos de memoria insertados (si las tablas estaban vacías).")


def ensure_admin_user(username: str = "admin", password: str = "admin") -> None:
    """Crea un usuario administrador por defecto si no existe.

    - username: admin
    - password: admin
    - roles: ["admin"]
    """
    with Session(engine) as session:
        existing = session.exec(select(UserTable).where(UserTable.username == username)).first()
        if existing:
            return

        hashed = pwd_context.hash(password)
        admin = UserTable(
            username=username,
            email="admin@example.com",
            name="Administrador",
            password_hash=hashed,
            roles=["admin"],
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        print(f"[SEED] Usuario admin creado: {admin.username}")