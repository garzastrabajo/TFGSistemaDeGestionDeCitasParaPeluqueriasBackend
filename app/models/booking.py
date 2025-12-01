from __future__ import annotations

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator, PrivateAttr
from sqlmodel import SQLModel, Field as SQLField
from sqlalchemy import Index


# ---------------- Nuevos modelos alineados con C# ----------------

class AppointmentState(str, Enum):
    Pendiente = "Pendiente"
    Confirmada = "Confirmada"
    Cancelada = "Cancelada"
    Completada = "Completada"


class Appointment(BaseModel):
    id: int
    userId: int
    barbershopId: int
    barberId: int
    serviceId: int

    scheduledAt: datetime
    startAt: datetime
    endAt: datetime

    state: AppointmentState = AppointmentState.Pendiente
    notes: Optional[str] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Helper para retrocompatibilidad
    def to_legacy_booking(self, customer_name: str, customer_phone: Optional[str] = None) -> "Booking":
        return Booking(
            id=self.id,
            barberId=self.barberId,
            serviceId=self.serviceId,
            customerName=customer_name,
            customerPhone=customer_phone,
            start=self.startAt.strftime("%Y-%m-%dT%H:%M"),
            end=self.endAt.strftime("%Y-%m-%dT%H:%M"),
            status=self.state.value.lower(),
        )


# ---------------- Retrocompatibilidad (tu endpoint actual usa esto) ----------------
# Mantén estos mientras migras a Appointment. Booking representa tu reserva antigua
# con start/end como string ISO "YYYY-MM-DDTHH:MM".

class Booking(BaseModel):
    id: int
    barberId: int
    serviceId: int
    customerName: str
    customerPhone: Optional[str] = None
    start: str   # ISO YYYY-MM-DDTHH:MM
    end: str     # ISO YYYY-MM-DDTHH:MM
    status: str  # suggested: "confirmed", etc.
    # Enriquecidos para UI
    barberName: Optional[str] = None
    serviceName: Optional[str] = None

    def to_appointment(
        self,
        user_id: int,
        barbershop_id: int,
        duration_minutes: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Appointment:
        start_dt = datetime.strptime(self.start, "%Y-%m-%dT%H:%M")
        if duration_minutes is None:
            # Si no viene duración, intenta deducirla del end
            try:
                end_dt = datetime.strptime(self.end, "%Y-%m-%dT%H:%M")
                duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
            except Exception:
                duration_minutes = 30
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        return Appointment(
            id=self.id,
            userId=user_id,
            barbershopId=barbershop_id,
            barberId=self.barberId,
            serviceId=self.serviceId,
            scheduledAt=start_dt,
            startAt=start_dt,
            endAt=end_dt,
            state=AppointmentState.Pendiente,
            notes=notes,
        )


class CreateBooking(BaseModel):
    barberId: int
    serviceId: int
    date: str          # "YYYY-MM-DD"
    time: str          # "HH:MM"
    customerName: Optional[str] = None
    customerPhone: Optional[str] = None

    _start_dt: Optional[datetime] = PrivateAttr(default=None)

    @model_validator(mode="after")
    def _parse_datetime(self) -> "CreateBooking":
        try:
            self._start_dt = datetime.fromisoformat(f"{self.date}T{self.time}")
        except Exception as e:
            raise ValueError(f"Formato inválido de fecha/hora: {e}")
        return self

    def to_booking(self, new_id: int, duration_minutes: int = 30) -> Booking:
        start_dt = self._start_dt or datetime.fromisoformat(f"{self.date}T{self.time}")
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        return Booking(
            id=new_id,
            barberId=self.barberId,
            serviceId=self.serviceId,
            customerName=self.customerName,
            customerPhone=self.customerPhone,
            start=start_dt.strftime("%Y-%m-%dT%H:%M"),
            end=end_dt.strftime("%Y-%m-%dT%H:%M"),
            status="confirmed",
        )


__all__ = [
    "AppointmentState",
    "Appointment",
    "Booking",
    "CreateBooking",
]


class BookingTable(SQLModel, table=True):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_bookings_user_start", "userId", "start"),
    )
    id: Optional[int] = SQLField(default=None, primary_key=True)
    barberId: int = SQLField(foreign_key="barbers.id")
    serviceId: int = SQLField(foreign_key="services.id")
    # Nueva columna opcional vinculada al usuario autenticado (para histórico propio)
    userId: Optional[int] = SQLField(default=None, foreign_key="user.id")
    customerName: str
    customerPhone: Optional[str] = None
    start: str  # YYYY-MM-DDTHH:MM
    end: str    # YYYY-MM-DDTHH:MM
    status: str = "confirmed"