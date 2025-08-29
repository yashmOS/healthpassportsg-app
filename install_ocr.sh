#!/bin/bash
set -e

echo "Installing system dependencies"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Please install Homebrew first: https://brew.sh/"
        exit 1
    fi

    echo "Installing/updating tesseract and poppler..."
    brew install tesseract poppler || brew upgrade tesseract poppler

elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    # Windows (Git Bash / Cygwin / WSL)
    echo "Windows detected. Please install the following manually:"
    echo "Tesseract OCR: https://github.com/tesseract-ocr/tesseract"
    echo "Poppler: https://github.com/oschwartz10612/poppler-windows"
    echo "Add both to your PATH environment variable."

else
    echo "Unsupported OS $OSTYPE. Please install tesseract and poppler manually."
fi

echo "Installing Python dependencies..."
# Upgrade pip
python -m pip install --upgrade pip

# Auto-detect requirements.txt location
if [[ -f requirements_ocr.txt ]]; then
    python -m pip install -r requirements_ocr.txt
elif [[ -f services/requirements_ocr.txt ]]; then
    python -m pip install -r services/requirements_ocr.txt
else
    echo "requirements_ocr.txt not found!"
    exit 1
fi

echo "Installation complete!"
