from pydantic import BaseModel, EmailStr, Field, ConfigDict # Import ConfigDict for Pydantic V2
from typing import List, Optional, Literal, Annotated
from datetime import datetime
from decimal import Decimal

# --- Base Configuration for Pydantic V2 ---
# Replace class Config: orm_mode = True
# with model_config = ConfigDict(from_attributes=True)

# --- Existing Schemas (for context, ensure these are defined) ---
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: Literal["admin", "repair_shop", "user"]

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- New/Updated Schemas for Admin Management ---

# User Management Schemas
class UserUpdateAdmin(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[Literal["admin", "repair_shop", "user"]] = None
    # password: Optional[str] = None # If admin can change password

class UserDetailAdmin(UserOut):
    updated_at: datetime
    # model_config already inherited from UserOut if UserOut is base
    # If not, add: model_config = ConfigDict(from_attributes=True)


# RepairShop Schemas
class RepairShopBase(BaseModel):
    name: str
    address: str
    phone: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class RepairShopCreateAdmin(RepairShopBase):
    user_id: int
    approved: bool = False

class RepairShopUpdateAdmin(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    approved: Optional[bool] = None
    user_id: Optional[int] = None

class RepairShopOut(RepairShopBase):
    id: int
    user_id: int
    approved: bool
    rating_avg: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Service Schemas
class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    # Remove max_digits and decimal_places from Field for Decimal
    price: Decimal # Pydantic will validate it's a decimal
    duration: int
    is_available: bool = True

class ServiceCreateAdmin(ServiceBase):
    repair_shop_id: int

class ServiceUpdateAdmin(BaseModel): # This was line 85 in your traceback
    name: Optional[str] = None
    description: Optional[str] = None
    # Remove max_digits and decimal_places from Field for Decimal
    price: Optional[Decimal] = Field(default=None)
    duration: Optional[int] = None
    is_available: Optional[bool] = None
    repair_shop_id: Optional[int] = None

class ServiceOut(ServiceBase):
    id: int
    repair_shop_id: int

    model_config = ConfigDict(from_attributes=True)


# Order Schemas
class OrderBase(BaseModel):
    user_id: int
    service_id: int
    repair_shop_id: int
    status: Literal["pending", "confirmed", "in_progress", "completed", "cancelled"]
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None

class OrderCreateAdmin(OrderBase):
    pass

class OrderUpdateAdmin(BaseModel):
    user_id: Optional[int] = None
    service_id: Optional[int] = None
    repair_shop_id: Optional[int] = None
    status: Optional[Literal["pending", "confirmed", "in_progress", "completed", "cancelled"]] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None

class OrderOut(OrderBase):
    id: int
    order_date: datetime

    model_config = ConfigDict(from_attributes=True)


# Payment Schemas
class PaymentBase(BaseModel):
    order_id: int
    # Remove max_digits and decimal_places from Field for Decimal
    amount: Decimal # Pydantic will validate it's a decimal
    payment_method: Literal["credit_card", "cash", "ewallet"]
    transaction_id: Optional[str] = None
    status: Literal["pending", "completed", "failed"]

class PaymentCreateAdmin(PaymentBase):
    pass

class PaymentUpdateAdmin(BaseModel):
    order_id: Optional[int] = None
    # Remove max_digits and decimal_places from Field for Decimal
    amount: Optional[Decimal] = Field(default=None)
    payment_method: Optional[Literal["credit_card", "cash", "ewallet"]] = None
    transaction_id: Optional[str] = None
    status: Optional[Literal["pending", "completed", "failed"]] = None

class PaymentOut(PaymentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Review Schemas
class ReviewBase(BaseModel):
    user_id: int
    repair_shop_id: int
    # For numeric constraints like ge/le, Annotated is fine
    rating: Annotated[int, Field(..., ge=1, le=5)]
    comment: Optional[str] = None

class ReviewCreateAdmin(ReviewBase):
    pass

class ReviewUpdateAdmin(BaseModel):
    rating: Annotated[Optional[int], Field(default=None, ge=1, le=5)]
    comment: Optional[str] = None

class ReviewOut(ReviewBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Optional: Generic response for paginated lists
class PaginatedResponseMeta(BaseModel):
    total_items: int
    total_pages: int
    page: int
    page_size: int
