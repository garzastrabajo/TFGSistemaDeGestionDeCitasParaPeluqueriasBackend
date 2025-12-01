"""
Registro central de routers. Añade aquí cualquier nuevo recurso.
"""
from fastapi import FastAPI

from .root import router as root_router
from .health import router as health_router
from .barbers import router as barbers_router
from .barbershop import router as barbershop_router
from .services import router as services_router
from .service_categories import router as service_categories_router
from .products import router as products_router
from .product_categories import router as product_categories_router
from .gallery import router as gallery_router
from .reviews import router as reviews_router
from .availability import router as availability_router
from .bookings import router as bookings_router
from .auth import router as auth_router
from .users import router as users_router


def register_routers(app: FastAPI) -> None:
    app.include_router(root_router)
    app.include_router(health_router)
    app.include_router(barbers_router)
    app.include_router(barbershop_router)
    app.include_router(services_router)
    app.include_router(service_categories_router)
    app.include_router(products_router)
    app.include_router(product_categories_router)
    app.include_router(gallery_router)
    app.include_router(reviews_router)
    app.include_router(availability_router)
    app.include_router(bookings_router)
    app.include_router(auth_router)
    app.include_router(users_router)