from sqlalchemy.orm import Session
from app.db import models
from decimal import Decimal # Để xử lý giá tiền chính xác
from datetime import datetime, timedelta
import random

# --- Hằng số và cấu hình ---
# (Trong thực tế, bạn có thể muốn tạo user với vai trò 'repair_shop' cụ thể hơn)
# Giả sử chúng ta sẽ tạo 5 chủ shop và phân bổ các shop cho họ
SHOP_OWNER_USERNAMES = ["shopowner1", "shopowner2", "shopowner3", "shopowner4", "shopowner5"]
NORMAL_USER_USERNAMES = ["user1", "user2", "user3", "user4", "user5", "user6", "user7", "user8", "user9", "user10"]

# Mật khẩu mẫu (KHÔNG DÙNG CHO PRODUCTION)
DEFAULT_PASSWORD_PLAIN = "string" 


def create_users(db: Session):
    print("Đang tạo người dùng mẫu...")
    users_to_create = []

    # 1. Admin user
    admin_user = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin_user:
        users_to_create.append(models.User(
            username="admin",
            email="admin@example.com",
            password_hash=DEFAULT_PASSWORD_PLAIN, # Cần băm trong thực tế
            role="admin"
        ))

    # 2. Shop owner users
    for i, username in enumerate(SHOP_OWNER_USERNAMES):
        if not db.query(models.User).filter(models.User.username == username).first():
            users_to_create.append(models.User(
                username=username,
                email=f"{username}@example.com",
                password_hash=DEFAULT_PASSWORD_PLAIN, # Cần băm
                role="repair_shop"
            ))
    
    # 3. Normal users
    for i, username in enumerate(NORMAL_USER_USERNAMES):
        if not db.query(models.User).filter(models.User.username == username).first():
            users_to_create.append(models.User(
                username=username,
                email=f"{username}@example.com",
                password_hash=DEFAULT_PASSWORD_PLAIN, # Cần băm
                role="user"
            ))

    if users_to_create:
        db.add_all(users_to_create)
        db.commit()
        print(f"Đã tạo {len(users_to_create)} người dùng mới.")
        for user in users_to_create:
            db.refresh(user) # Để lấy ID sau khi tạo
    else:
        print("Người dùng mẫu đã tồn tại.")
    
    # Trả về danh sách các user đã được tạo hoặc đã tồn tại để sử dụng sau này
    all_users = {
        "admin": db.query(models.User).filter(models.User.username == "admin").first(),
        "shop_owners": [db.query(models.User).filter(models.User.username == u).first() for u in SHOP_OWNER_USERNAMES],
        "normal_users": [db.query(models.User).filter(models.User.username == u).first() for u in NORMAL_USER_USERNAMES]
    }
    return all_users


def create_repair_shops(db: Session, shop_owners: list):
    print("Đang tạo cửa hàng mẫu...")
    if not shop_owners or all(owner is None for owner in shop_owners):
        print("Không có chủ sở hữu cửa hàng hợp lệ. Bỏ qua tạo cửa hàng.")
        return []

    # Dữ liệu cửa hàng bạn cung cấp
    shops_raw_data = [
        {"STT":1, "Tên tiệm sửa":"Sửa xe Tuấn", "Dịch vụ":"- Dịch vụ sửa chữa và bảo dưỡng xe máy tiêu chuẩn, bao gồm động cơ, phanh, và điện, thay lốp, bảo dưỡng định kỳ", "Longtitude - Kinh độ":108.2542723, "Latitude - vĩ độ":15.97729124, "Giờ hoạt động":"07:30–17:00", "Số điện thoại":"0906 485 248"},
        {"STT":2, "Tên tiệm sửa":"Tiệm Sửa Xe Chuyên Nghiệp Honda 69", "Dịch vụ":"- Dịch vụ sửa chữa, bảo dưỡng, và phụ tùng chính hãng cho xe Honda", "Longtitude - Kinh độ":108.254959, "Latitude - vĩ độ":15.97807513, "Giờ hoạt động":"07:00–18:00", "Số điện thoại":"0905 797 402"},
        {"STT":3, "Tên tiệm sửa":"Tiệm sửa xe Phước Hà", "Dịch vụ":"- Dịch vụ sửa chữa và bảo dưỡng xe máy tiêu chuẩn, bao gồm động cơ, phanh, và điện, thay lốp, bảo dưỡng định kỳ", "Longtitude - Kinh độ":108.2571048, "Latitude - vĩ độ":15.97910656, "Giờ hoạt động":"07:00–18:00", "Số điện thoại":"0766 664 452"},
        {"STT":4, "Tên tiệm sửa":"Tiệm Sửa Xe Sinh Sport", "Dịch vụ":"- Dịch vụ sửa chữa và bảo dưỡng xe máy tiêu chuẩn, bao gồm động cơ, phanh, và điện, thay lốp, bảo dưỡng định kỳ", "Longtitude - Kinh độ":108.2549161, "Latitude - vĩ độ":15.98030302, "Giờ hoạt động":"07:30–17:00", "Số điện thoại":"0786 268 616"},
        {"STT":5, "Tên tiệm sửa":"Tiệm Sửa Xe Thanh Thủy 2", "Dịch vụ":"- Dịch vụ sửa chữa và bảo dưỡng xe máy tiêu chuẩn, bao gồm động cơ, phanh, và điện, thay lốp, bảo dưỡng định kỳ", "Longtitude - Kinh độ":108.2545877, "Latitude - vĩ độ":15.97495109, "Giờ hoạt động":"07:30–17:00", "Số điện thoại":"0983 114 006"},
        {"STT":6, "Tên tiệm sửa":"Sửa Xe Cường", "Dịch vụ":"- Dịch vụ sửa chữa và bảo dưỡng xe máy tiêu chuẩn, bao gồm động cơ, phanh, và điện, thay lốp, bảo dưỡng định kỳ", "Longtitude - Kinh độ":108.2571048, "Latitude - vĩ độ":15.98232456, "Giờ hoạt động":"07:30–17:00", "Số điện thoại":"0934 702 433"},
        {"STT":7, "Tên tiệm sửa":"Sửa xe máy lưu động DNQN", "Dịch vụ":"- Dịch vụ sửa chữa và bảo dưỡng xe máy tiêu chuẩn, bao gồm động cơ, phanh, và điện, thay lốp, bảo dưỡng định kỳ", "Longtitude - Kinh độ":108.2359904, "Latitude - vĩ độ":15.9774356, "Giờ hoạt động":"Cả ngày", "Số điện thoại":"0796 737 005"},
        {"STT":8, "Tên tiệm sửa":"Sửa xe Bằng Anh", "Dịch vụ":"- Dịch vụ sửa chữa và bảo dưỡng xe máy tiêu chuẩn, bao gồm động cơ, phanh, và điện, thay lốp, bảo dưỡng định kỳ", "Longtitude - Kinh độ":108.2498521, "Latitude - vĩ độ":15.98121063, "Giờ hoạt động":"07:00–20:00", "Số điện thoại":"0798 999 259"},
        {"STT":9, "Tên tiệm sửa":"Tiệm sửa xe Hiền", "Dịch vụ":"- Dịch vụ sửa chữa và bảo dưỡng xe máy tiêu chuẩn, bao gồm động cơ, phanh, và điện, thay lốp, bảo dưỡng định kỳ", "Longtitude - Kinh độ":108.2397745, "Latitude - vĩ độ":15.98565645, "Giờ hoạt động":"07:00–19:00", "Số điện thoại":"0905 036 307"},
        {"STT":10, "Tên tiệm sửa":"Môtô Tuấn Nguyễn", "Dịch vụ":"- Dịch vụ sửa chữa và bảo dưỡng xe máy tiêu chuẩn, bao gồm động cơ, phanh, và điện, thay lốp, bảo dưỡng định kỳ", "Longtitude - Kinh độ":108.2596013, "Latitude - vĩ độ":15.99906415, "Giờ hoạt động":"07:00–18:30", "Số điện thoại":"0935 672 728"},
        {"STT":11, "Tên tiệm sửa":"Sửa Xe Máy lưu động", "Dịch vụ":"- Dịch vụ sửa chữa và bảo dưỡng xe máy tiêu chuẩn, bao gồm động cơ, phanh, và điện, thay lốp, bảo dưỡng định kỳ", "Longtitude - Kinh độ":108.238061, "Latitude - vĩ độ":15.9967433, "Giờ hoạt động":"07:30–17:00", "Số điện thoại":"0905 134 083"},
        {"STT":12, "Tên tiệm sửa":"Cửa hàng sửa chữa xe máy - Quang Huỳnh", "Dịch vụ":"- Dịch vụ sửa chữa và bảo dưỡng xe máy tiêu chuẩn, bao gồm động cơ, phanh, và điện, thay lốp, bảo dưỡng định kỳ", "Longtitude - Kinh độ":108.2555541, "Latitude - vĩ độ":16.01548178, "Giờ hoạt động":"07:00–20:00", "Số điện thoại":"0935 973 399"},
        {"STT":13, "Tên tiệm sửa":"Tiệm Sửa Xe Tiến Dũng", "Dịch vụ":"- Dịch vụ sửa chữa và bảo dưỡng xe máy tiêu chuẩn, bao gồm động cơ, phanh, và điện, thay lốp, bảo dưỡng định kỳ", "Longtitude - Kinh độ":108.2078379, "Latitude - vĩ độ":15.9862233, "Giờ hoạt động":"06:00–18:00", "Số điện thoại":"0986 800 603"}
    ]

    shops_to_create = []
    owner_idx = 0
    for data in shops_raw_data:
        if not db.query(models.RepairShop).filter(models.RepairShop.name == data["Tên tiệm sửa"]).first():
            # Đảm bảo có đủ chủ shop, nếu không sẽ lặp lại từ đầu danh sách chủ shop
            current_owner = shop_owners[owner_idx % len(shop_owners)] if shop_owners else None
            if not current_owner: 
                print(f"Không có chủ sở hữu hợp lệ để gán cho shop {data['Tên tiệm sửa']}, bỏ qua.")
                continue

            description_with_hours = f"{data['Dịch vụ']}. Giờ hoạt động: {data['Giờ hoạt động']}"
            
            shops_to_create.append(models.RepairShop(
                user_id=current_owner.id,
                name=data["Tên tiệm sửa"],
                address=f"Địa chỉ của {data['Tên tiệm sửa']}, Khu vực {current_owner.username}", 
                phone=data["Số điện thoại"],
                description=description_with_hours,
                approved=True, 
                rating_avg=round(random.uniform(3.5, 5.0), 1), 
                latitude=data["Latitude - vĩ độ"],
                longitude=data["Longtitude - Kinh độ"]
            ))
            owner_idx += 1
            
    if shops_to_create:
        db.add_all(shops_to_create)
        db.commit()
        print(f"Đã tạo {len(shops_to_create)} cửa hàng mới.")
        for shop in shops_to_create:
            db.refresh(shop)
    else:
        print("Các cửa hàng mẫu đã tồn tại hoặc không có chủ sở hữu hợp lệ.")
    
    return db.query(models.RepairShop).all()


def create_services(db: Session, shops: list):
    print("Đang tạo dịch vụ mẫu...")
    if not shops:
        print("Không có cửa hàng để tạo dịch vụ. Bỏ qua.")
        return []

    services_to_create = []
    common_services_data = [
        {"name": "Thay nhớt tổng hợp cao cấp", "description": "Sử dụng nhớt tổng hợp chất lượng cao cho hiệu suất tối ưu.", "price": Decimal("250000.00"), "duration": 30, "is_available": True},
        {"name": "Kiểm tra và bảo dưỡng hệ thống phanh", "description": "Kiểm tra, làm sạch và căn chỉnh hệ thống phanh trước và sau.", "price": Decimal("120000.00"), "duration": 60, "is_available": True},
        {"name": "Rửa xe và làm bóng dàn áo", "description": "Rửa xe kỹ lưỡng, làm sạch chi tiết và phủ bóng bảo vệ sơn.", "price": Decimal("100000.00"), "duration": 60, "is_available": random.choice([True, False])},
        {"name": "Bảo dưỡng định kỳ toàn diện", "description": "Kiểm tra tổng thể các hạng mục theo khuyến cáo nhà sản xuất, bao gồm lọc gió, bugi.", "price": Decimal("450000.00"), "duration": 150, "is_available": True},
        {"name": "Vá lốp/săm không ruột", "description": "Vá nhanh các loại lốp xe máy, đảm bảo an toàn.", "price": Decimal("30000.00"), "duration": 20, "is_available": True},
        {"name": "Thay thế phụ tùng (bugi, lọc gió)", "description": "Thay thế bugi, lọc gió chính hãng hoặc tương đương.", "price": Decimal("180000.00"), "duration": 40, "is_available": True},
    ]

    for shop in shops:
        if db.query(models.Service).filter(models.Service.repair_shop_id == shop.id).count() == 0:
            # Thêm tất cả các dịch vụ phổ biến cho mỗi shop
            for service_data in common_services_data:
                services_to_create.append(models.Service(
                    repair_shop_id=shop.id,
                    **service_data
                ))
    
    if services_to_create:
        db.add_all(services_to_create)
        db.commit()
        print(f"Đã tạo {len(services_to_create)} dịch vụ mới.")
        for service in services_to_create:
            db.refresh(service)
    else:
        print("Dịch vụ mẫu đã tồn tại hoặc không có shop mới để thêm dịch vụ.")
    return db.query(models.Service).all()

def create_orders_and_payments(db: Session, normal_users: list, services: list, shops: list):
    print("Đang tạo đơn hàng và thanh toán mẫu...")
    if not normal_users or not services or not shops:
        print("Thiếu người dùng, dịch vụ hoặc cửa hàng để tạo đơn hàng. Bỏ qua.")
        return [], []

    orders_to_create = []
    payments_to_create = []
    
    # Tạo khoảng 30-50 đơn hàng mẫu
    for _ in range(random.randint(30, 50)):
        user = random.choice(normal_users)
        # Chọn một shop ngẫu nhiên, sau đó chọn một dịch vụ của shop đó
        shop = random.choice(shops)
        shop_services = [s for s in services if s.repair_shop_id == shop.id]
        if not shop_services:
            continue # Shop này không có dịch vụ nào được tạo
        service = random.choice(shop_services)

        if user and service and shop: # Đảm bảo tất cả đều hợp lệ
            order_status = random.choice([s.value for s in models.OrderStatus.__members__.values()])
            scheduled_datetime = datetime.utcnow() + timedelta(days=random.randint(1, 14), hours=random.randint(0,23), minutes=random.choice([0, 15, 30, 45]))
            
            order_data = {
                "user_id": user.id,
                "service_id": service.id,
                "repair_shop_id": shop.id,
                "status": order_status,
                "order_date": datetime.utcnow() - timedelta(days=random.randint(0, 60), hours=random.randint(0,23)),
                "scheduled_date": scheduled_datetime if order_status not in ["completed", "cancelled"] else None,
                "completed_date": scheduled_datetime + timedelta(hours=service.duration // 60, minutes=service.duration % 60 + random.randint(5,30)) if order_status == "completed" else None
            }
            new_order = models.Order(**order_data)
            orders_to_create.append(new_order)
            
    if orders_to_create:
        db.add_all(orders_to_create)
        db.commit() 
        print(f"Đã tạo {len(orders_to_create)} đơn hàng mới.")
        for order in orders_to_create:
            db.refresh(order)
            # Lấy lại service object để có giá chính xác (nếu service được refresh)
            service_for_payment = db.query(models.Service).filter(models.Service.id == order.service_id).first()
            if not service_for_payment: continue

            if order.status not in ["pending", "cancelled"] or random.choice([True, False, False]): 
                payment_data = {
                    "order_id": order.id,
                    "amount": service_for_payment.price, 
                    "payment_method": random.choice([pm.value for pm in models.PaymentMethod.__members__.values()]),
                    "transaction_id": f"RIDECARE-{order.id}-{random.randint(10000,99999)}",
                    "status": "completed" if order.status == "completed" else random.choice(["pending", "completed", "failed"])
                }
                new_payment = models.Payment(**payment_data)
                payments_to_create.append(new_payment)
        
        if payments_to_create:
            db.add_all(payments_to_create)
            db.commit()
            print(f"Đã tạo {len(payments_to_create)} thanh toán mới.")
            for payment in payments_to_create:
                db.refresh(payment)
    else:
        print("Không có đơn hàng nào được tạo để thêm thanh toán.")
        
    return db.query(models.Order).all(), db.query(models.Payment).all()


def create_reviews(db: Session, normal_users: list, shops: list):
    print("Đang tạo đánh giá mẫu...")
    if not normal_users or not shops:
        print("Thiếu người dùng hoặc cửa hàng để tạo đánh giá. Bỏ qua.")
        return

    reviews_to_create = []
    # Tạo khoảng 40-60 reviews
    for _ in range(random.randint(40, 60)):
        user = random.choice(normal_users)
        shop = random.choice(shops)
        
        existing_review = db.query(models.Review).filter(
            models.Review.user_id == user.id,
            models.Review.repair_shop_id == shop.id
        ).first()

        if user and shop and not existing_review:
            review_data = {
                "user_id": user.id,
                "repair_shop_id": shop.id,
                "rating": random.randint(1, 5),
                "comment": random.choice([
                    "Dịch vụ tuyệt vời, nhân viên rất chuyên nghiệp và thân thiện. Sẽ giới thiệu cho bạn bè!",
                    "Sửa xe nhanh chóng, giá cả hợp lý. Tôi rất hài lòng.",
                    "Chất lượng dịch vụ tốt, nhưng thời gian chờ hơi lâu một chút.",
                    "Cần cải thiện thêm về không gian phòng chờ cho khách.",
                    "Chắc chắn sẽ quay lại đây vào lần bảo dưỡng xe tiếp theo.",
                    None, 
                    "Địa điểm dễ tìm, cửa hàng sạch sẽ và gọn gàng. Nhân viên tư vấn nhiệt tình.",
                    "Phụ tùng thay thế có vẻ chất lượng, xe chạy êm hơn hẳn.",
                    "Giá hơi cao hơn so với một số nơi khác nhưng đáng tiền.",
                    "Thợ tay nghề cao, bắt bệnh xe chính xác."
                ]),
                "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 90))
            }
            reviews_to_create.append(models.Review(**review_data))

    if reviews_to_create:
        db.add_all(reviews_to_create)
        db.commit()
        print(f"Đã tạo {len(reviews_to_create)} đánh giá mới.")
        for review in reviews_to_create:
            db.refresh(review)
        
        shop_ids_with_new_reviews = list(set([r.repair_shop_id for r in reviews_to_create]))
        for shop_id_to_update in shop_ids_with_new_reviews:
            shop_to_update = db.query(models.RepairShop).filter(models.RepairShop.id == shop_id_to_update).first()
            if shop_to_update:
                avg_rating_query = db.query(models.func.avg(models.Review.rating)).filter(models.Review.repair_shop_id == shop_id_to_update)
                avg_rating = avg_rating_query.scalar()
                shop_to_update.rating_avg = round(avg_rating, 2) if avg_rating is not None else 0.0
        db.commit()
        print("Đã cập nhật rating trung bình cho các cửa hàng có đánh giá mới.")
    else:
        print("Không có đánh giá mới nào được tạo (có thể do đã tồn tại).")


# --- Hàm chính để gọi tất cả ---
def create_initial_data(db: Session):
    print("Bắt đầu quá trình tạo dữ liệu mẫu...")
    
    # Bước 1: Tạo Users
    users_dict = create_users(db)
    
    # Bước 2: Tạo RepairShops
    valid_shop_owners = [owner for owner in users_dict.get("shop_owners", []) if owner and owner.role == "repair_shop"]
    if not valid_shop_owners and users_dict.get("admin"):
         admin_user = users_dict["admin"]
         if admin_user and admin_user.role == "admin": 
            print("Không có chủ shop_owner, sử dụng admin làm chủ shop mẫu.")
            valid_shop_owners = [admin_user]

    all_shops = create_repair_shops(db, valid_shop_owners)
    
    # Bước 3: Tạo Services
    all_services = create_services(db, all_shops)
    
    # Bước 4: Tạo Orders và Payments
    valid_normal_users = [user for user in users_dict.get("normal_users", []) if user and user.role == "user"]
    # Đảm bảo all_services và all_shops không rỗng trước khi truyền vào
    if valid_normal_users and all_services and all_shops:
        create_orders_and_payments(db, valid_normal_users, all_services, all_shops)
    else:
        print("Bỏ qua tạo Orders/Payments do thiếu Users, Services hoặc Shops.")
    
    # Bước 5: Tạo Reviews
    if valid_normal_users and all_shops:
        create_reviews(db, valid_normal_users, all_shops)
    else:
        print("Bỏ qua tạo Reviews do thiếu Users hoặc Shops.")
        
    print("Hoàn tất quá trình tạo dữ liệu mẫu.")
