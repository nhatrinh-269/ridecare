FROM python:3.9-slim

WORKDIR /app

# Copy toàn bộ mã nguồn backend
COPY . .

# Cài đặt các dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
