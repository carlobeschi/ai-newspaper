#!/usr/bin/env python3
"""Trova e scarica una foto con licenza libera da Wikimedia Commons.

Uso: python3 -I foto.py OUT_DIR DATA "query 1" ["query 2" ...]
Prova le query in ordine; salva OUT_DIR/img/DATA.jpg e stampa su stdout il JSON
del campo "photo" da mettere nell'edizione di issues.json (o {} se non trova nulla).
"""
import json, re, sys, html, urllib.parse, urllib.request, urllib.error, pathlib

UA = "IlQuotidianoDellAI/1.0 (https://github.com/carlobeschi/ai-newspaper)"
OK = re.compile(r"^(cc0|public domain|pd\b|cc by(-sa)? ?[1-4]\.0|cc by(-sa)? ?2\.5)", re.I)

def get(url, tries=4):
    import time
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == tries - 1:
                raise
            time.sleep(8 * (i + 1))

def text(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return html.unescape(re.sub(r"\s+", " ", s)).strip()

def search(q):
    params = {"action": "query", "format": "json", "formatversion": "2",
              "generator": "search", "gsrnamespace": "6", "gsrlimit": "15",
              "gsrsearch": q + " filetype:bitmap", "prop": "imageinfo",
              "iiprop": "url|extmetadata|size", "iiurlwidth": "1280"}
    d = json.loads(get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)))
    pages = sorted(d.get("query", {}).get("pages", []), key=lambda p: p.get("index", 99))
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        m = ii.get("extmetadata", {})
        lic = text(m.get("LicenseShortName", {}).get("value"))
        w, h = ii.get("width", 0), ii.get("height", 0)
        if not OK.match(lic) or w < 900 or not (1.2 <= w / max(h, 1) <= 2.2):
            continue
        orig = ii.get("url", "").split("?", 1)[0]
        if not orig.lower().endswith((".jpg", ".jpeg")) or "/wikipedia/commons/" not in orig:
            continue
        # miniatura standard su upload.wikimedia.org: .../commons/thumb/a/ab/Nome.jpg/1280px-Nome.jpg
        name = orig.rsplit("/", 1)[1]
        thumb = orig.replace("/wikipedia/commons/", "/wikipedia/commons/thumb/", 1) + f"/1280px-{name}"
        artist = text(m.get("Artist", {}).get("value")) or "Autore sconosciuto"
        desc = text(m.get("ImageDescription", {}).get("value"))
        return {"thumb": thumb, "author": artist[:80], "license": lic,
                "page": ii.get("descriptionurl"), "title": p["title"][5:].rsplit(".", 1)[0],
                "desc": desc[:200]}
    return None

def main():
    out, date, queries = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3:]
    for q in queries:
        try:
            hit = search(q)
        except Exception as e:
            print(f"ricerca fallita per {q!r}: {e}", file=sys.stderr); continue
        if not hit:
            continue
        (out / "img").mkdir(parents=True, exist_ok=True)
        (out / "img" / f"{date}.jpg").write_bytes(get(hit["thumb"]))
        print(json.dumps({"file": f"img/{date}.jpg", "author": hit["author"], "license": hit["license"],
                          "source": "Wikimedia Commons", "page": hit["page"],
                          "alt": hit["desc"] or hit["title"]}, ensure_ascii=False))
        return
    print("{}")

main()
