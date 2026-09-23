import os, requests
from dotenv import load_dotenv
env_path = r'C:\Users\dlsma\.gemini\antigravity\scratch\exam-answer-matcher\backend\.env'
load_dotenv(env_path, override=True)
key = os.getenv("GEMINI_API_KEY", "")
print("Key:", len(key), "chars,", key[:12])

for model in ["gemini-3.6-flash", "gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-2.5-pro"]:
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent"
    r = requests.post(url,
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": "Say hi"}]}]},
        timeout=20
    )
    if r.status_code == 200:
        print("SUCCESS:", model)
        break
    else:
        print(model, "->", r.status_code)
