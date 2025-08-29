# Use slim Python base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies first
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    build-essential \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# Verify tesseract installation
RUN which tesseract && tesseract --version

# Install uv package manager
RUN pip install uv

# Copy project files
COPY . .

# Sync Python dependencies into .venv
RUN uv sync

# Ensure Flask app is recognized
ENV FLASK_APP=app.py

# Explicitly set path to Tesseract for pytesseract
ENV TESSERACT_CMD=/usr/bin/tesseract

# Expose Render’s assigned port
EXPOSE 10000

# Run Flask using the virtual environment Python
CMD ["/app/.venv/bin/python", "-c", "import os; import pytesseract; pytesseract.pytesseract.tesseract_cmd=os.environ.get('TESSERACT_CMD','/usr/bin/tesseract'); from flask import Flask; import app; app.app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))"]
