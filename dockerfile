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

# Install uv to export requirements, not to manage venv
RUN pip install uv

COPY . .

# Instead of creating a separate .venv, install directly into container
RUN uv pip install --system --requirement pyproject.toml || uv pip install --system --editable .

ENV FLASK_APP=app.py
EXPOSE 10000

CMD ["python", "entrypoint.py"]
