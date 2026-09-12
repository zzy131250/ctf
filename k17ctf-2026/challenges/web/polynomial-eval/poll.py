import requests, time, json, sys
TOK="<webhook-token>"
deadline=time.time()+90
seen=set()
while time.time()<deadline:
    try:
        r=requests.get(f"https://webhook.site/token/{TOK}/requests?sorting=newest", timeout=20)
        d=r.json()
        for it in d.get('data',[]):
            k=it['uuid']
            if k in seen: continue
            seen.add(k)
            print("HIT:", it['method'], it['url'])
            print("   UA:", it.get('headers',{}).get('user-agent'))
            print("   REF:", it.get('headers',{}).get('referer'))
            print("   IP:", it.get('ip'))
            sys.stdout.flush()
    except Exception as e:
        print("poll err", e)
    time.sleep(4)
print("done")
