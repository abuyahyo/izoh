"""
Generate sw.js from build/sw.template.js by replacing __CACHE_VERSION__
with a hash of the app shell content. Run this before every commit
that changes index.html / app.js / style.css / manifest.json.
"""
import hashlib
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
TEMPLATE = ROOT / "build" / "sw.template.js"
OUT = ROOT / "sw.js"
WATCH = [
    ROOT / "index.html",
    ROOT / "style.css",
    ROOT / "app.js",
    ROOT / "manifest.json",
]


def main():
    h = hashlib.sha1()
    for f in WATCH:
        h.update(f.read_bytes())
    # Also hash the template itself so SW logic changes bump version too
    h.update(TEMPLATE.read_bytes())
    version = h.hexdigest()[:12]

    text = TEMPLATE.read_text(encoding="utf-8")
    text = text.replace("__CACHE_VERSION__", version)
    OUT.write_text(text, encoding="utf-8")
    print(f"[+] {OUT.name} written with CACHE_VERSION = {version}")


if __name__ == "__main__":
    main()
