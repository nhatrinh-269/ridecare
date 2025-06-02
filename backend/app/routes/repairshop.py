from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, RepairShop, Order, Payment, Review

router = APIRouter()

class UsernameRequest(BaseModel):
    username: str

@router.post("/stats")
def get_repairshop_stats(data: UsernameRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=data.username, role="repair_shop").first()
    if not user or not user.repair_shop:
        raise HTTPException(status_code=404, detail="Repair shop not found")

    shop = user.repair_shop

    orders = db.query(Order).filter_by(repair_shop_id=shop.id).all()
    payments = db.query(Payment).join(Order).filter(Order.repair_shop_id == shop.id).all()
    reviews = db.query(Review).filter_by(repair_shop_id=shop.id).all()

    # Đếm theo trạng thái
    status_counts = {
        "pending": sum(1 for o in orders if o.status == "pending"),
        "confirmed": sum(1 for o in orders if o.status == "confirmed"),
        "in_progress": sum(1 for o in orders if o.status == "in_progress"),
        "completed": sum(1 for o in orders if o.status == "completed"),
        "cancelled": sum(1 for o in orders if o.status == "cancelled")
    }

    # Doanh thu theo phương thức
    revenue_by_method = {
        "credit_card": sum(p.amount for p in payments if p.payment_method == "credit_card" and p.status == "completed"),
        "cash": sum(p.amount for p in payments if p.payment_method == "cash" and p.status == "completed"),
        "ewallet": sum(p.amount for p in payments if p.payment_method == "ewallet" and p.status == "completed")
    }

    return {
        "total_orders": len(orders),
        "total_revenue": sum(p.amount for p in payments if p.status == "completed"),
        "avg_rating": sum(r.rating for r in reviews) / len(reviews) if reviews else 0.0,
        "status_counts": status_counts,
        "revenue_by_method": revenue_by_method
    }
