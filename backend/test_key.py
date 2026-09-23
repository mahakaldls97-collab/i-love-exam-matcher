import sys, os

# Read key from argument
key = sys.argv[1]
path = r'C:\Users\dlsma\.gemini\antigravity\scratch\exam-answer-matcher\backend\.env'

# Save key
with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(f'GEMINI_API_KEY={key}\n')
print('Key saved!')

# Test as Bearer token
import requests
url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'
headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
data = {'contents': [{'parts': [{'text': 'Say Namaste'}]}]}
r = requests.post(url, headers=headers, json=data)
print('Bearer test - Status:', r.status_code)

# Test as API key param
r2 = requests.post(url + f'?key={key}', headers={'Content-Type': 'application/json'}, json=data)
print('API key test - Status:', r2.status_code)
if r2.status_code == 200:
    print('SUCCESS!', r2.json()['candidates'][0]['content']['parts'][0]['text'][:50])
else:
    print('API Error:', r2.text[:150])
