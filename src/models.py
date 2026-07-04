from __future__ import annotations

from datetime import date, time as dtime, datetime
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, String, Time, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Master(Base):
    __tablename__ = "masters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    services: Mapped[list["Service"]] = relationship(
        back_populates="master", cascade="all, delete-orphan"
    )
    slots: Mapped[list["Slot"]] = relationship(
        back_populates="master", cascade="all, delete-orphan"
    )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="master")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[int] = mapped_column(Integer)
    duration_min: Mapped[int] = mapped_column(Integer)
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"))
    master: Mapped["Master"] = relationship(back_populates="services")


class Slot(Base):
    __tablename__ = "slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"))
    date: Mapped[date] = mapped_column(Date)
    time_start: Mapped[dtime] = mapped_column(Time)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)

    master: Mapped["Master"] = relationship(back_populates="slots")
    booking: Mapped[Optional["Booking"]] = relationship(back_populates="slot", uselist=False)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    slot_id: Mapped[int | None] = mapped_column(ForeignKey("slots.id"), nullable=True)
    date: Mapped[date] = mapped_column(Date)
    time: Mapped[dtime] = mapped_column(Time)
    client_name: Mapped[str] = mapped_column(String(100))
    client_phone: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    master: Mapped["Master"] = relationship(back_populates="bookings")
    slot: Mapped[Optional["Slot"]] = relationship(back_populates="booking")
