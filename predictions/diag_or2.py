#!/usr/bin/env python3
import os, json, urllib.request
key = os.environ.get("OPENROUTER_API_KEY", "")
print(f"KEY_SET={bool(key)}")
print(f"KEY_LEN={len(key)}")
print(f"KEY_PREFIX={key[:10] if key else 'NONE'}")
if not key:
    exit(0)

# Test openrouter/free
try:
    payload = json.dumps({"model":"openrouter/free","messages":[{"role":"user","content":"OK"}],"max_tokens":5}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=payload,
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","HTTP-Referer":"https://paperchase.online"})
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    print(f"FREE_MODEL={resp.get('choices',[{}])[0].get('message',{}).get('content','')[:30]}")
except Exception as e:
    print(f"FREE_MODEL_ERROR={str(e)[:200]}")

# Test nemotron
try:
    payload = json.dumps({"model":"nvidia/nemotron-3-super-120b-a12b:free","messages":[{"role":"user","content":"OK"}],"max_tokens":5}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=payload,
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","HTTP-Referer":"https://paperchase.online"})
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    print(f"NEMOTRON={resp.get('choices',[{}])[0].get('message',{}).get('content','')[:30]}")
except Exception as e:
    print(f"NEMOTRON_ERROR={str(e)[:200]}")
