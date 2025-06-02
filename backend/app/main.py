from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session # Import Session
from app.db.database import engine, Base, get_db # Import get_db
from app.db import models # Import models
from app.routes import auth, admin, repairshop, user

# 1. Khởi tạo database
Base.metadata.create_all(bind=engine)

# 2. Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="RideCare API",
    version="1.0.0",
    description="Hệ thống tìm kiếm và quản lý tiệm sửa xe"
)

# THÊM: Sự kiện startup để kiểm tra và tạo tài khoản admin
@app.on_event("startup")
async def startup_event():
    # Sử dụng SessionLocal trực tiếp để có thể tạo session trước khi ứng dụng khởi động hoàn toàn
    db: Session = next(get_db()) # Lấy một session từ generator
    try:
        # Kiểm tra xem có người dùng nào với vai trò 'admin' chưa
        admin_user = db.query(models.User).filter(models.User.role == "admin").first()

        if not admin_user:
            # Nếu chưa có admin, tạo một tài khoản admin mới
            new_admin = models.User(
                username="admin_ridecare", # Tên người dùng admin mặc định
                email="admin@ridecare.com", # Email admin mặc định
                password_hash="12345",      # Mật khẩu admin mặc định (RẤT KHÔNG AN TOÀN!)
                role="admin"
            )
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            print(">>> Tài khoản Admin mặc định 'admin_ridecare' đã được tạo <<<")
        else:
            print(">>> Tài khoản Admin đã tồn tại. Không tạo mới. <<<")
    except Exception as e:
        print(f"Lỗi khi kiểm tra/tạo tài khoản admin: {e}")
    finally:
        db.close()

# 3. CORS Middleware (cho phép frontend truy cập API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cân nhắc giới hạn lại khi triển khai
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Thiết lập template engine
templates = Jinja2Templates(directory="frontend")

# 6. Đăng ký routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(repairshop.router, prefix="/repairshop", tags=["Repair Shops"])

# 7. Route mặc định trả về trang chủ
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin/dashboard")
async def get_admin_dashboard(request: Request):
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})

@app.get("/admin/account_management")
async def get_admin_account_management(request: Request):
    return templates.TemplateResponse("admin/account_management.html", {"request": request})

@app.get("/admin/repairshop_management")
async def get_admin_repairshop_management(request: Request):
    return templates.TemplateResponse("admin/repairshop_management.html", {"request": request})

@app.get("/admin/service_management")
async def get_admin_service_management(request: Request):
    return templates.TemplateResponse("admin/service_management.html", {"request": request})

@app.get("/repairshop/dashboard")
async def get_repairshop_dashboard(request: Request):
    return templates.TemplateResponse("repairshop/dashboard.html", {"request": request})

@app.get("/repairshop/order_management")
async def get_repairshop_order_management(request: Request):
    return templates.TemplateResponse("repairshop/order_management.html", {"request": request})

@app.get("/repairshop/revenue")
async def get_repairshop_revenue(request: Request):
    return templates.TemplateResponse("repairshop/revenue.html", {"request": request})

@app.get("/repairshop/info")
async def get_repairshop_info(request: Request):
    return templates.TemplateResponse("repairshop/shop_info.html", {"request": request})

@app.get("/user/dashboard")
async def get_user_dashboard(request: Request):
    return templates.TemplateResponse("user/dashboard.html", {"request": request})
# 
@app.get("/user/booking")
async def booking(request: Request, shop_id: int = Query(...), service_ids: str = Query(...)):
    return templates.TemplateResponse("user/booking.html", {
        "request": request,
        "shop_id": shop_id,
        "service_ids": service_ids
    })

@app.get("/user/payment")
async def get_user_payment(request: Request):
    return templates.TemplateResponse("user/payment.html", {"request": request})

@app.get("/user/reviews")
async def get_user_reviews(request: Request):
    return templates.TemplateResponse("user/reviews.html", {"request": request})

@app.get("/user/search_shops")
async def get_user_search_shops(request: Request):
    return templates.TemplateResponse("user/search_shops.html", {"request": request})

@app.get("/user/shop_details/{shop_id}")
async def get_user_shop_details(request: Request):
    return templates.TemplateResponse("user/shop_details.html", {"request": request})

@app.get("/user/user_information")
async def get_user_information(request: Request):
    return templates.TemplateResponse("user/user_information.html", {"request": request})

@app.get("/login")
async def get_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup")
async def get_signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})
