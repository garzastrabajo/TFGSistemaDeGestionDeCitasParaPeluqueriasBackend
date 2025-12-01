from .availability import AvailabilityResponse

from .booking import (
    Appointment,
    AppointmentState,
    Booking,
    CreateBooking,
)

from .barber import Barber, BarberSchedule, DayOfWeek
from .barbershop import (
    Barbershop,
    BarbershopSchedule,
    SocialLinks,
    OpeningHours,
    DayHours,
)

from .category import ProductCategory, ServiceCategory
from .gallery import GalleryItem
from .product import Product, InventoryItem, InventoryRecord

# Reexportamos Review y CreateReview apuntando al legacy por compatibilidad
from .review import (
    Review,                 # alias a ReviewLegacy
    CreateReview,           # alias a CreateReviewLegacy
    ReviewLegacy,
    CreateReviewLegacy,
    ReviewNew,
    ServiceReview,
)

from .service import ServiceOffering, Service


__all__ = [
    # Availability
    "AvailabilityResponse",
    # Booking / Appointment
    "Appointment",
    "AppointmentState",
    "Booking",
    "CreateBooking",
    # Barber
    "Barber",
    "BarberSchedule",
    "DayOfWeek",
    # Barbershop
    "Barbershop",
    "BarbershopSchedule",
    "SocialLinks",
    "OpeningHours",
    "DayHours",
    # Categories
    "ProductCategory",
    "ServiceCategory",
    # Gallery
    "GalleryItem",
    # Products & Inventory
    "Product",
    "InventoryItem",
    "InventoryRecord",
    # Reviews (legacy + nuevos)
    "Review",
    "CreateReview",
    "ReviewLegacy",
    "CreateReviewLegacy",
    "ReviewNew",
    "ServiceReview",
    # Services
    "ServiceOffering",
    "Service",
    # User
    "User",
]