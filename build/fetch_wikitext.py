"""Fetch raw wikitext of an Uzbek entry to understand wikitext structure."""
import json, urllib.request, urllib.parse

API_URL = "https://uz.wiktionary.org/w/api.php"

def api(params):
    url = API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "IzohDict/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

# Get raw wikitext of "non"
params = {
    "action": "parse",
    "page": "non",
    "format": "json",
    "prop": "wikitext",
    "utf8": 1,
}
data = api(params)
wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
with open(r'C:\Users\abu_y\izoh\wiktionary_non_wikitext.txt', 'w', encoding='utf-8') as f:
    f.write(wikitext)
print(f"Written {len(wikitext)} chars")

# Also try na'matak
params2 = {
    "action": "parse",
    "page": "na'matak",
    "format": "json",
    "prop": "wikitext",
    "utf8": 1,
    "redirects": 1,
}
data2 = api(params2)
wikitext2 = data2.get("parse", {}).get("wikitext", {}).get("*", "")
with open(r'C:\Users\abu_y\izoh\wiktionary_namatak_wikitext.txt', 'w', encoding='utf-8') as f:
    f.write(wikitext2)
print(f"Written namatak: {len(wikitext2)} chars")

# Also check the dump format - get a stub
params3 = {
    "action": "parse",
    "page": "non",
    "format": "json",
    "prop": "text",
    "utf8": 1,
}
data3 = api(params3)
html = data3.get("parse", {}).get("text", {}).get("*", "")
with open(r'C:\Users\abu_y\izoh\wiktionary_non_html.txt', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Written HTML: {len(html)} chars")
