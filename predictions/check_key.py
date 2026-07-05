#!/usr/bin/env python3
"""Diagnostic: check if OPENROUTER_API_KEY is set and working."""
import os, json, urllib.request

key = os.environ.get("OPENROUTER_API_KEY", "")
print(f"OPENROUTER_API_KEY set: {'YES' if key else 'NO'}")
print(f"Key length: {len(key)}")
print(f"First 8 chars: {key[:8] if key else 'N/A'}")

if not key:
    print("RESULT: KEY_MISSING")
    exit(1)

# Test connection
try:
    payload = json.dumps({
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "messages": [{"role": "user", "content": "Say OK in 1 word"}],
        "max_tokens": 5
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://paperchase.online"
        }
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
    print(f"Test call result: {content[:30]}")
    print("RESULT: API_WORKS")
except Exception as e:
    print(f"Test call FAILED: {str(e)[:100]}")
    print("RESULT: API_FAILS")
