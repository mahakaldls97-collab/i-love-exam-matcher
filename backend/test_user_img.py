import os
import base64
import json
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")
img_path = r"C:/Users/dlsma/.gemini/antigravity/brain/d8b15807-cfcc-4641-91f2-091c0f20dadc/.user_uploaded/media_1790070344367.png"

with open(img_path, "rb") as f:
    b64_img = base64.b64encode(f.read()).decode("utf-8")

prompt = """You are an expert OCR and exam parsing engine.
Read this exam paper image carefully. Extract all questions with options. Ignore pen marks, tick marks, and watermarks.
Output ONLY a valid JSON array with this structure:
[
  {
    "q_no": "1",
    "question": "Hindi\\nEnglish",
    "options": {
      "A": "...",
      "B": "...",
      "C": "...",
      "D": "...",
      "E": "..."
    }
  }
]"""

payload = {
    "contents": [{
        "parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": "image/png", "data": b64_img}}
        ]
    }]
}

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
resp = requests.post(url, json=payload, timeout=120)
print("HTTP Status:", resp.status_code)
try:
    data = resp.json()
    content = data["candidates"][0]["content"]["parts"][0]["text"]
    out_path = "extraction_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS! Result saved to:", out_path)
    print("Content length:", len(content), "characters")
except Exception as e:
    out_path = "extraction_error.json"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("Error. Raw response saved to:", out_path)
