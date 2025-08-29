import os
import pytesseract
from app import app

# Prepend /usr/bin to PATH to ensure Tesseract is found
if "/usr/bin" not in os.environ.get("PATH", "").split(":"):
    os.environ["PATH"] = "/usr/bin:" + os.environ.get("PATH", "")

# Explicit path to Tesseract
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Start Flask
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
