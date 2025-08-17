import json
import os
import re

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from PIL.ImageFile import ImageFile
from PIL.PpmImagePlugin import PpmImageFile


# Load and convert file to PIL images
def load_input_file(file_path: str) -> list[Image.Image] | list[ImageFile]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        images = convert_from_path(file_path)
    elif ext in [".jpg", ".jpeg", ".png"]:
        images = [Image.open(file_path)]
    else:
        raise ValueError("Unsupported file format")
    return images


# Preprocess image to handle shadowed text using adaptive thresholding
def preprocess_image(img: PpmImageFile) -> np.ndarray:
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
    processed_image = cv2.adaptiveThreshold(
        resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 63, 12
    )
    return processed_image


# Detect language from image (basic version using Tesseract script confidence)
def detect_language(image: np.ndarray) -> str:
    langs = ["eng", "tam", "mal", "chi_sim"]  # Chinese Simplified, Tamil, Malay
    scores = {}
    for lang in langs:
        data = pytesseract.image_to_data(
            image, lang=lang, output_type=pytesseract.Output.dict
        )
        confs = [int(conf) for conf in data["conf"] if conf != "-1"]
        avg_conf = sum(confs) / len(confs) if confs else 0
        scores[lang] = avg_conf
    return max(scores, key=scores.get)


# OCR function
def ocr_image(img: np.ndarray, lang: str = "eng") -> str:
    return pytesseract.image_to_string(img, lang=lang)


# Main pipeline
def run_ocr(file_path, output_json="output.json"):
    images = load_input_file(file_path)
    results = []

    for i, pil_img in enumerate(images):
        pre_img = preprocess_image(pil_img)
        detected_lang = detect_language(pre_img)
        print(f"[Page {i + 1}] Detected language: {detected_lang}")
        text = ocr_image(pre_img, lang=detected_lang)

        results.append({"page": i + 1, "language": detected_lang, "text": text.strip()})

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"OCR complete. Saved to {output_json}")
    return results


ocr_result = run_ocr("/content/test_text.png")

# Post-OCR Cleaner


def clean_ocr_text(ocr_results: list[dict]) -> list[dict]:
    cleaned_results = []

    for result in ocr_results:
        text = result["text"]

        # Basic fixes
        text = re.sub(r"\s+", " ", text)  # Collapse multiple whitespaces
        text = re.sub(r"(\d)\s+(\d)", r"\1\2", text)  # Fix broken numbers
        text = re.sub(r"([a-zA-Z])\s+([a-zA-Z])", r"\1\2", text)  # Fix broken words
        text = re.sub(
            r"(?<!\d)([.,])(?!\d)", r" \1 ", text
        )  # Add space around punctuation
        text = re.sub(
            r"([a-z])([A-Z])", r"\1 \2", text
        )  # Add space for camel-case artifacts

        # Fix common OCR confusion
        fixes = {
            "1mg": "1 mg",
            "lmg": "1 mg",
            "I mg": "1 mg",
            "0": "O",  # Only if surrounding characters are letters?
            "Phone(": "Phone: (",
            "|": "I",
        }
        for wrong, right in fixes.items():
            text = text.replace(wrong, right)

        result["cleaned_text"] = text.strip()
        cleaned_results.append(result)

    return cleaned_results


# Label-Aware Parser
LABELS = {
    "name": ["name", "patient name", "pt name", "patient"],
    "date": ["date", "issued date", "visit date"],
    "address": ["address", "addr", "residence"],
    "phone": ["phone", "tel", "telephone"],
    "refill": ["refill"],
}


def normalize_label(line: str) -> str:
    line_lower = line.lower()
    for label, variants in LABELS.items():
        for variant in variants:
            if variant in line_lower:
                return label
    return None


def extract_key_values(text: str) -> dict:
    extracted = {
        "name": None,
        "date": None,
        "address": None,
        "phone": None,
        "doctor": None,
        "medications": [],
        "refill": None,
    }

    # 1. Split into lines for easier parsing
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # 2. Try structured field matching
    for line in lines:
        line_lower = line.lower()

        # Name / Patient
        if any(label in line_lower for label in LABELS["name"]):
            match = re.search(
                r"(?:Name|Patient)[^\w]*[:\-]?\s*(.*)", line, re.IGNORECASE
            )
            if match:
                extracted["name"] = match.group(1).strip()

        # Date
        elif any(label in line_lower for label in LABELS["date"]):
            match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", line)
            if match:
                extracted["date"] = match.group(1).strip()

        # Address
        elif any(label in line_lower for label in LABELS["address"]):
            match = re.search(r"(?:Address)[^\w]*[:\-]?\s*(.*)", line, re.IGNORECASE)
            if match:
                extracted["address"] = match.group(1).strip()

        # Phone
        elif any(label in line_lower for label in LABELS["phone"]):
            match = re.search(r"(\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4})", line)
            if match:
                extracted["phone"] = match.group(1)

        # Refill
        elif any(label in line_lower for label in LABELS["refill"]):
            match = re.search(r"Refill[^\w]*[:\-]?\s*(.*)", line, re.IGNORECASE)
            if match:
                extracted["refill"] = match.group(1).strip()

    # 3. Doctor line (first line heuristic)
    if lines and "dr" in lines[0].lower():
        extracted["doctor"] = lines[0]

    # 4. Medication extraction — look for drug lines and instructions
    drug_lines = []
    instructions = ""
    in_directions = False

    for line in lines:
        # Detect med name + dosage
        med_match = re.match(r"([A-Za-z]+)\s+([\d\.]+\s*(?:mg|gram|ml|mcg|g))", line)
        if med_match:
            drug_lines.append(
                {
                    "name": med_match.group(1),
                    "dosage": med_match.group(2),
                    "instructions": "",
                }
            )

        # Detect Directions section
        if "directions" in line.lower():
            in_directions = True
            continue

        if in_directions:
            if "refill" in line.lower():  # end of instruction block
                in_directions = False
                continue
            instructions += line + " "

    # Map directions back to meds if one-to-one
    if len(drug_lines) == 1:
        drug_lines[0]["instructions"] = instructions.strip()
    elif len(drug_lines) > 1:
        parts = re.split(r"\b(?:\d+\s+pill|tablet|every|for)\b", instructions)
        for i, med in enumerate(drug_lines):
            if i < len(parts):
                med["instructions"] = parts[i].strip()

    extracted["medications"] = drug_lines

    return extracted
