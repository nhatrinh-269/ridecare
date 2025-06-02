# backend/app/main.py

from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # <-- Import dòng này
from fastapi.templating import Jinja2Templates

from app.db.database import engine, Base
from app.routes import auth, admin, repairshop, user

# 1. Khởi tạo database
Base.metadata.create_all(bind=engine)

# 2. Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="RideCare API",
    version="1.0.0",
    description="Hệ thống tìm kiếm và quản lý tiệm sửa xe"
)

# 3. CORS Middleware (cho phép frontend truy cập API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Thêm phần này để phục vụ các file tĩnh (CSS, JS, images, v.v.) ---
# Giả sử các file tĩnh của bạn nằm trong thư mục 'backend/frontend/static'
# URL sẽ là /static/<tên_file_cua_ban>
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
# --------------------------------------------------------------------

# 5. Thiết lập template engine
# Đảm bảo đường dẫn này đúng với vị trí thư mục 'frontend' bên trong 'backend'
templates = Jinja2Templates(directory="frontend")

# 6. Đăng ký routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(repairshop.router, prefix="/repairshop", tags=["Repair Shops"])

# 7. Các routes trả về trang HTML của bạn (không thay đổi)
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