"""Test redirect handling with Wiktionary API."""
import json, time, urllib.request, urllib.parse

API_URL = "https://uz.wiktionary.org/w/api.php"

def api(params):
    url = API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "IzohDict/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

results = []

# Test na'matak with parse + redirects
results.append("=== Test 1: na'matak with parse+redirects ===")
params = {
    "action": "parse",
    "page": "na'matak",
    "format": "json",
    "prop": "text|categories",
    "utf8": 1,
    "redirects": 1,
}
data = api(params)
parse = data.get("parse", {})
results.append(f"  pageid: {parse.get('pageid')}")
results.append(f"  title: {parse.get('title')}")
results.append(f"  redirects: {parse.get('redirects')}")
# Check if redirect page
html = parse.get("text", {}).get("*", "")
if "redirectMsg" in html:
    results.append("  => Is a redirect page!")
else:
    results.append(f"  => Normal page (html len={len(html)})")

# Test na'matak with query + redirects
results.append("\n=== Test 2: na'matak with query+redirects ===")
params2 = {
    "action": "query",
    "titles": "na'matak",
    "format": "json",
    "utf8": 1,
    "redirects": 1,
}
data2 = api(params2)
query = data2.get("query", {})
redirects = query.get("redirects", [])
results.append(f"  redirects: {json.dumps(redirects, ensure_ascii=False)}")
normalized = query.get("normalized", [])
results.append(f"  normalized: {json.dumps(normalized, ensure_ascii=False)}")
pages = query.get("pages", {})
for pid, info in pages.items():
    results.append(f"  page: pid={pid}, title={info.get('title')}, ns={info.get('ns')}")
    results.append(f"    missing: {info.get('missing', False)}")
    results.append(f"    invalid: {info.get('invalid', False)}")

# Test naʼmatak (with the correct apostrophe) 
results.append("\n=== Test 3: naʼmatak (correct) ===")
params3 = {
    "action": "parse",
    "page": "naʼmatak",
    "format": "json",
    "prop": "text|categories",
    "utf8": 1,
    "redirects": 1,
}
data3 = api(params3)
parse3 = data3.get("parse", {})
results.append(f"  pageid: {parse3.get('pageid')}")
results.append(f"  title: {parse3.get('title')}")
html3 = parse3.get("text", {}).get("*", "")
if "redirectMsg" in html3:
    results.append("  => Is a redirect page!")
else:
    results.append(f"  => Normal page (html len={len(html3)})")

# Now check: can we list all Uzbek words?
# The category Oʻzbek_tili has 42121 pages - let's get the full list with cmcontinue
results.append("\n=== Test 4: List all pages in Oʻzbek_tili (paginated) ===")
all_pages = []
cmcontinue = None
total = 0
limit = 500
while True:
    params4 = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": "Category:Oʻzbek_tili",
        "cmtype": "page",
        "cmlimit": limit,
        "format": "json",
        "utf8": 1,
    }
    if cmcontinue:
        params4["cmcontinue"] = cmcontinue
    try:
        data4 = api(params4)
    except Exception as e:
        results.append(f"  Error at page {total}: {e}")
        break
    query4 = data4.get("query", {})
    members = query4.get("categorymembers", [])
    all_pages.extend(members)
    total += len(members)
    results.append(f"  Got {total} pages so far")
    cont = data4.get("continue", {})
    cmcontinue = cont.get("cmcontinue")
    if not cmcontinue:
        break
    time.sleep(0.3)

results.append(f"\nTotal pages in category: {len(all_pages)}")
# Write all titles to file
titles = [p.get("title") for p in all_pages]
with open(r'C:\Users\abu_y\izoh\wiktionary_all_titles.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(titles))
results.append(f"Saved {len(titles)} titles")

with open(r'C:\Users\abu_y\izoh\wiktionary_redirect_test.json', 'w', encoding='utf-8') as f:
    json.dump({"results": results}, f, ensure_ascii=False, indent=2)
print('Written')
