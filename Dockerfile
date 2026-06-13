FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=TKI/app_web.py
# Hugging Face Spaces requires port 7860
ENV PORT=7860

WORKDIR /app

# Install system dependencies (required for psycopg2 and standard C bindings)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces requires running as a non-root user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Install python dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY --chown=user . .

# Expose port
EXPOSE 7860

# Run gunicorn server
CMD gunicorn -w 2 -b 0.0.0.0:7860 TKI.app_web:app
