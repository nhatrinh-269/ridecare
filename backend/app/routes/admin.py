from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func # For your existing stats endpoint
from typing import List, Optional

# Assuming your project structure allows these imports:
from app.db.database import get_db
from app.db import models # e.g., from app.db.models import User, RepairShop, Service, Order, Payment, Review
# Import your Pydantic schemas (adjust path if you put them in a separate admin_schemas.py)
from app.db import schemas # e.g., schemas.UserOut, schemas.UserCreate, schemas.UserUpdateAdmin, etc.

# Password Hashing (passlib) has been REMOVED as per request.
# def get_password_hash(password: str):
#     return pwd_context.hash(password)

# Your existing router instance
router = APIRouter()

# --- Helper function for 404 ---
def get_model_or_404(db: Session, model_class, model_id: int):
    instance = db.query(model_class).filter(model_class.id == model_id).first()
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model_class.__name__} with id {model_id} not found")
    return instance

# --- Your Existing Stats Endpoint ---
@router.get("/stats", summary="Get Admin Dashboard Statistics")
def get_admin_stats(db: Session = Depends(get_db)):
    return {
        "total_users": db.query(models.User).count(),
        "total_shops": db.query(models.RepairShop).count(),
        "total_services": db.query(models.Service).count(),
        "total_orders": db.query(models.Order).count(),
        "orders_by_status": {
            # Assuming status_enum is the string value directly if .type.enums returns strings
            status_enum: db.query(models.Order).filter(models.Order.status == status_enum).count()
            for status_enum in models.Order.status.type.enums
        },
        "revenue_by_method": {
            # Assuming method_enum is the string value directly
            method_enum: float(db.query(func.coalesce(func.sum(models.Payment.amount), 0.0)).filter(models.Payment.payment_method == method_enum, models.Payment.status == "completed").scalar())
            for method_enum in models.Payment.payment_method.type.enums
        }
    }

# --- Manage Users ---
@router.post("/users/", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED, summary="Admin: Create User")
def admin_create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Store password as plain text - NOT RECOMMENDED FOR PRODUCTION
    plain_password = user.password
    # The 'password' field from UserCreate schema is used directly.
    # Ensure your User model's 'password_hash' column can store it or rename it to 'password'.
    # For this example, we assume the model's field is 'password_hash' but will store plain text.
    db_user_data = user.model_dump(exclude={"password"})
    db_user_data["password_hash"] = plain_password # Storing plain text in password_hash column

    db_user = models.User(**db_user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/", response_model=List[schemas.UserOut], summary="Admin: List Users")
def admin_list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id}", response_model=schemas.UserOut, summary="Admin: Get User by ID")
def admin_get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = get_model_or_404(db, models.User, user_id)
    return db_user

@router.put("/users/{user_id}", response_model=schemas.UserOut, summary="Admin: Update User")
def admin_update_user(user_id: int, user_update: schemas.UserUpdateAdmin, db: Session = Depends(get_db)):
    db_user = get_model_or_404(db, models.User, user_id)

    update_data = user_update.model_dump(exclude_unset=True)

    if "username" in update_data and update_data["username"] != db_user.username:
        if db.query(models.User).filter(models.User.username == update_data["username"]).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    if "email" in update_data and update_data["email"] != db_user.email:
        if db.query(models.User).filter(models.User.email == update_data["email"]).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken")
    
    # Admin password update is not handled here if passwords are plain text.
    # If you need to update plain text passwords, you would add a 'password' field to UserUpdateAdmin
    # and handle it similarly to the create endpoint. However, this is generally avoided.

    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Admin: Delete User")
def admin_delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = get_model_or_404(db, models.User, user_id)
    db.delete(db_user)
    db.commit()
    return

# --- Manage Repair Shops ---
@router.post("/repair-shops/", response_model=schemas.RepairShopOut, status_code=status.HTTP_201_CREATED, summary="Admin: Create Repair Shop")
def admin_create_repair_shop(shop: schemas.RepairShopCreateAdmin, db: Session = Depends(get_db)):
    owner = get_model_or_404(db, models.User, shop.user_id)
    if owner.role != "repair_shop":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User ID {shop.user_id} is not a repair_shop role or does not exist.")
    existing_shop = db.query(models.RepairShop).filter(models.RepairShop.user_id == shop.user_id).first()
    if existing_shop:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User ID {shop.user_id} already owns a repair shop.")

    db_shop = models.RepairShop(**shop.model_dump())
    db.add(db_shop)
    db.commit()
    db.refresh(db_shop)
    return db_shop

@router.get("/repair-shops/", response_model=List[schemas.RepairShopOut], summary="Admin: List Repair Shops")
def admin_list_repair_shops(
    skip: int = 0, limit: int = 100,
    approved: Optional[bool] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.RepairShop)
    if approved is not None:
        query = query.filter(models.RepairShop.approved == approved)
    if user_id is not None:
        query = query.filter(models.RepairShop.user_id == user_id)
    shops = query.offset(skip).limit(limit).all()
    return shops

@router.get("/repair-shops/{shop_id}", response_model=schemas.RepairShopOut, summary="Admin: Get Repair Shop by ID")
def admin_get_repair_shop(shop_id: int, db: Session = Depends(get_db)):
    db_shop = get_model_or_404(db, models.RepairShop, shop_id)
    return db_shop

@router.put("/repair-shops/{shop_id}", response_model=schemas.RepairShopOut, summary="Admin: Update Repair Shop")
def admin_update_repair_shop(shop_id: int, shop_update: schemas.RepairShopUpdateAdmin, db: Session = Depends(get_db)):
    db_shop = get_model_or_404(db, models.RepairShop, shop_id)
    update_data = shop_update.model_dump(exclude_unset=True)

    if "user_id" in update_data and update_data["user_id"] != db_shop.user_id:
        new_owner = get_model_or_404(db, models.User, update_data["user_id"])
        if new_owner.role != "repair_shop":
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"New owner User ID {update_data['user_id']} is not a repair_shop role.")
        existing_shop_for_new_owner = db.query(models.RepairShop).filter(models.RepairShop.user_id == update_data["user_id"]).first()
        if existing_shop_for_new_owner:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"New owner User ID {update_data['user_id']} already owns another shop.")

    for field, value in update_data.items():
        setattr(db_shop, field, value)

    db.commit()
    db.refresh(db_shop)
    return db_shop

@router.delete("/repair-shops/{shop_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Admin: Delete Repair Shop")
def admin_delete_repair_shop(shop_id: int, db: Session = Depends(get_db)):
    db_shop = get_model_or_404(db, models.RepairShop, shop_id)
    db.delete(db_shop)
    db.commit()
    return

# --- Manage Services ---
@router.post("/services/", response_model=schemas.ServiceOut, status_code=status.HTTP_201_CREATED, summary="Admin: Create Service")
def admin_create_service(service: schemas.ServiceCreateAdmin, db: Session = Depends(get_db)):
    get_model_or_404(db, models.RepairShop, service.repair_shop_id) # Ensure shop exists
    db_service = models.Service(**service.model_dump())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@router.get("/services/", response_model=List[schemas.ServiceOut], summary="Admin: List Services")
def admin_list_services(
    skip: int = 0, limit: int = 100,
    repair_shop_id: Optional[int] = None,
    is_available: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Service)
    if repair_shop_id is not None:
        query = query.filter(models.Service.repair_shop_id == repair_shop_id)
    if is_available is not None:
        query = query.filter(models.Service.is_available == is_available)
    services = query.offset(skip).limit(limit).all()
    return services

@router.get("/services/{service_id}", response_model=schemas.ServiceOut, summary="Admin: Get Service by ID")
def admin_get_service(service_id: int, db: Session = Depends(get_db)):
    db_service = get_model_or_404(db, models.Service, service_id)
    return db_service

@router.put("/services/{service_id}", response_model=schemas.ServiceOut, summary="Admin: Update Service")
def admin_update_service(service_id: int, service_update: schemas.ServiceUpdateAdmin, db: Session = Depends(get_db)):
    db_service = get_model_or_404(db, models.Service, service_id)
    update_data = service_update.model_dump(exclude_unset=True)

    if "repair_shop_id" in update_data and update_data["repair_shop_id"] != db_service.repair_shop_id:
        get_model_or_404(db, models.RepairShop, update_data["repair_shop_id"])

    for field, value in update_data.items():
        setattr(db_service, field, value)

    db.commit()
    db.refresh(db_service)
    return db_service

@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Admin: Delete Service")
def admin_delete_service(service_id: int, db: Session = Depends(get_db)):
    db_service = get_model_or_404(db, models.Service, service_id)
    db.delete(db_service)
    db.commit()
    return

# --- Manage Orders ---
@router.post("/orders/", response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED, summary="Admin: Create Order")
def admin_create_order(order: schemas.OrderCreateAdmin, db: Session = Depends(get_db)):
    get_model_or_404(db, models.User, order.user_id)
    get_model_or_404(db, models.Service, order.service_id)
    get_model_or_404(db, models.RepairShop, order.repair_shop_id)
    service_check = db.query(models.Service).filter(models.Service.id == order.service_id, models.Service.repair_shop_id == order.repair_shop_id).first()
    if not service_check:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Service ID {order.service_id} does not belong to Repair Shop ID {order.repair_shop_id}")

    db_order = models.Order(**order.model_dump())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.get("/orders/", response_model=List[schemas.OrderOut], summary="Admin: List Orders")
def admin_list_orders(
    skip: int = 0, limit: int = 100,
    user_id: Optional[int] = None,
    repair_shop_id: Optional[int] = None,
    status: Optional[str] = Query(None, enum=[s for s in models.Order.status.type.enums]), # Corrected: s is already the value
    db: Session = Depends(get_db)
):
    query = db.query(models.Order)
    if user_id is not None:
        query = query.filter(models.Order.user_id == user_id)
    if repair_shop_id is not None:
        query = query.filter(models.Order.repair_shop_id == repair_shop_id)
    if status is not None:
        query = query.filter(models.Order.status == status)
    orders = query.order_by(models.Order.order_date.desc()).offset(skip).limit(limit).all()
    return orders

@router.get("/orders/{order_id}", response_model=schemas.OrderOut, summary="Admin: Get Order by ID")
def admin_get_order(order_id: int, db: Session = Depends(get_db)):
    db_order = get_model_or_404(db, models.Order, order_id)
    return db_order

@router.put("/orders/{order_id}", response_model=schemas.OrderOut, summary="Admin: Update Order")
def admin_update_order(order_id: int, order_update: schemas.OrderUpdateAdmin, db: Session = Depends(get_db)):
    db_order = get_model_or_404(db, models.Order, order_id)
    update_data = order_update.model_dump(exclude_unset=True)

    if "user_id" in update_data and update_data["user_id"] != db_order.user_id:
        get_model_or_404(db, models.User, update_data["user_id"])
    if "service_id" in update_data and update_data["service_id"] != db_order.service_id:
        get_model_or_404(db, models.Service, update_data["service_id"])
    if "repair_shop_id" in update_data and update_data["repair_shop_id"] != db_order.repair_shop_id:
        get_model_or_404(db, models.RepairShop, update_data["repair_shop_id"])
    
    new_service_id = update_data.get("service_id", db_order.service_id)
    new_repair_shop_id = update_data.get("repair_shop_id", db_order.repair_shop_id)
    if "service_id" in update_data or "repair_shop_id" in update_data:
        service_check = db.query(models.Service).filter(models.Service.id == new_service_id, models.Service.repair_shop_id == new_repair_shop_id).first()
        if not service_check:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Service ID {new_service_id} does not belong to Repair Shop ID {new_repair_shop_id}")

    for field, value in update_data.items():
        setattr(db_order, field, value)

    db.commit()
    db.refresh(db_order)
    return db_order

@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Admin: Delete Order")
def admin_delete_order(order_id: int, db: Session = Depends(get_db)):
    db_order = get_model_or_404(db, models.Order, order_id)
    db.delete(db_order)
    db.commit()
    return

# --- Manage Payments ---
@router.post("/payments/", response_model=schemas.PaymentOut, status_code=status.HTTP_201_CREATED, summary="Admin: Create Payment")
def admin_create_payment(payment: schemas.PaymentCreateAdmin, db: Session = Depends(get_db)):
    get_model_or_404(db, models.Order, payment.order_id)
    existing_payment = db.query(models.Payment).filter(models.Payment.order_id == payment.order_id).first()
    if existing_payment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Order ID {payment.order_id} already has a payment.")

    db_payment = models.Payment(**payment.model_dump())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.get("/payments/", response_model=List[schemas.PaymentOut], summary="Admin: List Payments")
def admin_list_payments(
    skip: int = 0, limit: int = 100,
    order_id: Optional[int] = None,
    payment_method: Optional[str] = Query(None, enum=[pm for pm in models.Payment.payment_method.type.enums]), # Corrected: pm is already the value
    status: Optional[str] = Query(None, enum=[ps for ps in models.Payment.status.type.enums]), # Corrected: ps is already the value
    db: Session = Depends(get_db)
):
    query = db.query(models.Payment)
    if order_id is not None:
        query = query.filter(models.Payment.order_id == order_id)
    if payment_method is not None:
        query = query.filter(models.Payment.payment_method == payment_method)
    if status is not None:
        query = query.filter(models.Payment.status == status)
    payments = query.offset(skip).limit(limit).all()
    return payments

@router.get("/payments/{payment_id}", response_model=schemas.PaymentOut, summary="Admin: Get Payment by ID")
def admin_get_payment(payment_id: int, db: Session = Depends(get_db)):
    db_payment = get_model_or_404(db, models.Payment, payment_id)
    return db_payment

@router.put("/payments/{payment_id}", response_model=schemas.PaymentOut, summary="Admin: Update Payment")
def admin_update_payment(payment_id: int, payment_update: schemas.PaymentUpdateAdmin, db: Session = Depends(get_db)):
    db_payment = get_model_or_404(db, models.Payment, payment_id)
    update_data = payment_update.model_dump(exclude_unset=True)

    if "order_id" in update_data and update_data["order_id"] != db_payment.order_id:
        get_model_or_404(db, models.Order, update_data["order_id"])
        existing_payment = db.query(models.Payment).filter(models.Payment.order_id == update_data["order_id"], models.Payment.id != payment_id).first()
        if existing_payment:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"The new Order ID {update_data['order_id']} already has an associated payment.")

    for field, value in update_data.items():
        setattr(db_payment, field, value)

    db.commit()
    db.refresh(db_payment)
    return db_payment

@router.delete("/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Admin: Delete Payment")
def admin_delete_payment(payment_id: int, db: Session = Depends(get_db)):
    db_payment = get_model_or_404(db, models.Payment, payment_id)
    db.delete(db_payment)
    db.commit()
    return

# --- Manage Reviews (Optional, if Admin needs to moderate) ---
@router.get("/reviews/", response_model=List[schemas.ReviewOut], summary="Admin: List Reviews")
def admin_list_reviews(
    skip: int = 0, limit: int = 100,
    user_id: Optional[int] = None,
    repair_shop_id: Optional[int] = None,
    rating: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Review)
    if user_id is not None:
        query = query.filter(models.Review.user_id == user_id)
    if repair_shop_id is not None:
        query = query.filter(models.Review.repair_shop_id == repair_shop_id)
    if rating is not None:
        query = query.filter(models.Review.rating == rating)
    reviews = query.order_by(models.Review.created_at.desc()).offset(skip).limit(limit).all()
    return reviews

@router.get("/reviews/{review_id}", response_model=schemas.ReviewOut, summary="Admin: Get Review by ID")
def admin_get_review(review_id: int, db: Session = Depends(get_db)):
    db_review = get_model_or_404(db, models.Review, review_id)
    return db_review

@router.put("/reviews/{review_id}", response_model=schemas.ReviewOut, summary="Admin: Update Review (e.g., moderate comment)")
def admin_update_review(review_id: int, review_update: schemas.ReviewUpdateAdmin, db: Session = Depends(get_db)):
    db_review = get_model_or_404(db, models.Review, review_id)
    update_data = review_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_review, field, value)
    db.commit()
    db.refresh(db_review)
    return db_review

@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Admin: Delete Review")
def admin_delete_review(review_id: int, db: Session = Depends(get_db)):
    db_review = get_model_or_404(db, models.Review, review_id)
    db.delete(db_review)
    db.commit()
    return
