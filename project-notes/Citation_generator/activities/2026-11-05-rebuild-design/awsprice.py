"""Read AWS's public price list (no credentials). Region us-east-2 (Ohio). Prints selected unit prices."""
import json
import re
import sys
import urllib.request

BASE = "https://pricing.us-east-1.amazonaws.com"


def get(path):
    return json.load(urllib.request.urlopen(BASE + path, timeout=120))


idx = get("/offers/v1.0/aws/index.json")["offers"]
want = {}
for code in idx:
    for key in ("Vector", "Cognito", "AWSLambda", "ApiGateway", "AmazonDynamoDB", "AmazonSQS", "AmazonCloudWatch",
                "AmazonCloudFront", "AWSSecretsManager", "AmazonRoute53", "awswaf", "AmazonS3", "AmazonBedrock", "AWSSystemsManager"):
        if key.lower() in code.lower():
            want[code] = idx[code]["currentRegionIndexUrl"] if "currentRegionIndexUrl" in idx[code] else idx[code]["currentVersionUrl"]
print("service codes found:", sorted(want))


def region_file(code):
    url = idx[code].get("currentRegionIndexUrl")
    if not url:
        return None
    regions = get(url)["regions"]
    r = regions.get("us-east-2") or regions.get("us-east-1")
    return r["currentVersionUrl"]


def show(code, pattern, limit=14, field="usagetype"):
    path = region_file(code)
    if not path:
        print(code, "no regional file")
        return
    d = get(path)
    n = 0
    for sku, p in d["products"].items():
        a = p.get("attributes", {})
        text = " | ".join(str(v) for v in a.values())
        if re.search(pattern, text, re.I):
            terms = d["terms"].get("OnDemand", {}).get(sku, {})
            for t in terms.values():
                for pd in t["priceDimensions"].values():
                    price = pd["pricePerUnit"].get("USD")
                    if price and float(price) > 0:
                        print(f"  {code:18} {a.get(field,'')[:46]:46} {a.get('group','')[:28]:28} ${float(price):.10g} per {pd['unit']} (begin {pd.get('beginRange')})  {pd['description'][:60]}")
                        n += 1
        if n >= limit:
            break
    if n == 0:
        print(" ", code, "no match for", pattern)


for code, pat, lim in [
    ("AmazonS3Vectors", r".", 24),
    ("AWSLambda", r"Lambda-GB-Second|Request", 8),
    ("AmazonApiGateway", r"HTTP|APIGateway.*Requests|ApiGatewayHttpApi", 8),
    ("AmazonDynamoDB", r"ReadRequestUnits|WriteRequestUnits|TimedStorage-ByteHrs", 8),
    ("AmazonCognito", r"MAU|Tier|User Pool|Lite|Essentials", 10),
]:
    if code in want:
        show(code, pat, lim)
    else:
        print(code, "not in index; closest:", [c for c in want if code[6:10].lower() in c.lower()])
