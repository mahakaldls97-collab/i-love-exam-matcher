import sys, os
sys.path.insert(0, ".")
from extractor import call_gemini

try:
    res = call_gemini([{"text": "Return a simple JSON array: [1, 2, 3]"}])
    print("call_gemini SUCCESS:", res)
except Exception as e:
    print("call_gemini ERROR:", e)
