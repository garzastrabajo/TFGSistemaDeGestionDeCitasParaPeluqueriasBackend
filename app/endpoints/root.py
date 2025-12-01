from fastapi import APIRouter

router = APIRouter(tags=["root"])

@router.get("/", summary="Información general de la API")
def root():
    return {
        "name": "API Barbería 💈",
        "version": "1.0.0",
        "endpoints": [
            "/barbers",
            "/barbers/{id}",
            "/barbers/by-service/{service_id}",
            "/products",
            "/products/{id}",
            "/products/by-category/{category_id}",
            "/product-categories",
            "/services",
            "/services/{id}",
            "/service-categories",
            "/barbershop",
            "/gallery",
            "/reviews (GET, POST)",
            "/availability",
            "/bookings (GET, POST)",
            "/bookings/me",
            "/bookings/{id}",
            "/health"
        ]
    }