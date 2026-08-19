#!/usr/bin/env python3
"""Quick test of OpenRouter models via GitHub Actions env."""
import os, json, sys

try:
    import requests
except ImportError:
    os.system("pip install requests -q")
    import requests

key = os.environ.get("OPENROUTER_API_KEY", "")
if not key:
    print("NO_KEY")
    sys.exit(1)

models = [
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-coder:free",
]

for model in models:
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "HTTP-Referer": "https://paperchase.online"},
            json={"model": model, "messages": [{"role": "user", "content": "Reply with just: OK"}], "max_tokens": 10, "temperature": 0},
            timeout=15,
        )
        if r.ok:
            txt = r.json()["choices"][0]["message"]["content"].strip()
            print(f"OK {model}: {txt}")
        else:
            err = r.json().get("error", {}).get("message", r.text[:100])
            print(f"FAIL {model}: {err}")
    except Exception as e:
        print(f"FAIL {model}: {e}")
