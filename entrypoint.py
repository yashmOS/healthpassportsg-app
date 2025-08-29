import os
import pytesseract
from app import app

# Explicit path to Tesseract
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Start Flask
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
