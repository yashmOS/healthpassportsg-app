FROM python:3.13

# Set working directory
WORKDIR /app

# Install system dependencies (Tesseract, Poppler, build tools)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    build-essential \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Verify Tesseract installation
RUN which tesseract && tesseract --version

# Install uv package manager
RUN pip install uv

# Copy project files
COPY . .

# Sync Python dependencies into .venv
RUN uv sync

# Set Flask app explicitly
ENV FLASK_APP=app.py

# Expose Render’s assigned port
EXPOSE 10000

# Run Flask using the virtual environment Python and entrypoint
CMD ["/app/.venv/bin/python", "entrypoint.py"]