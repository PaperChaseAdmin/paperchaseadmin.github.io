#!/usr/bin/env python3
"""Diagnose OpenRouter API - write result to file, no masking issues."""
import os, json, urllib.request, urllib.error, sys
from datetime import datetime

key = os.environ.get("OPENROUTER_API_KEY", "")
log = {"time": datetime.utcnow().isoformat(), "key_set": bool(key), "key_len": len(key), "tests": []}

if not key:
    log["result"] = "KEY_MISSING"
    json.dump(log, open("tmp_diag_result.json","w"))
    print("KEY_MISSING")
    sys.exit(1)

# Test 1: openrouter/free
try:
    payload = json.dumps({"model":"openrouter/free","messages":[{"role":"user","content":"Say OK in 1 word"}],"max_tokens":5,"temperature":0}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=payload, 
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","HTTP-Referer":"https://paperchase.online"})
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    content = resp.get("choices",[{}])[0].get("message",{}).get("content","")
    log["tests"].append({"model":"openrouter/free","status":"OK","content":content[:30]})
except Exception as e:
    log["tests"].append({"model":"openrouter/free","status":"FAIL","error":str(e)[:200]})

# Test 2: nemotron
try:
    payload = json.dumps({"model":"nvidia/nemotron-3-super-120b-a12b:free","messages":[{"role":"user","content":"Say OK in 1 word"}],"max_tokens":5,"temperature":0}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=payload,
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","HTTP-Referer":"https://paperchase.online"})
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    content = resp.get("choices",[{}])[0].get("message",{}).get("content","")
    log["tests"].append({"model":"nemotron","status":"OK","content":content[:30]})
except Exception as e:
    log["tests"].append({"model":"nemotron","status":"FAIL","error":str(e)[:200]})

log["result"] = "COMPLETE"
json.dump(log, open("tmp_diag_result.json","w"), indent=2)
print(f"Done: {log['result']} - {len(log['tests'])} tests")
