FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=TKI/app_web.py
ENV PORT=5000

WORKDIR /app

# Install system dependencies (required for psycopg2 and standard C bindings)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (Railway dynamically assigns PORT, but default is 5000)
EXPOSE 5000

# Run gunicorn server
CMD gunicorn -w 2 -b 0.0.0.0:$PORT TKI.app_web:app
