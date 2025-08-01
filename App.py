import PyPDF2 as st
import tempfile
import re
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import pytesseract

def rozpoznej_typ_dokumentu(text):
    text = text.lower()
    if "pracovní smlouva" in text:
        return "PS"
    elif "mzdový výměr" in text or "mzdovy vymer" in text:
        return "MV"
    elif "dodatek k pracovní smlouvě" in text or "dodatek k pracovni smlouve" in text:
        return "DPS"
    else:
        return "UNKNOWN"

def najdi_jmeno(text):
    match = re.search(r"Jméno a příjmení:\s*([A-ZÁ-Ž][a-zá-ž]+)\s+([A-ZÁ-Ž][a-zá-ž]+)", text)
    if match:
        prijmeni = match.group(1)
        jmeno = match.group(2)
        return prijmeni, jmeno
    return "Neznámý", "Neznámý"

def najdi_datum(text):
    # Hledá datum s 1 nebo 2 ciframi dne a měsíce za "účinnosti dnem"
    match = re.search(r"účinnosti dnem\s*(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
    if match:
        den, mesic, rok = match.group(1).zfill(2), match.group(2).zfill(2), match.group(3)
        datum_formatted = f"{rok}-{mesic}-{den}"
        st.write(f"🗓️ [DEBUG] Datum podle 'účinnosti dnem': {datum_formatted}")
        return datum_formatted

    # Pokud nevyšlo, najde první datum obecně ve formátu D{1,2}.M{1,2}.YYYY
    match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
    if match:
        den, mesic, rok = match.group(1).zfill(2), match.group(2).zfill(2), match.group(3)
        datum_formatted = f"{rok}-{mesic}-{den}"
        st.write(f"🗓️ [DEBUG] Datum podle obecného formátu: {datum_formatted}")
        return datum_formatted

    st.write("🗓️ [DEBUG] Datum nenalezeno")
    return "0000-00-00"

def je_nova_zakladni_stranka(text):
    keywords = ["pracovní smlouva", "mzdový výměr", "dodatek k pracovní smlouvě"]
    text_lower = text.lower()
    return any(k in text_lower for k in keywords)

st.title("📝 OCR segmentace naskenovaného PDF na jednotlivé dokumenty")

uploaded_file = st.file_uploader("Nahraj jeden velký PDF soubor", type="pdf")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    reader = PdfReader(tmp_path)
    num_pages = len(reader.pages)
    st.write(f"📄 Celkem stran ve vstupu: {num_pages}")

    st.info("Probíhá OCR, může to chvíli trvat...")
    images = convert_from_path(tmp_path, dpi=200)

    page_texts = []
    for i, img in enumerate(images):
        text = pytesseract.image_to_string(img, lang='ces')
        page_texts.append(text)
        st.write(f"📝 OCR načtena stránka {i+1}/{num_pages}")

    segment_start_pages = []
    for i, text in enumerate(page_texts):
        if je_nova_zakladni_stranka(text):
            segment_start_pages.append(i)
    segment_start_pages.append(num_pages)

    st.write(f"🔖 Nalezených segmentů: {len(segment_start_pages)-1}")

    for idx in range(len(segment_start_pages) - 1):
        start = segment_start_pages[idx]
        end = segment_start_pages[idx + 1]

        segment_text = "".join(page_texts[start:end])

        typ = rozpoznej_typ_dokumentu(segment_text)
        prijmeni, jmeno = najdi_jmeno(segment_text)
        datum = najdi_datum(segment_text)

        novy_nazev = f"{typ}_{prijmeni}_{jmeno}_INNO_{datum}.pdf"
        st.markdown(f"### Segment {idx+1}: `{novy_nazev}` (strany {start+1}-{end})")

        writer = PdfWriter()
        for p in range(start, end):
            writer.add_page(reader.pages[p])

        segment_tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        with open(segment_tmp_file.name, "wb") as f_out:
            writer.write(f_out)

        st.write(f"📄 Počet stran segmentu: {end - start}")
        for i_img in range(start, end):
            st.image(images[i_img], caption=f"Strana {i_img - start + 1}", use_container_width=True)

        with open(segment_tmp_file.name, "rb") as f:
            st.download_button(
                label="📥 Stáhnout tento segment",
                data=f,
                file_name=novy_nazev,
                mime="application/pdf",
                key=f"download_segment_{idx}"
            )