import sys, os, requests, json

key = sys.argv[1]
path = r'C:\Users\dlsma\.gemini\antigravity\scratch\exam-answer-matcher\backend\.env'
with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(f'GEMINI_API_KEY={key}\n')
print('Key saved. Testing methods...\n')

url_v1b = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'
body = {'contents': [{'parts': [{'text': 'Say hi'}]}]}

tests = [
    ('x-goog-api-key header', {'x-goog-api-key': key, 'Content-Type': 'application/json'}, url_v1b, {}),
    ('?key= param',           {'Content-Type': 'application/json'}, url_v1b, {'key': key}),
    ('Bearer header',          {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}, url_v1b, {}),
]

for name, headers, url, params in tests:
    try:
        r = requests.post(url, headers=headers, params=params, json=body, timeout=15)
        if r.status_code == 200:
            ans = r.json()['candidates'][0]['content']['parts'][0]['text']
            print(f'[SUCCESS] {name}: {ans[:40]}')
        else:
            err = r.json().get('error', {}).get('message', r.text[:100])
            print(f'[FAIL {r.status_code}] {name}: {err[:80]}')
    except Exception as e:
        print(f'[ERR] {name}: {e}')
