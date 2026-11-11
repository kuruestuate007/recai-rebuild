import json
import re
import urllib.request

BASE = "https://pricing.us-east-1.amazonaws.com"


def get(path):
    return json.load(urllib.request.urlopen(BASE + path, timeout=180))


idx = get("/offers/v1.0/aws/index.json")["offers"]


def scan(code, pattern, limit=20, region="us-east-2"):
    url = idx[code].get("currentRegionIndexUrl")
    regions = get(url)["regions"]
    r = regions.get(region) or regions.get("us-east-1")
    d = get(r["currentVersionUrl"])
    n = 0
    for sku, p in d["products"].items():
        a = p.get("attributes", {})
        text = " | ".join(str(v) for v in a.values())
        if re.search(pattern, text, re.I):
            for t in d["terms"].get("OnDemand", {}).get(sku, {}).values():
                for pd in t["priceDimensions"].values():
                    price = pd["pricePerUnit"].get("USD")
                    if price is not None and float(price) > 0:
                        print(f"  {code}: {a.get('usagetype','')[:44]:44} ${float(price):.8g} per {pd['unit']} | {pd['description'][:90]}")
                        n += 1
        if n >= limit:
            break
    print(f"  ({code}: {n} rows for /{pattern}/ in {region})")


for code, pat in (("AmazonS3", r"vector"), ("AmazonBedrockFoundationModels", r"titan.*embed|embed.*titan|rerank"), ("AmazonBedrock", r"titan.*embed|rerank")):
    if code in idx:
        try:
            scan(code, pat, 14)
        except Exception as e:
            print(" ", code, "failed:", repr(e)[:100])
    else:
        print(" ", code, "not in index")
print("services mentioning vector:", [c for c in idx if "vector" in c.lower()])
