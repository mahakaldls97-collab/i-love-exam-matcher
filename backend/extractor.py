import os
import base64
import json
import re
import io
import time
import requests
import pypdfium2 as pdfium
from dotenv import load_dotenv

load_dotenv(override=True)

# API Keys & Configurations
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
GEMINI_BASE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

CHUNK_PROMPT = """You are an expert at parsing Indian competitive exam papers.
Extract ALL multiple-choice questions (MCQs) visible across these pages into a JSON object with a "questions" array.

Return ONLY this JSON structure:
{
  "questions": [
    {
      "q_no": "1",
      "question": "Hindi text\\nEnglish text",
      "options": {
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "...",
        "E": "..."
      }
    }
  ]
}

Rules:
1. BILINGUAL SUPPORT: If a question is in both Hindi and English, include BOTH in "question" separated by newline (\\n).
2. If only Hindi, keep Hindi. If only English, keep English.
3. Keep all options (A, B, C, D, E).
4. Do NOT skip any questions on these pages.
"""

ANSWER_KEY_PROMPT = """You are an expert at parsing official exam answer keys.
Extract ALL question numbers and their corresponding official answers from this document.

Return ONLY this JSON:
{
  "type": "answers_only",
  "data": [
    {"q_no": "1", "correct_answer": "B"}
  ]
}

Rules:
- Extract all questions from question 1 to the last question.
- correct_answer should be A, B, C, D, or E (or Delete).
"""

def clean_json(text: str) -> str:
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
    return text.strip()

def get_mime_type(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    return {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "webp": "image/webp",
        "gif": "image/gif", "bmp": "image/bmp",
        "pdf": "application/pdf",
    }.get(ext, "application/octet-stream")

_gemini_key_index = 0

def get_gemini_keys() -> list:
    raw = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
    keys = [k.strip() for k in re.split(r"[,;\n]+", raw) if k.strip()]
    return keys if keys else [""]

def call_gemini(parts: list, timeout: int = 75) -> str:
    """Calls Google Gemini API with automatic Multi-Key rotation."""
    global _gemini_key_index
    keys = get_gemini_keys()
    total_keys = len(keys)

    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    # Try each key if rate-limited or error occurs
    last_err = None
    for k_attempt in range(max(len(keys), 3)):
        current_key = keys[_gemini_key_index % total_keys]
        _gemini_key_index = (_gemini_key_index + 1) % total_keys
        
        headers = {"x-goog-api-key": current_key, "Content-Type": "application/json"}
        r = requests.post(GEMINI_BASE_URL, headers=headers, json=body, timeout=timeout)
        
        if r.status_code == 429:
            print(f"Key #{_gemini_key_index} rate-limited (429), rotating to next key...")
            time.sleep(1.0)
            continue
        
        if r.status_code != 200:
            err = r.text[:250]
            try:
                err = r.json().get("error", {}).get("message", err)
            except Exception:
                pass
            last_err = err
            print(f"Key error ({r.status_code}): {err}, rotating to next key...")
            continue

        res_json = r.json()
        candidates = res_json.get("candidates", [])
        if not candidates:
            continue

        for p in candidates[0].get("content", {}).get("parts", []):
            if "text" in p and p["text"]:
                return p["text"]

    raise ValueError(f"All Gemini API keys failed or rate-limited. Last error: {last_err}")

def call_openai_vision(img_parts: list, prompt_text: str, timeout: int = 75) -> str:
    """Calls OpenAI Chat Completions API with vision support."""
    key = os.getenv("OPENAI_API_KEY", OPENAI_API_KEY).strip()
    if not key:
        raise ValueError("OPENAI_API_KEY not configured.")
    
    messages_content = [{"type": "text", "text": prompt_text}]
    for part in img_parts:
        if "inlineData" in part:
            mime = part["inlineData"].get("mimeType", "image/jpeg")
            data = part["inlineData"].get("data", "")
            messages_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime};base64,{data}",
                    "detail": "high"
                }
            })
    
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "user", "content": messages_content}
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 4096
    }
    
    resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise ValueError(f"OpenAI API Error ({resp.status_code}): {resp.text[:250]}")
    
    data = resp.json()
    return data["choices"][0]["message"]["content"]

def call_ai_engine(img_parts: list, prompt_text: str, timeout: int = 75) -> str:
    """
    DUAL-ENGINE AUTO ROUTER:
    1. Tries Google Gemini (Free, Fast)
    2. If Gemini fails or hits limit -> Automatically falls back to OpenAI (GPT-4o)
    3. If only one key is present, uses that provider seamlessly.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY).strip()
    openai_key = os.getenv("OPENAI_API_KEY", OPENAI_API_KEY).strip()

    # 1. Try Gemini first if key available
    if gemini_key:
        try:
            print("🤖 [AI Engine] Running via Google Gemini...")
            gemini_parts = list(img_parts)
            gemini_parts.append({"text": prompt_text})
            return call_gemini(gemini_parts, timeout=timeout)
        except Exception as e:
            print(f"⚠️ Google Gemini failed: {e}")
            if openai_key:
                print("🔄 [AI Engine Auto-Fallback] Switching seamlessly to OpenAI...")
            else:
                raise e

    # 2. Use OpenAI if key available (either primary or fallback)
    if openai_key:
        print("🤖 [AI Engine] Running via OpenAI (GPT-4o)...")
        return call_openai_vision(img_parts, prompt_text, timeout=timeout)

    raise ValueError("Neither GEMINI_API_KEY nor OPENAI_API_KEY is configured!")

def render_pages_to_jpegs(pdf, page_indices, scale: float = 1.0):
    parts = []
    for idx in page_indices:
        if idx >= len(pdf):
            continue
        bmp = pdf[idx].render(scale=scale)
        img = bmp.to_pil()
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=65)
        enc = base64.b64encode(buf.getvalue()).decode()
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": enc}})
    return parts

async def extract_and_parse_paper(file_bytes: bytes, filename: str) -> list:
    if filename.lower().endswith(".pdf"):
        pdf = pdfium.PdfDocument(file_bytes)
        total_pages = len(pdf)
        print(f"Processing PDF ({filename}): {total_pages} pages.")

        if total_pages <= 4:
            chunks = [list(range(total_pages))]
        else:
            chunks = []
            chunk_size = 4
            start_p = 1 if total_pages > 4 else 0
            for start in range(start_p, total_pages, chunk_size):
                chunks.append(list(range(start, min(start + chunk_size, total_pages))))

        all_questions = []
        for c_idx, chunk in enumerate(chunks):
            print(f"Extracting pages {chunk[0]+1} to {chunk[-1]+1} (Chunk {c_idx+1}/{len(chunks)})...")
            img_parts = render_pages_to_jpegs(pdf, chunk, scale=1.0)
            if not img_parts:
                continue
            try:
                raw = call_ai_engine(img_parts, CHUNK_PROMPT, timeout=75)
                cleaned = clean_json(raw)
                items = json.loads(cleaned)
                if isinstance(items, list):
                    all_questions.extend(items)
                elif isinstance(items, dict) and "questions" in items:
                    all_questions.extend(items["questions"])
            except Exception as e:
                print(f"Warning on chunk {chunk}: {e}")
            time.sleep(1.0)

        # Deduplicate and sort
        seen = set()
        unique = []
        for q in all_questions:
            qno_raw = str(q.get("q_no", "")).strip()
            qno = re.sub(r"[^\d]", "", qno_raw) or qno_raw
            if qno and qno not in seen:
                seen.add(qno)
                q["q_no"] = qno
                unique.append(q)

        def sort_key(item):
            try:
                return int(item["q_no"])
            except ValueError:
                return 9999

        unique.sort(key=sort_key)
        print(f"Finished: {len(unique)} questions extracted from {filename}.")
        return unique

    else:
        # Image file
        mime = get_mime_type(filename)
        enc = base64.b64encode(file_bytes).decode()
        img_parts = [{"inlineData": {"mimeType": mime, "data": enc}}]
        raw = call_ai_engine(img_parts, CHUNK_PROMPT, timeout=75)
        cleaned = clean_json(raw)
        items = json.loads(cleaned)
        if isinstance(items, dict) and "questions" in items:
            items = items["questions"]
        return items if isinstance(items, list) else []

async def extract_and_parse_key(file_bytes: bytes, filename: str) -> dict:
    if filename.lower().endswith(".pdf"):
        pdf = pdfium.PdfDocument(file_bytes)
        img_parts = render_pages_to_jpegs(pdf, list(range(len(pdf))), scale=1.5)
        raw = call_ai_engine(img_parts, ANSWER_KEY_PROMPT, timeout=75)
    else:
        mime = get_mime_type(filename)
        enc = base64.b64encode(file_bytes).decode()
        img_parts = [{"inlineData": {"mimeType": mime, "data": enc}}]
        raw = call_ai_engine(img_parts, ANSWER_KEY_PROMPT, timeout=75)

    data = json.loads(clean_json(raw))
    if isinstance(data, list):
        data = {"type": "answers_only", "data": data}
    return data
