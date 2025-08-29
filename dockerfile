FROM python:3.13

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    build-essential \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN which tesseract && tesseract --version

# Copy project files
COPY . .

# Install Python dependencies into system Python
RUN pip install -r requirements.txt

ENV FLASK_APP=app.py
EXPOSE 10000

CMD ["python", "entrypoint.py"]
