import pypdfium2 as pdfium, io, base64, os, requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv(override=True)

key = os.getenv('GEMINI_API_KEY')
pdf_path = r'C:\Users\dlsma\OneDrive\Desktop\ans.pdf'
pdf = pdfium.PdfDocument(pdf_path)

bmp = pdf[0].render(scale=2.0)
img = bmp.to_pil()
buf = io.BytesIO()
img.save(buf, format='JPEG', quality=85)
enc = base64.b64encode(buf.getvalue()).decode()

prompt = """Extract ALL question numbers and their corresponding official answers from this answer key table.
Return ONLY this JSON:
{
  "type": "answers_only",
  "data": [
    {"q_no": "1", "correct_answer": "B"},
    {"q_no": "2", "correct_answer": "A"}
  ]
}
Rules:
- Include all question numbers (1 to 150).
- correct_answer must be A, B, C, D, or Delete/Bonus.
"""

url = 'https://generativelanguage.googleapis.com/v1/models/gemini-3.6-flash:generateContent'
body = {
    'contents': [{'parts': [{'inlineData': {'mimeType': 'image/jpeg', 'data': enc}}, {'text': prompt}]}],
    'generationConfig': {'responseMimeType': 'application/json', 'thinkingConfig': {'thinkingBudget': 0}}
}
r = requests.post(url, headers={'x-goog-api-key': key, 'Content-Type': 'application/json'}, json=body, timeout=40)
print('Status:', r.status_code)
if r.status_code == 200:
    data = json.loads(r.json()['candidates'][0]['content']['parts'][0]['text'])
    items = data.get('data', [])
    print(f'Extracted {len(items)} answers from ans.pdf!')
    if items:
        print('First 5:', items[:5])
        print('Last 5:', items[-5:])
else:
    print('Error:', r.text[:200])
