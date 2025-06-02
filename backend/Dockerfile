# backend/Dockerfile

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Chỉ định cổng mà ứng dụng sẽ lắng nghe
EXPOSE 8000

# Lệnh để khởi động ứng dụng của bạn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]