from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from app.db.database import get_db
from app.db.models import RepairShop
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import joinedload
from datetime import datetime
router = APIRouter()

class ShopOut(BaseModel):
    id: int
    name: str
    address: str
    phone: str
    latitude: float
    longitude: float

    class Config:
        orm_mode = True

class ServiceOut(BaseModel):
    id: int
    name: str
    description: str
    price: float
    duration: int
    is_available: bool

    class Config:
        orm_mode = True

class ReviewOut(BaseModel):
    id: int
    user_id: int
    rating: int
    comment: str
    created_at: datetime  # ✅ Đổi từ str -> datetime

    class Config:
        orm_mode = True

class RepairShopDetailOut(BaseModel):
    id: int
    name: str
    address: str
    phone: str
    description: str
    rating_avg: float
    services: List[ServiceOut]
    reviews: List[ReviewOut]

    class Config:
        orm_mode = True

@router.get("/shops", response_model=List[ShopOut])
def get_shops(db: Session = Depends(get_db)):
    shops = db.query(RepairShop).filter(RepairShop.approved == True).all()
    return shops


@router.get("/repairshop/{shop_id}", response_model=RepairShopDetailOut)
def get_repairshop_detail(shop_id: int, db: Session = Depends(get_db)):
    shop = (
        db.query(RepairShop)
        .options(
            joinedload(RepairShop.services),
            joinedload(RepairShop.reviews),
        )
        .filter(RepairShop.id == shop_id, RepairShop.approved == True)
        .first()
    )
    if not shop:
        raise HTTPException(status_code=404, detail="Repair shop not found")

    return shop

# app/api/booking.py
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, Service, RepairShop
from typing import List
 
@router.get("/preview")
def get_booking_preview(
    username: str,
    shop_id: int,
    service_ids: List[int] = Query(...),
    db: Session = Depends(get_db)
):
    print(f"Username: {username}, Shop ID: {shop_id}, Service IDs: {service_ids}")
    # 1. Lấy thông tin người dùng
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Lấy thông tin shop
    shop = db.query(RepairShop).filter(RepairShop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Repair shop not found")

    # 3. Lấy danh sách dịch vụ theo ID
    services = db.query(Service).filter(
        Service.id.in_(service_ids),
        Service.repair_shop_id == shop_id
    ).all()

    if not services:
        raise HTTPException(status_code=404, detail="No matching services found")

    return {
        "user": {
            "username": user.username,
            "email": user.email,
        },
        "shop": {
            "id": shop.id,
            "name": shop.name,
            "address": shop.address
        },
        "services": [
            {
                "id": s.id,
                "name": s.name,
                "price": float(s.price),
                "duration": s.duration
            } for s in services
        ]
    }


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, Service, RepairShop, Order, Payment
from pydantic import BaseModel, constr, condecimal
from enum import Enum
from typing import Optional
from datetime import datetime

# Enum cho trạng thái
class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class PaymentStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

# Schema nhận dữ liệu booking + thanh toán

class PaymentMethod(str, Enum):
    credit_card = "credit_card"
    cash = "cash"
    ewallet = "ewallet"
    momo = "momo"

class BookingPaymentIn(BaseModel):
    username: str
    shop_id: int
    service_id: int
    address: str
    phone: str
    scheduled_date: Optional[datetime]
    payment_method: PaymentMethod
    amount: condecimal(max_digits=10, decimal_places=2)
    transaction_id: Optional[str]

@router.post("/payment")
def create_booking_and_payment(data: BookingPaymentIn, db: Session = Depends(get_db)):
    print(f"Received booking data: {data}")
    # 1. Lấy user theo username
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Lấy repair shop
    shop = db.query(RepairShop).filter(RepairShop.id == data.shop_id, RepairShop.approved == True).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Repair shop not found or not approved")

    # 3. Lấy service
    service = db.query(Service).filter(Service.id == data.service_id, Service.repair_shop_id == data.shop_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found for this repair shop")

    # 4. Tạo Order mới
    new_order = Order(
        user_id=user.id,
        service_id=service.id,
        repair_shop_id=shop.id,
        status=OrderStatus.pending.value,
        order_date=datetime.utcnow(),
        scheduled_date=data.scheduled_date
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # 5. Tạo Payment liên kết với order
    new_payment = Payment(
        order_id=new_order.id,
        amount=data.amount,
        payment_method=data.payment_method.value,
        transaction_id=data.transaction_id,
        status=PaymentStatus.completed.value  # Giả sử thanh toán thành công luôn
    )
    db.add(new_payment)

    # 6. Cập nhật trạng thái Order sau khi thanh toán
    new_order.status = OrderStatus.confirmed.value

    db.commit()
    db.refresh(new_order)
    db.refresh(new_payment)

    return {
        "message": "Booking and payment successful",
        "order_id": new_order.id,
        "payment_id": new_payment.id,
        "status": new_order.status,
        "scheduled_date": new_order.scheduled_date,
    }



from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional
from sqlalchemy.sql import func
from app.db.database import get_db
from app.db.models import Review, RepairShop, User

class ReviewCreate(BaseModel):
    username: str
    repairshop_id: int  # không có dấu gạch dưới, đúng với dữ liệu FE
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

    @validator('comment')
    def comment_length(cls, v):
        if v and len(v) > 500:
            raise ValueError('Comment tối đa 500 ký tự')
        return v
@router.post("/reviews/", status_code=status.HTTP_201_CREATED)
def create_review(review: ReviewCreate, db: Session = Depends(get_db)):
    # Kiểm tra repair_shop tồn tại
    shop = db.query(RepairShop).filter(RepairShop.id == review.repairshop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Repair shop không tồn tại")

    # Tìm user theo username
    user = db.query(User).filter(User.username == review.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User không tồn tại")

    # Tạo review mới
    new_review = Review(
        user_id=user.id,
        repair_shop_id=review.repairshop_id,
        rating=review.rating,
        comment=review.comment
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    # Cập nhật rating trung bình của repair_shop
    avg_rating = db.query(func.avg(Review.rating)).filter(Review.repair_shop_id == review.repairshop_id).scalar()
    shop.rating_avg = float(round(avg_rating, 2))
    db.commit()

    return {"message": "Review đã được tạo", "review_id": new_review.id}


@router.get("/{username}/profile")
def get_user_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User không tồn tại")

    # Lấy feedback (review) của user
    reviews = db.query(Review).filter(Review.user_id == user.id).all()
    reviews_data = [
        {
            "id": r.id,
            "repair_shop_id": r.repair_shop_id,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat(),
        }
        for r in reviews
    ]

    # Lấy orders của user cùng dịch vụ và repair_shop
    orders = (
        db.query(Order, Service, RepairShop)
        .join(Service, Order.service_id == Service.id)
        .join(RepairShop, Order.repair_shop_id == RepairShop.id)
        .filter(Order.user_id == user.id)
        .all()
    )
    orders_data = []
    for order, service, repair_shop in orders:
        orders_data.append({
            "order_id": order.id,
            "status": order.status,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "scheduled_date": order.scheduled_date.isoformat() if order.scheduled_date else None,
            "completed_date": order.completed_date.isoformat() if order.completed_date else None,
            "service": {
                "id": service.id,
                "name": service.name,
                "description": service.description,
                "price": float(service.price),
                "duration": service.duration,
            },
            "repair_shop": {
                "id": repair_shop.id,
                "name": repair_shop.name,
                "address": repair_shop.address,
                "phone": repair_shop.phone,
            }
        })

    # Lấy các payment liên quan đến orders của user
    order_ids = [order.id for order, _, _ in orders]
    payments = db.query(Payment).filter(Payment.order_id.in_(order_ids)).all()
    payments_data = [
        {
            "payment_id": p.id,
            "order_id": p.order_id,
            "amount": float(p.amount),
            "payment_method": p.payment_method,
            "transaction_id": p.transaction_id,
            "status": p.status,
        }
        for p in payments
    ]

    # Trả về dữ liệu tổng hợp
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
        },
        "reviews": reviews_data,
        "orders": orders_data,
        "payments": payments_data,
    }
