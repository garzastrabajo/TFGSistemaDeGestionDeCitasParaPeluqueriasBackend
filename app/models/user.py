from __future__ import annotations
from datetime import datetime, timezone, date
from typing import List, Optional

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


class UserTable(SQLModel, table=True):
    __tablename__ = "user"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, min_length=3, max_length=50)
    email: Optional[str] = Field(default=None, index=True, unique=True)
    name: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)
    # Nueva columna para fecha de nacimiento (persistencia de perfil)
    birth_date: Optional[date] = Field(default=None)
    # Nueva columna opcional para URL de foto de perfil
    photo_url: Optional[str] = Field(default=None, max_length=255)
    password_hash: str
    roles: List[str] = Field(default_factory=lambda: ["user"], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


__all__ = ["UserTable"]
