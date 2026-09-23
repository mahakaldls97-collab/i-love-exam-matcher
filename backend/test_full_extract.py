import os, base64, requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv(override=True)

key = os.getenv('GEMINI_API_KEY')
pdf_path = r'C:\Users\dlsma\OneDrive\Desktop\lab pa.pdf'

with open(pdf_path, 'rb') as f:
    enc = base64.b64encode(f.read()).decode()

prompt = """Extract ALL questions (from question 1 to the very last question, up to question 150) from this entire exam booklet.
For each question:
- "q_no": string question number (e.g. "1", "2")
- "question": full question text in Hindi and English (bilingual)
- "options": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}
Return ONLY a valid JSON array containing every single question from 1 to 150. Do not stop or truncate early.
"""

url = 'https://generativelanguage.googleapis.com/v1/models/gemini-3.6-flash:generateContent'
headers = {'x-goog-api-key': key, 'Content-Type': 'application/json'}
body = {
    'contents': [{
        'parts': [
            {'inlineData': {'mimeType': 'application/pdf', 'data': enc}},
            {'text': prompt}
        ]
    }],
    'generationConfig': {
        'responseMimeType': 'application/json',
        'maxOutputTokens': 65536,
        'thinkingConfig': {'thinkingBudget': 0}
    }
}
print("Calling Gemini with maxOutputTokens 65536...")
r = requests.post(url, headers=headers, json=body, timeout=180)
print('Status:', r.status_code)
if r.status_code == 200:
    res_text = r.json()['candidates'][0]['content']['parts'][0]['text']
    data = json.loads(res_text)
    print('Total questions extracted:', len(data))
    if data:
        print('First Q:', data[0]['q_no'])
        print('Last Q:', data[-1]['q_no'])
        with open('extracted_sample.json', 'w', encoding='utf-8') as out:
            json.dump(data, out, ensure_ascii=False, indent=2)
else:
    print('Error:', r.text[:300])
