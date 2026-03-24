FROM python:3.12-slim

# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install Postgres dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 1. Copy requirements from your Windows root to Docker /app/
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 2. Copy EVERYTHING from E:\Ecomm into Docker /app/
COPY . /app/

EXPOSE 8000

# 3. Use 'sh' to enter the ecom folder and then run the server
CMD ["sh", "-c", "python ecom/manage.py runserver 0.0.0.0:8000"]