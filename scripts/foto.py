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
DAY_IT = ["arancione", "rossa", "verde", "gialla", "viola", "blu", "verde petrolio"]
INK, PAPER = "#16171b", "#f4f1e8"


def _halftone(g, W, H, step, col, t, jitter=False):
    """Retino: un punto ogni `step` px, raggio proporzionale a t(x, y) in [0, 1]."""
    for row, y in enumerate(range(0, H, step)):
        off = step // 2 if jitter and row % 2 else 0
        for x in range(-step, W + step, step):
            x2 = x + off
            r = step * .52 * max(0.0, min(1.0, t(x2, y)))
            if r > 1:
                g.ellipse([x2 - r, y - r, x2 + r, y + r], fill=col)


def _disco(g, W, H, day, rnd):
    cx, cy, R = rnd.uniform(.35, .65) * W, rnd.uniform(.28, .45) * H, rnd.uniform(.32, .42) * W
    _halftone(g, W, H, W // 60, day, lambda x, y: 1 - (math.hypot(x - cx, y - cy) - R * .55) / (R * .7))
    for k in range(rnd.randint(3, 6)):
        rr, a0 = R * (.25 + .13 * k), rnd.uniform(0, 360)
        g.arc([cx - rr, cy - rr, cx + rr, cy + rr], a0, a0 + rnd.uniform(60, 220), fill=INK, width=W // 96)
    a = math.tan(math.radians(rnd.choice([-14, -8, 8, 14])))
    y0, h = rnd.uniform(.6, .72) * H, rnd.uniform(.08, .13) * H
    g.polygon([(-50, y0), (W + 50, y0 + a * W), (W + 50, y0 + a * W + h), (-50, y0 + h)], fill=INK)
    bx, by, u = rnd.uniform(.06, .4) * W, max(y0, y0 + a * W) + h + W * .04, W * .031
    for i in range(rnd.randint(5, 9)):
        for j in range(3):
            if rnd.random() < .75:
                g.rectangle([bx + i * u, by + j * u, bx + i * u + u * .6, by + j * u + u * .6],
                            fill=INK if rnd.random() < .6 else day)
    return "un disco a mezzatinta, archi e una fascia d'inchiostro"


def _sole(g, W, H, day, rnd):
    hy, cx, R = rnd.uniform(.52, .62) * H, rnd.uniform(.3, .7) * W, rnd.uniform(.36, .48) * W
    _halftone(g, W, int(hy), W // 48, day,
              lambda x, y: 1.25 - math.hypot(x - cx, y - hy) / R if math.hypot(x - cx, y - hy) < R else 0)
    g.rectangle([0, hy, W, hy + H * .018], fill=INK)
    y, k = hy + H * .05, 0
    while y < H:
        th = H * (.008 + .005 * k)
        x0 = rnd.uniform(0, .25) * W if k % 2 else 0
        g.rectangle([x0, y, W - (rnd.uniform(0, .25) * W if k % 3 == 1 else 0), y + th], fill=INK)
        y += th + H * (.03 - min(.02, .003 * k)); k += 1
    r = W * rnd.uniform(.05, .08); sx, sy = rnd.choice([.12, .85]) * W, rnd.uniform(.1, .2) * H
    g.ellipse([sx - r, sy - r, sx + r, sy + r], fill=INK)
    return "un sole a mezzatinta che sorge su righe d'inchiostro"


def _diagonali(g, W, H, day, rnd):
    flip = rnd.random() < .5
    def t(x, y):
        u = ((W - x) if flip else x) / W * .55 + y / H * .45
        return u * 1.25 - .15
    _halftone(g, W, H, W // 40, day, t, jitter=True)
    ang = math.radians(rnd.choice([30, 38, 45, 52])) * (-1 if flip else 1)
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    c0 = rnd.uniform(-.15, .05) * W
    for i, (w, col) in enumerate([(rnd.uniform(.06, .1), INK), (rnd.uniform(.02, .035), INK),
                                  (rnd.uniform(.05, .08), day), (rnd.uniform(.015, .03), INK)]):
        c = c0 + i * W * rnd.uniform(.13, .2)
        L = W * 3
        px, py = W / 2 + nx * c, H / 2 + ny * c
        ww = w * W
        g.polygon([(px - dx * L, py - dy * L), (px + dx * L, py + dy * L),
                   (px + dx * L + nx * ww, py + dy * L + ny * ww), (px - dx * L + nx * ww, py - dy * L + ny * ww)], fill=col)
    return "fasce diagonali d'inchiostro su un fondo a mezzatinta"


def _griglia(g, W, H, day, rnd):
    cols, rows = 4, 5
    m = W * .07; cw = (W - 2 * m) / cols; ch = (H - 2 * m) / rows; s = min(cw, ch)
    for i in range(cols):
        for j in range(rows):
            x, y = m + i * cw, m + j * ch
            kind = rnd.choice(["q", "q", "h", "c", "dot", "sq", "none"])
            col = INK if rnd.random() < .55 else day
            if kind == "q":
                cx, cy = x + rnd.choice([0, s]), y + rnd.choice([0, s])
                start = {(x, y): 0, (x + s, y): 90, (x + s, y + s): 180, (x, y + s): 270}[(cx, cy)]
                g.pieslice([cx - s, cy - s, cx + s, cy + s], start, start + 90, fill=col)
            elif kind == "h":
                o = rnd.choice([0, 90, 180, 270])
                g.pieslice([x, y, x + s, y + s], o, o + 180, fill=col)
            elif kind == "c":
                g.ellipse([x + s * .12, y + s * .12, x + s * .88, y + s * .88], fill=col)
            elif kind == "dot":
                st = int(s / 7)
                _halftone(g, int(x + s), int(y + s), st, day,
                          lambda px, py, x=x, y=y: (1 - (py - y) / s) * 1.1 if x <= px <= x + s and y <= py <= y + s else 0)
            elif kind == "sq":
                g.rectangle([x + s * .2, y + s * .2, x + s * .8, y + s * .8], outline=col, width=int(W * .014))
    return "una griglia di quarti di cerchio, cerchi e quadrati"


def _rete(g, W, H, day, rnd):
    cx, cy, R = rnd.uniform(.35, .65) * W, rnd.uniform(.35, .6) * H, rnd.uniform(.35, .5) * W
    _halftone(g, W, H, W // 54, day, lambda x, y: math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * (R * .55) ** 2)) * 1.15)
    pts = [(rnd.uniform(.08, .92) * W, rnd.uniform(.08, .92) * H) for _ in range(rnd.randint(11, 16))]
    for a in pts:
        near = sorted(pts, key=lambda b: math.hypot(a[0] - b[0], a[1] - b[1]))[1:4]
        for b in near[:rnd.randint(2, 3)]:
            g.line([a, b], fill=INK, width=int(W * .006))
    for k, (x, y) in enumerate(pts):
        r = W * rnd.choice([.012, .018, .028, .045])
        if k % 4 == 0:
            g.ellipse([x - r * 1.8, y - r * 1.8, x + r * 1.8, y + r * 1.8], outline=INK, width=int(W * .006))
        g.ellipse([x - r, y - r, x + r, y + r], fill=INK if k % 3 else day)
    return "una rete di nodi e linee d'inchiostro su una nube a mezzatinta"


def _onde(g, W, H, day, rnd):
    f, ph, amp = rnd.uniform(2.5, 4.5), rnd.uniform(0, 6.3), rnd.uniform(.04, .09) * H
    _halftone(g, W, H, W // 50, day,
              lambda x, y: .5 + .6 * math.sin(f * 2 * math.pi * (y + amp * math.sin(x / W * 2 * math.pi * 1.3 + ph)) / H))
    R = W * rnd.uniform(.22, .3); cx = rnd.choice([.3, .5, .7]) * W; cy = rnd.uniform(.3, .65) * H
    g.ellipse([cx - R, cy - R, cx + R, cy + R], fill=INK)
    r2 = R * rnd.uniform(.35, .5); ox = rnd.uniform(-.3, .3) * R
    g.ellipse([cx + ox - r2, cy - r2, cx + ox + r2, cy + r2], fill=day)
    for k in range(3):
        x = rnd.uniform(.05, .95) * W
        g.rectangle([x, 0, x + W * .012, H], fill=INK)
    return "onde a mezzatinta e un grande cerchio d'inchiostro"


def _triangoli(g, W, H, day, rnd):
    ax = rnd.uniform(.2, .8) * W
    big = [(ax, H * rnd.uniform(.05, .15)), (W * rnd.uniform(-.1, .1), H * .92), (W * rnd.uniform(.9, 1.1), H * .92)]
    ia = lambda p, q, r: (p[0] * (q[1] - r[1]) + q[0] * (r[1] - p[1]) + r[0] * (p[1] - q[1]))
    def inside(x, y, T):
        a, b, c = T; s1 = ia((x, y), a, b); s2 = ia((x, y), b, c); s3 = ia((x, y), c, a)
        return (s1 >= 0 and s2 >= 0 and s3 >= 0) or (s1 <= 0 and s2 <= 0 and s3 <= 0)
    _halftone(g, W, H, W // 44, day, lambda x, y: (y / H) * 1.2 if inside(x, y, big) else 0)
    s = W * rnd.uniform(.3, .42); tx, ty = rnd.uniform(.2, .8) * W, rnd.uniform(.35, .65) * H
    up = rnd.random() < .5
    g.polygon([(tx, ty - s * .6 if up else ty + s * .6), (tx - s * .6, ty + s * .4 if up else ty - s * .4),
               (tx + s * .6, ty + s * .4 if up else ty - s * .4)], fill=INK)
    g.rectangle([0, H * .92, W, H * .935], fill=INK)
    for k in range(rnd.randint(4, 7)):
        y = H * (.05 + .035 * k); x0 = rnd.choice([.05, .6]) * W
        g.rectangle([x0, y, x0 + W * rnd.uniform(.12, .32), y + H * .007], fill=INK)
    return "triangoli sovrapposti d'inchiostro e a mezzatinta"


def _colonne(g, W, H, day, rnd):
    n = rnd.randint(6, 9); m = W * .08; cw = (W - 2 * m) / n; base = H * .82
    hs = [rnd.uniform(.15, .65) * H for _ in range(n)]
    if rnd.random() < .6:
        hs.sort(reverse=rnd.random() < .5)
    for i, h in enumerate(hs):
        x0, x1, top = m + i * cw + cw * .12, m + (i + 1) * cw - cw * .12, base - h
        if i % 3 == rnd.randint(0, 2):
            g.rectangle([x0, top, x1, base], fill=INK)
        else:
            _halftone(g, int(x1) + 1, int(base), int(cw / 5),
                      day, lambda x, y, x0=x0, x1=x1, top=top: (1.15 - (y - top) / h * .7) if x0 <= x <= x1 and y >= top else 0)
    g.rectangle([0, base, W, base + H * .02], fill=INK)
    R = W * rnd.uniform(.08, .13); cx = rnd.uniform(.2, .8) * W; cy = H * rnd.uniform(.08, .2) + R
    g.ellipse([cx - R, cy - R, cx + R, cy + R], fill=day)
    g.ellipse([cx - R, cy - R, cx + R, cy + R], outline=INK, width=int(W * .01))
    return "colonne a mezzatinta come un grafico, sotto un disco"


LAYOUTS = [_disco, _sole, _diagonali, _griglia, _rete, _onde, _triangoli, _colonne]


def poster(name, seed, path, W=960, H=1200):
    """Poster astratto in bicromia (inchiostro + colore del giorno) a mezzatinta.
    La composizione ruota con la data (passo 3 su 8): due giorni di fila non si somigliano
    e la coppia colore/composizione si ripete solo ogni 56 giorni. Restituisce l'alt."""
    from PIL import Image, ImageDraw
    date = datetime.date.fromisoformat(name[:10])
    wd = (date.weekday() + 1) % 7
    day = DAY[wd]
    rnd = random.Random(hashlib.md5((name + seed).encode()).hexdigest())
    S = 2
    im = Image.new("RGB", (W * S, H * S), PAPER)
    g = ImageDraw.Draw(im)
    desc = LAYOUTS[(date.toordinal() * 3) % len(LAYOUTS)](g, W * S, H * S, day, rnd)
    px = im.load()  # grana di stampa
    for _ in range(W * H // 12):
        px[rnd.randrange(W * S), rnd.randrange(H * S)] = (244, 241, 232) if rnd.random() < .5 else (40, 40, 44)
    im.resize((W, H), Image.LANCZOS).save(path, quality=80, optimize=True)
    return f"Composizione astratta in bicromia {DAY_IT[wd]} e nera: {desc}"


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
        alt = poster(name, " ".join(queries), img)
        log("Nessuna foto trovata: generato il poster di riserva")
        print(json.dumps({"file": f"img/{name}.jpg", "illustration": True, "generated": True, "alt": alt,
                          "credit": "Grafica generata dal Quotidiano dell'AI.",
                          "author": "Grafica generata dal Quotidiano dell'AI",
                          "source": "Il Quotidiano dell'AI"}, ensure_ascii=False))
        return
    print("{}")


main()
