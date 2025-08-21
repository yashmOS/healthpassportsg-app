# ocr.py
"""
OCR + Gemini Parser Module
--------------------------
This script extracts text from PDFs/images (with language detection),
sends them to Gemini for structured parsing, and saves results as JSON.

Usage:
    python ocr.py <path_to_file>
Or import as a module:
    from ocr import run_pipeline, Result
"""

import os
import re
import json
from typing import Dict
from pprint import pprint

import fitz  # PyMuPDF for machine-readable PDFs
import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np
from langdetect import detect, DetectorFactory

import google.generativeai as genai

# Ensure langdetect is deterministic
DetectorFactory.seed = 0

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY")  # Replace securely
genai.configure(api_key=GEMINI_API_KEY)



# Language Detection


def detect_language_from_text(text: str) -> str:
    try:
        return detect(text)
    except:
        return "unknown"


def detect_language_from_image(img: np.ndarray) -> str:
    langs = ['eng', 'tam', 'mal', 'chi_sim']
    scores = {}

    for lang in langs:
        data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
        confs = [int(conf) for conf in data['conf'] if conf != '-1']
        avg_conf = sum(confs) / len(confs) if confs else 0
        scores[lang] = avg_conf

    return max(scores, key=scores.get)


# Text Extraction

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text.strip()


def ocr_pdf(file_path: str) -> str:
    pages = convert_from_path(file_path, dpi=300)
    all_text = []

    for i, page in enumerate(pages):
        img = np.array(page)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        processed = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 63, 12
        )

        lang = detect_language_from_image(processed)
        print(f"[Page {i+1}] Detected OCR language: {lang}")
        text = pytesseract.image_to_string(processed, lang=lang)
        all_text.append(text)

    return "\n".join(all_text)


def ocr_image(file_path: str) -> str:
    img = cv2.imread(file_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    processed = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 63, 12
    )

    lang = detect_language_from_image(processed)
    print(f"[Image] Detected OCR language: {lang}")
    return pytesseract.image_to_string(processed, lang=lang)


def load_and_extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
        if text.strip():
            detected_lang = detect_language_from_text(text)
            print(f"[PDF] Machine-readable text detected (lang: {detected_lang})")
        else:
            text = ocr_pdf(file_path)
    elif ext in [".jpg", ".jpeg", ".png"]:
        text = ocr_image(file_path)
    else:
        raise ValueError("Unsupported file format")

    return text.strip()

# Text Cleaner

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(\d)\s+(\d)", r"\1\2", text)
    text = re.sub(r"([a-zA-Z])\s+([a-zA-Z])", r"\1\2", text)
    text = re.sub(r"(?<!\d)([.,])(?!\d)", r" \1 ", text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = text.replace("|", "I")
    return text.strip()

# Gemini Parser

def parse_medical_with_gemini(file_path: str, extracted_text: str) -> Dict:
    prompt = f"""
    You are a medical document parser. Read the document carefully and extract
    information into the following JSON structure:

    {{
      "patient_details": {{
        "name": "",
        "date": "",
        "address": "",
        "phone": "",
        "refill": ""
      }},
      "record_metadata": {{
        "record_type": "",
        "hospital_name": "",
        "doctor_name": "",
        "department": "",
        "record_date": "",
        "other_metadata": {{}}
      }},
      "sections": {{
        "line_items": [],
        "medications": [],
        "lab_results": [],
        "diagnoses": []
      }},
      "totals": {{
        "before_subsidy": "",
        "govt_subsidy": "",
        "before_gst": "",
        "gst": "",
        "gst_absorbed": "",
        "after_subsidy": "",
        "net_payment": "",
        "final_payable": ""
      }},
      "other_details": {{}}
    }}

    Rules:
    - Always include the keys shown above, even if empty.
    - If a section is not relevant, return an empty list.
    - If a field is missing, leave it as an empty string.
    - Return JSON only. No explanations.

    Extracted Text:
    {extracted_text}
    """

    file_ref = genai.upload_file(path=file_path)

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        contents=[
            {"role": "user", "parts": [{"text": prompt}]},
            file_ref
        ],
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0
        }
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        print("Error decoding JSON response. Raw response:")
        print(response.text)
        return {}



# Normalizer


def normalize_output(data: Dict) -> Dict:
    def clean_nulls(obj):
        if isinstance(obj, dict):
            return {k: clean_nulls(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_nulls(v) for v in obj]
        elif obj is None:
            return ""
        elif isinstance(obj, str):
            return obj.replace("O", "0") if any(c.isdigit() for c in obj) else obj.strip()
        else:
            return obj

    data = clean_nulls(data)

    if "totals" in data:
        if data["totals"]["net_payment"] == "" and data["totals"]["after_subsidy"] != "":
            data["totals"]["net_payment"] = data["totals"]["after_subsidy"]

    if "record_metadata" in data:
        if data["patient_details"]["date"] == "" and data["record_metadata"]["record_date"] != "":
            data["patient_details"]["date"] = data["record_metadata"]["record_date"]

    return data



# Pipeline Runner


Result = {}

def run_pipeline(file_path: str, output_json: str = "Result.json") -> Dict:
    global Result

    raw_text = load_and_extract_text(file_path)
    cleaned_text = clean_text(raw_text)

    gemini_raw_result = parse_medical_with_gemini(file_path, cleaned_text)
    Result = normalize_output(gemini_raw_result)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(Result, f, indent=2, ensure_ascii=False)

    print(f"✅ Parsing complete. Results saved to {output_json}")
    return Result



# Main


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ocr.py <file_path>")
    else:
        file_path = sys.argv[1]
        final_result = run_pipeline(file_path)
        pprint(final_result)
