from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Bạn có thể cần nếu dùng StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager # <<< THÊM IMPORT NÀY

# Giả sử SessionLocal được định nghĩa trong database.py để tạo session
from app.db.database import engine, Base, SessionLocal # <<< THÊM SessionLocal
from app.routes import auth, admin, repairshop, user
from app.db.init_db import create_initial_data # <<< THÊM IMPORT NÀY

# Hàm lifespan để xử lý sự kiện khởi động và tắt ứng dụng
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code thực thi khi ứng dụng khởi động
    print("Ứng dụng đang khởi động...")
    print("Đang tạo các bảng trong cơ sở dữ liệu (nếu chưa có)...")
    Base.metadata.create_all(bind=engine) # Tạo bảng nếu chưa tồn tại

    # Tạo dữ liệu mẫu
    print("Đang khởi tạo dữ liệu mẫu...")
    db = SessionLocal()
    try:
        create_initial_data(db)
        print("Hoàn tất tạo dữ liệu mẫu.")
    except Exception as e:
        print(f"Lỗi khi tạo dữ liệu mẫu: {e}")
    finally:
        db.close()
    
    yield # Đây là điểm ứng dụng sẽ chạy
    
    # Code thực thi khi ứng dụng tắt (nếu cần)
    print("Ứng dụng đang tắt...")

# Hàm lifespan để xử lý sự kiện khởi động và tắt ứng dụng
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code thực thi khi ứng dụng khởi động
    print("Ứng dụng đang khởi động...")
    print("Đang tạo các bảng trong cơ sở dữ liệu (nếu chưa có)...")
    Base.metadata.create_all(bind=engine) # Tạo bảng nếu chưa tồn tại

    # Tạo dữ liệu mẫu
    print("Đang khởi tạo dữ liệu mẫu...")
    db = SessionLocal()
    try:
        create_initial_data(db)
        print("Hoàn tất tạo dữ liệu mẫu.")
    except Exception as e:
        print(f"Lỗi khi tạo dữ liệu mẫu: {e}")
    finally:
        db.close()
    
    yield # Đây là điểm ứng dụng sẽ chạy
    
    # Code thực thi khi ứng dụng tắt (nếu cần)
    print("Ứng dụng đang tắt...")

# 2. Khởi tạo ứng dụng FastAPI với lifespan
app = FastAPI(
    title="RideCare API",
    version="1.0.0",
    description="Hệ thống tìm kiếm và quản lý tiệm sửa xe",
    lifespan=lifespan # <<< THÊM THAM SỐ NÀY
)

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
