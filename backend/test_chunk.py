import pypdfium2 as pdfium
import io, base64, os, requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv(override=True)

key = os.getenv('GEMINI_API_KEY')
pdf_path = r'C:\Users\dlsma\OneDrive\Desktop\lab pa.pdf'
pdf = pdfium.PdfDocument(pdf_path)

sub = pdfium.PdfDocument.new()
sub.import_pages(pdf, [1, 2, 3]) # pages 2, 3, 4 (0-indexed)
buf = io.BytesIO()
sub.save(buf)
enc = base64.b64encode(buf.getvalue()).decode()

prompt = """Extract all MCQs from these pages.
Return ONLY a JSON array:
[{"q_no": "1", "question": "Hindi and/or English question text", "options": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}}]
Include BOTH Hindi and English for bilingual questions.
"""

url = 'https://generativelanguage.googleapis.com/v1/models/gemini-3.6-flash:generateContent'
headers = {'x-goog-api-key': key, 'Content-Type': 'application/json'}
body = {
    'contents': [{'parts': [{'inlineData': {'mimeType': 'application/pdf', 'data': enc}}, {'text': prompt}]}],
    'generationConfig': {'responseMimeType': 'application/json', 'thinkingConfig': {'thinkingBudget': 0}}
}
r = requests.post(url, headers=headers, json=body, timeout=40)
print('Status:', r.status_code)
if r.status_code == 200:
    data = json.loads(r.json()['candidates'][0]['content']['parts'][0]['text'])
    print(f'Extracted {len(data)} questions.')
    for q in data:
        print(f"Q.{q['q_no']}: {q['question'][:80].replace(chr(10), ' ')}")
else:
    print('Error:', r.text[:200])
