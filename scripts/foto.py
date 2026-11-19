#!/usr/bin/env python3
"""Trova un'immagine per l'apertura: Wikimedia Commons, poi Pexels, poi un poster generato.

Uso: python3 -I scripts/foto.py OUT_DIR NOME "query 1" ["query 2" ...] [--poster | --no-poster]

Salva OUT_DIR/img/NOME.jpg e stampa su stdout il JSON del campo "photo" (o {} se non trova nulla).
Ordine delle fonti:
  1. Wikimedia Commons (licenze libere). L'IP del cloud è condiviso e Wikimedia risponde spesso 429:
     lo script rispetta Retry-After e aspetta fino a ~4 minuti in tutto. Se è impostata la variabile
     WIKIMEDIA_TOKEN (token OAuth 2 personale) le richieste sono autenticate e hanno limiti per utente.
  2. Pexels, solo se è impostata PEXELS_API_KEY (e la rete permette api.pexels.com, images.pexels.com).
  3. Poster generato in codice, in bicromia con il colore del giorno (NOME deve iniziare con AAAA-MM-GG).
     Attivo di default quando OUT_DIR è "quotidiano"; --poster / --no-poster lo forzano.
I messaggi diagnostici vanno su stderr.
"""
import datetime, hashlib, html, json, math, os, pathlib, random, re, sys, time
import urllib.error, urllib.parse, urllib.request

UA = "IlQuotidianoDellAI/1.1 (https://github.com/carlobeschi/ai-newspaper)"
OK = re.compile(r"^(cc0|public domain|pd\b|cc by(-sa)? ?[1-4]\.0|cc by(-sa)? ?2\.5)", re.I)
WAIT_BUDGET = 240  # secondi massimi di attesa per i 429, in tutto il run
_waited = 0


def log(*a):
    print(*a, file=sys.stderr)


def get(url, headers=None, tries=6):
    global _waited
    h = {"User-Agent": UA}
    h.update(headers or {})
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or i == tries - 1:
                raise
            try:
                wait = int(e.headers.get("Retry-After") or 0)
            except ValueError:
                wait = 0
            wait = max(wait, 10 * (i + 1)) + random.uniform(1, 5)
            if _waited + wait > WAIT_BUDGET:
                raise
            log(f"HTTP {e.code} da {urllib.parse.urlsplit(url).netloc}, attendo {wait:.0f}s")
            time.sleep(wait)
            _waited += wait


def text(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return html.unescape(re.sub(r"\s+", " ", s)).strip()


# ---------- 1. Wikimedia Commons ----------
def wikimedia(q):
    params = {"action": "query", "format": "json", "formatversion": "2",
              "generator": "search", "gsrnamespace": "6", "gsrlimit": "15",
              "gsrsearch": q + " filetype:bitmap", "prop": "imageinfo",
              "iiprop": "url|extmetadata|size", "iiurlwidth": "1280"}
    hdr = {}
    if os.environ.get("WIKIMEDIA_TOKEN"):
        hdr["Authorization"] = "Bearer " + os.environ["WIKIMEDIA_TOKEN"]
    d = json.loads(get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params), hdr))
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
        return thumb, {"author": artist[:80], "license": lic, "source": "Wikimedia Commons",
                       "page": ii.get("descriptionurl"),
                       "alt": desc[:200] or p["title"][5:].rsplit(".", 1)[0]}
    return None


# ---------- 2. Pexels ----------
def pexels(q):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None
    url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": q, "orientation": "landscape", "per_page": "15"})
    d = json.loads(get(url, {"Authorization": key}))
    for p in d.get("photos", []):
        w, h = p.get("width", 0), p.get("height", 0)
        if w < 1200 or not (1.2 <= w / max(h, 1) <= 2.2):
            continue
        src = p["src"]["original"] + "?auto=compress&cs=tinysrgb&w=1280"
        return src, {"author": (p.get("photographer") or "Autore sconosciuto")[:80],
                     "license": "Licenza Pexels", "source": "Pexels", "page": p.get("url"),
                     "alt": (p.get("alt") or q)[:200]}
    return None


# ---------- 3. Poster generato ----------
# stessi colori di DAY_COLORS in quotidiano/index.html (0 = domenica; la domenica usa l'accento arancio)
DAY = ["#ff6a3d", "#d2452b", "#1f7a4f", "#f2b632", "#6d3fc0", "#1739c9", "#0f6b78"]
INK, PAPER = "#16171b", "#f4f1e8"


def poster(name, seed, path, W=960, H=1200):
    from PIL import Image, ImageDraw
    date = datetime.date.fromisoformat(name[:10])
    day = DAY[(date.weekday() + 1) % 7]
    rnd = random.Random(hashlib.md5((name + seed).encode()).hexdigest())
    S = 2
    im = Image.new("RGB", (W * S, H * S), PAPER)
    g = ImageDraw.Draw(im)
    # grande disco a mezzatinta nel colore del giorno
    cx, cy = rnd.uniform(.4, .65) * W * S, rnd.uniform(.28, .45) * H * S
    R = rnd.uniform(.32, .42) * W * S
    step = 16 * S
    for y in range(0, H * S, step):
        for x in range(0, W * S, step):
            t = max(0, min(1, 1 - (math.hypot(x - cx, y - cy) - R * .55) / (R * .7)))
            r = step * .52 * t
            if r > 1:
                g.ellipse([x - r, y - r, x + r, y + r], fill=day)
    # anelli d'inchiostro
    for k in range(rnd.randint(3, 6)):
        rr = R * (.25 + .13 * k)
        a0 = rnd.uniform(0, 360)
        g.arc([cx - rr, cy - rr, cx + rr, cy + rr], a0, a0 + rnd.uniform(60, 220), fill=INK, width=5 * S)
    # fascia d'inchiostro inclinata
    a = math.tan(math.radians(rnd.choice([-14, -8, 8, 14])))
    y0, h = rnd.uniform(.6, .72) * H * S, rnd.uniform(.08, .13) * H * S
    g.polygon([(-50, y0), (W * S + 50, y0 + a * W * S), (W * S + 50, y0 + a * W * S + h), (-50, y0 + h)], fill=INK)
    # griglia di quadratini sotto la fascia
    bx, by, u = rnd.uniform(.06, .4) * W * S, max(y0, y0 + a * W * S) + h + 36 * S, 30 * S
    for i in range(rnd.randint(5, 9)):
        for j in range(3):
            if rnd.random() < .75:
                g.rectangle([bx + i * u, by + j * u, bx + i * u + 18 * S, by + j * u + 18 * S],
                            fill=INK if rnd.random() < .6 else day)
    # grana di stampa
    px = im.load()
    for _ in range(W * H // 12):
        px[rnd.randrange(W * S), rnd.randrange(H * S)] = (244, 241, 232) if rnd.random() < .5 else (40, 40, 44)
    im.resize((W, H), Image.LANCZOS).save(path, quality=80, optimize=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    out, name, queries = pathlib.Path(args[0]), args[1], args[2:]
    use_poster = "--poster" in flags or (out.name == "quotidiano" and "--no-poster" not in flags)
    img = out / "img" / f"{name}.jpg"
    for label, fn in (("Wikimedia", wikimedia), ("Pexels", pexels)):
        for q in queries:
            try:
                hit = fn(q)
            except Exception as e:
                log(f"{label}: ricerca fallita per {q!r}: {e}")
                break  # se la fonte è bloccata, inutile provare le altre query
            if not hit:
                continue
            src, meta = hit
            try:
                data = get(src)
            except Exception as e:
                log(f"{label}: download fallito: {e}")
                continue
            img.parent.mkdir(parents=True, exist_ok=True)
            img.write_bytes(data)
            print(json.dumps({"file": f"img/{name}.jpg", **meta}, ensure_ascii=False))
            return
    if use_poster:
        img.parent.mkdir(parents=True, exist_ok=True)
        poster(name, " ".join(queries), img)
        log("Nessuna foto trovata: generato il poster di riserva")
        print(json.dumps({"file": f"img/{name}.jpg", "illustration": True, "generated": True,
                          "alt": "Composizione astratta in bicromia: un disco a mezzatinta nel colore del giorno, "
                                 "anelli e una fascia d'inchiostro",
                          "caption": "Nessuna foto oggi: composizione astratta nel colore del giorno.",
                          "credit": "Grafica generata dal Quotidiano dell'AI.",
                          "author": "Grafica generata dal Quotidiano dell'AI",
                          "source": "Il Quotidiano dell'AI"}, ensure_ascii=False))
        return
    print("{}")


main()
