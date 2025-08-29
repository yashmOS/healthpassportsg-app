# Python image
FROM python:3.13

# Set working directory inside container
WORKDIR /app

# Install system dependencies (Tesseract, Poppler, build tools for Python packages)
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

# Copy project files into container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set Flask app entrypoint (optional but good practice)
ENV FLASK_APP=app.py

# Expose port used by Flask
EXPOSE 10000

# Start the Flask application
CMD ["flask", "run", "--host=0.0.0.0", "--port=10000"]
