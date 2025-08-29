# Python image
FROM python:3.13

# Set working directory inside container
WORKDIR /app

# Install Tesseract, Poppler, and build tools
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    build-essential \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Download all traineddata files from tessdata_best
RUN mkdir -p /usr/share/tesseract-ocr/5/tessdata && \
    curl -L https://github.com/tesseract-ocr/tessdata_best/archive/refs/heads/main.zip -o /tmp/tessdata.zip && \
    unzip /tmp/tessdata.zip -d /tmp/ && \
    cp /tmp/tessdata_best-main/*.traineddata /usr/share/tesseract-ocr/5/tessdata/ && \
    rm -rf /tmp/tessdata.zip /tmp/tessdata_best-main

# Verify Tesseract installation 
RUN which tesseract && tesseract --version && tesseract --list-langs

# Copy project files into container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set Flask app entrypoint 
ENV FLASK_APP=app.py

# Expose port used by Flask
EXPOSE 10000

# Start the Flask application
CMD ["flask", "run", "--host=0.0.0.0", "--port=10000"]
