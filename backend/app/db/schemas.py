from pydantic import BaseModel, EmailStr
from typing import Literal
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Literal["admin", "repair_shop", "user"]

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime

    class Config:
        orm_mode = True
