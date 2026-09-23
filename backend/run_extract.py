import os
import base64
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")
img_path = r"C:\Users\dlsma\.gemini\antigravity\brain\d8b15807-cfcc-4641-91f2-091c0f20dadc\.user_uploaded\media_1790070344367.png"

with open(img_path, "rb") as f:
    b64_img = base64.b64encode(f.read()).decode("utf-8")

prompt = "Extract the MCQ question number, question text (Hindi and English both), and all options (A,B,C,D,E) from this Indian exam paper image. Ignore pen marks, ticks, crosses and watermarks. Return ONLY valid JSON array."

payload = {
    "contents": [{
        "parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": "image/png", "data": b64_img}}
        ]
    }]
}

models = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.5-flash-lite"]

for model in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    print(f"Trying {model}...", flush=True)
    try:
        resp = requests.post(url, json=payload, timeout=120)
        print(f"  HTTP {resp.status_code}", flush=True)
        if resp.status_code == 200:
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            with open("extracted_question.txt", "w", encoding="utf-8") as out:
                out.write(text)
            print(f"  SUCCESS! {len(text)} chars saved to extracted_question.txt", flush=True)
            break
        else:
            # Print error but continue to next model
            try:
                err = resp.json().get("error", {}).get("message", "Unknown error")
                print(f"  Error: {err[:120]}", flush=True)
            except Exception:
                print(f"  Error response", flush=True)
            time.sleep(1)
    except requests.exceptions.ReadTimeout:
        print(f"  Timeout after 120s, trying next model...", flush=True)
    except Exception as e:
        print(f"  Exception: {type(e).__name__}: {e}", flush=True)
