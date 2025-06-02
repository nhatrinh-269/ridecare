from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, RepairShop, Service, Order, Review,Payment
from sqlalchemy import func

router = APIRouter()

@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    return {
        "total_users": db.query(User).count(),
        "total_shops": db.query(RepairShop).count(),
        "total_services": db.query(Service).count(),
        "total_orders": db.query(Order).count(),
        "orders_by_status": {
            "pending": db.query(Order).filter(Order.status == "pending").count(),
            "confirmed": db.query(Order).filter(Order.status == "confirmed").count(),
            "in_progress": db.query(Order).filter(Order.status == "in_progress").count(),
            "completed": db.query(Order).filter(Order.status == "completed").count(),
            "cancelled": db.query(Order).filter(Order.status == "cancelled").count(),
        },
        "revenue_by_method": {
            "credit_card": float(db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.payment_method == "credit_card", Payment.status == "completed").scalar()),
            "cash": float(db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.payment_method == "cash", Payment.status == "completed").scalar()),
            "ewallet": float(db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.payment_method == "ewallet", Payment.status == "completed").scalar()),
        }
    }
