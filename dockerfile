FROM python:3.13-slim

# Install uv
RUN pip install uv

# Set workdir
WORKDIR /app
COPY . .

# Install system dependencies (tesseract, poppler, build tools)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    build-essential \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# Verify tesseract install
RUN which tesseract && tesseract --version

# Sync Python dependencies
RUN uv sync

# Set flask app explicitly
ENV FLASK_APP=app.py

# Expose port (for local testing)
EXPOSE 10000

# Run flask
CMD flask run --host=0.0.0.0 --port=$PORT
