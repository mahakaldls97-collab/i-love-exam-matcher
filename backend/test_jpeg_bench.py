import pypdfium2 as pdfium, io, base64, os, requests, sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv(override=True)

key = os.getenv('GEMINI_API_KEY')
pdf_path = r'C:\Users\dlsma\OneDrive\Desktop\lab pa.pdf'
pdf = pdfium.PdfDocument(pdf_path)

parts = []
t0 = time.time()
for pno in range(1, 6): # 5 pages (pages 2 to 6)
    bmp = pdf[pno].render(scale=1.2)
    img = bmp.to_pil()
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=75)
    enc = base64.b64encode(buf.getvalue()).decode()
    parts.append({'inlineData': {'mimeType': 'image/jpeg', 'data': enc}})

print(f"Rendered 5 pages to JPEG in {time.time()-t0:.2f}s")

prompt = """Extract all MCQs visible across these pages into a JSON array:
[{"q_no": "1", "question": "Hindi and/or English text", "options": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}}]
Include BOTH Hindi and English for bilingual questions.
"""
parts.append({'text': prompt})

url = 'https://generativelanguage.googleapis.com/v1/models/gemini-3.6-flash:generateContent'
body = {
    'contents': [{'parts': parts}],
    'generationConfig': {'responseMimeType': 'application/json', 'thinkingConfig': {'thinkingBudget': 0}}
}
t1 = time.time()
r = requests.post(url, headers={'x-goog-api-key': key, 'Content-Type': 'application/json'}, json=body, timeout=60)
print(f"Gemini API call took {time.time()-t1:.2f}s, status: {r.status_code}")
if r.status_code == 200:
    data = json.loads(r.json()['candidates'][0]['content']['parts'][0]['text'])
    print(f"Extracted {len(data)} questions! Q{data[0].get('q_no')} to Q{data[-1].get('q_no')}")
    print("Sample Q1:", data[0].get('question')[:80].replace('\n', ' '))
else:
    print("Error:", r.text[:200])
