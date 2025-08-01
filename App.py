# Klíčová slova pro začátek nového dokumentu
KEYWORDS = [
    "Pracovní smlouva",
    "Dodatek č.",
    "Mzdový výměr",
    "Dohoda o provedení práce",
    "Dohoda o pracovní činnosti"
]

import fitz  # PyMuPDF
import os
import re

# --- Nastavení ---
input_pdf_path = "velky_soubor.pdf"
output_folder = "vystupy"
KEYWORDS = [
    "Pracovní smlouva",
    "Dodatek č.",
    "Mzdový výměr",
    "Dohoda o provedení práce",
    "Dohoda o pracovní činnosti"
]

os.makedirs(output_folder, exist_ok=True)

# --- Načti PDF ---
doc = fitz.open(input_pdf_path)

segments = []
current_segment = {"start": 0, "type": None, "name": None}

for page_num in range(len(doc)):
    page = doc.load_page(page_num)
    text = page.get_text()

    for keyword in KEYWORDS:
        if keyword in text:
            if current_segment["type"]:  # už něco běží -> ukončíme předchozí blok
                current_segment["end"] = page_num - 1
                segments.append(current_segment)
                current_segment = {"start": page_num, "type": None, "name": None}

            current_segment["start"] = page_num
            current_segment["type"] = keyword

            # Zkus najít jméno
            name_match = re.search(r"(?:Jméno|Zaměstnanec|Pan|Paní)\s*([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+\s+[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)", text)
            if name_match:
                current_segment["name"] = name_match.group(1)

# Přidej poslední segment až do konce dokumentu
if current_segment["type"]:
    current_segment["end"] = len(doc) - 1
    segments.append(current_segment)

# --- Ulož jednotlivé soubory ---
for i, seg in enumerate(segments):
    output_path = f"{output_folder}/{i+1:03d}_{seg['type'].replace(' ', '_')}"
    if seg["name"]:
        output_path += f"_{seg['name'].replace(' ', '_')}"
    output_path += ".pdf"

    new_doc = fitz.open()
    for page_num in range(seg["start"], seg["end"] + 1):
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

    new_doc.save(output_path)
    new_doc.close()
    print(f"Uloženo: {output_path}")