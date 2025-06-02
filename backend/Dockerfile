FROM python:3.9-slim

WORKDIR /app

# Copy file requirements.txt từ thư mục backend
COPY ./backend/requirements.txt requirements.txt

# Cài đặt các dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn backend
COPY ./backend/ .

# Copy thư mục frontend
COPY ../frontend /app/frontend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
