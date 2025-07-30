from datetime import datetime, timezone
from database import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    access_token: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


class FoodBag(Base):
    __tablename__ = "food_bags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    image: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[float] = mapped_column(nullable=False)
    available_bags: Mapped[int] = mapped_column(nullable=False)
    address: Mapped[str] = mapped_column(nullable=False)
    owner: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    until_time: Mapped[datetime] = mapped_column(nullable=False)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    bag_id: Mapped[int] = mapped_column(ForeignKey("food_bags.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.now(timezone.utc),
        type_=TIMESTAMP(timezone=True),
    )
