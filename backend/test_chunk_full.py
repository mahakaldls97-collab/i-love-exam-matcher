import pypdfium2 as pdfium
import io, base64, os, requests, sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv(override=True)

key = os.getenv('GEMINI_API_KEY')
pdf_path = r'C:\Users\dlsma\OneDrive\Desktop\lab pa.pdf'

def extract_chunk(sub_pdf_bytes, page_range):
    enc = base64.b64encode(sub_pdf_bytes).decode()
    prompt = f"""Extract all MCQs from pages {page_range} of this exam paper.
Return a JSON array:
[
  {{
    "q_no": "1",
    "question": "Hindi text and/or English text",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}}
  }}
]
Rules:
- Include BOTH Hindi and English if bilingual.
- Include ALL options (A, B, C, D, E).
"""
    url = 'https://generativelanguage.googleapis.com/v1/models/gemini-3.6-flash:generateContent'
    body = {
        'contents': [{'parts': [{'inlineData': {'mimeType': 'application/pdf', 'data': enc}}, {'text': prompt}]}],
        'generationConfig': {'responseMimeType': 'application/json', 'thinkingConfig': {'thinkingBudget': 0}}
    }
    r = requests.post(url, headers={'x-goog-api-key': key, 'Content-Type': 'application/json'}, json=body, timeout=45)
    if r.status_code == 200:
        return json.loads(r.json()['candidates'][0]['content']['parts'][0]['text'])
    else:
        print(f"Error on {page_range}:", r.status_code, r.text[:150])
        return []

pdf = pdfium.PdfDocument(pdf_path)
total_pages = len(pdf)
print(f"Total pages: {total_pages}")

# Test on first 2 chunks: pages 1-4 and 5-8
all_q = []
for start in [1, 5]:
    end = min(start + 4, total_pages)
    sub = pdfium.PdfDocument.new()
    sub.import_pages(pdf, list(range(start, end)))
    buf = io.BytesIO()
    sub.save(buf)
    t0 = time.time()
    res = extract_chunk(buf.getvalue(), f"{start+1}-{end}")
    print(f"Pages {start+1}-{end} took {time.time()-t0:.1f}s, extracted {len(res)} questions.")
    all_q.extend(res)

print(f"\nTotal extracted so far: {len(all_q)}")
for q in all_q[:5]:
    print(f"Q.{q.get('q_no')}: {q.get('question','')[:60].replace(chr(10), ' ')}")
