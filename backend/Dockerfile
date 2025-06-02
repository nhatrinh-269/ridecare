# backend/Dockerfile (ở thư mục backend/)

# Sử dụng image Python cơ bản
FROM python:3.9-slim 

# Đặt thư mục làm việc trong container
WORKDIR /app

# Sao chép tất cả nội dung từ thư mục 'backend' (đây là context build) vào '/app'
# Điều này sẽ bao gồm cả thư mục 'frontend' mà bạn đã di chuyển vào 'backend'
COPY . .

# Cài đặt các dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Mở cổng mà ứng dụng của bạn lắng nghe
EXPOSE 8000

# Lệnh để chạy ứng dụng của bạn (Render Start Command sẽ ghi đè cái này)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]