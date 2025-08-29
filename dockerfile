FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y tesseract-ocr poppler-utils

# Install uv
RUN pip install uv

WORKDIR /app
COPY . .

# Sync dependencies
RUN uv sync

# Expose port
EXPOSE 10000

CMD flask run --host=0.0.0.0 --port=$PORT
