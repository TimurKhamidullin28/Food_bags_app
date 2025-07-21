from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
from datetime import datetime


class UserCreateModel(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["Клиент", "Заведение"]


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str

    class Config:
        orm_mode = True


class FoodBagIn(BaseModel):
    name: str
    description: str
    image: Optional[str] = None
    price: float
    available_bags: int
    address: str
    until_time: datetime


class FoodBagOut(FoodBagIn):
    id: int

    class Config:
        orm_mode = True


class FoodBagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    price: Optional[float] = None
    available_bags: Optional[int] = None
    address: Optional[str] = None
    until_time: Optional[datetime] = None
