from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Float, Enum, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("admin", "repair_shop", "user"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    repair_shop = relationship("RepairShop", back_populates="owner", uselist=False)

class RepairShop(Base):
    __tablename__ = "repairshops"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    description = Column(String(500), nullable=True)
    approved = Column(Boolean, default=False)
    rating_avg = Column(Float, default=0.0)
    latitude = Column(Float, nullable=True)      # Thêm
    longitude = Column(Float, nullable=True)     # Thêm
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="repair_shop")
    services = relationship("Service", back_populates="repair_shop")
    reviews = relationship("Review", back_populates="repair_shop")

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    repair_shop_id = Column(Integer, ForeignKey("repairshops.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    price = Column(DECIMAL(10,2), nullable=False)
    duration = Column(Integer, nullable=False)  # phút
    is_available = Column(Boolean, default=True)

    repair_shop = relationship("RepairShop", back_populates="services")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    repair_shop_id = Column(Integer, ForeignKey("repairshops.id"), nullable=False)
    status = Column(Enum("pending", "confirmed", "in_progress", "completed", "cancelled"), default="pending")
    order_date = Column(DateTime, default=func.now())
    scheduled_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    amount = Column(DECIMAL(10,2), nullable=False)
    payment_method = Column(Enum("credit_card", "cash", "ewallet"), nullable=False)
    transaction_id = Column(String(255), nullable=True)
    status = Column(Enum("pending", "completed", "failed"), default="pending")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    repair_shop_id = Column(Integer, ForeignKey("repairshops.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())
    repair_shop = relationship("RepairShop", back_populates="reviews") 
