# 📝 Exam Answer Matcher

> Question Paper और Answer Key को AI से automatically match करें — अलग Set/Series हो तो भी!

## Features

- 📄 **PDF + Image Support** — Question Paper और Answer Key PDF या image में upload करें
- 🤖 **AI-Powered Matching** — Gemini AI question content के आधार पर different series को match करता है
- ✍️ **Easy Answer Entry** — Click करके A/B/C/D select करें
- 📊 **Detailed Results** — Per-question breakdown + Total Score
- ➖ **Negative Marking** — Configurable negative marking support
- 📱 **Mobile Friendly** — Phone पर भी आसानी से use करें

---

## Setup (पहली बार)

### Step 1 — Gemini API Key लें (Free)
1. जाएं: https://aistudio.google.com
2. "Get API Key" → Create API Key
3. Key copy करें

### Step 2 — Dependencies Install करें
```bash
cd backend
pip install -r requirements.txt
```

### Step 3 — API Key Set करें
```bash
# backend फोल्डर में .env file बनाएं:
copy .env.example .env
# .env खोलें और GEMINI_API_KEY=आपकी_key_यहाँ_paste_करें
```

### Step 4 — Server चलाएं
```bash
# Option A: run.bat double-click करें (Windows)
# Option B: command से:
cd backend
uvicorn main:app --reload --port 8000
```

### Step 5 — Browser में खोलें
```
http://localhost:8000
```

---

## Usage

1. **Upload** — Question Paper और Answer Key upload करें
2. **Settings** — Marks per question और Negative marking set करें
3. **Extract** — "Questions Extract करें" button दबाएं (10-30 sec)
4. **Answers** — हर question के लिए अपना answer (A/B/C/D) चुनें
5. **Score** — "Score Calculate करें" दबाएं
6. **Results** — Detailed table और score summary देखें!

---

## Supported Formats

| Document Type | Formats |
|---|---|
| Question Paper | PDF, JPG, PNG, WEBP |
| Answer Key | PDF, JPG, PNG, WEBP |

**Answer Key Types:**
- ✅ Full question paper with correct answers
- ✅ Simple Q.No → Answer list (e.g., "1-B, 2-A, 3-D...")

---

## Tech Stack

- **Backend:** Python + FastAPI
- **AI:** Google Gemini 1.5 Flash
- **PDF Parsing:** pdfplumber
- **Frontend:** Vanilla HTML + CSS + JavaScript

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Could not parse questions" | PDF quality check करें; image के रूप में try करें |
| Slow response | Gemini API call करता है — 15-30 sec normal है |
| Wrong matching | Answer key में full questions होने पर matching बेहतर होती है |
| API error | .env में GEMINI_API_KEY सही है check करें |
