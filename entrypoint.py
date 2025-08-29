import os
import pytesseract
from app import app  # import your Flask app

# Explicitly set the Tesseract binary path
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Run Flask
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
