import os
import pytesseract
from app import app  

# Explicitly set Tesseract binary path
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Run Flask
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
