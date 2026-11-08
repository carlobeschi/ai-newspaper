#!/usr/bin/env python3
"""Genera i feed RSS del Quotidiano e del Settimanale dai rispettivi data/issues.json.

Uso: python3 scripts/feeds.py   (dalla radice del repository)
Scrive quotidiano/feed.xml e settimanale/feed.xml. Lo lancia anche la GitHub Action
.github/workflows/feeds.yml a ogni modifica dei dati.
"""
import json
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://carlobeschi.github.io/ai-newspaper/"
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
SIDE = {"In breve", "Weak signals", "What's hot on Twitter"}


def day_it(iso):
    d = datetime.fromisoformat(iso)
    return f"{GIORNI[d.weekday()]} {d.day} {MESI[d.month - 1]} {d.year}"


def pub_date(iso, hour):
    return format_datetime(datetime.fromisoformat(iso).replace(hour=hour, tzinfo=timezone.utc))


def plain(s):
    return re.sub(r"\[([^\]]+)\]\([^)\s]+\)", r"\1", s)


def parse_daily(md):
    """Stesse regole di quotidiano/index.html: k conta i titoli in grassetto in ordine."""
    items, section, k, cur = [], None, 0, None
    for raw in md.split("\n"):
        line = raw.strip()
        if line.startswith("## "):
            section, cur = line[3:].strip(), None
            continue
        if section is None:
            continue
        if not line:
            cur = None
            continue
        m = re.match(r"^\*\*(.+)\*\*$", line)
        if m:
            cur = {"title": m.group(1), "k": k, "section": section, "body": ""}
            items.append(cur)
            k += 1
            continue
        if line.startswith("- "):
            continue
        if cur is not None:
            cur["body"] += (" " if cur["body"] else "") + line
    for i in items:
        body = re.split(r"\s—\s(?:fonti:|\[fonte\])", i["body"])[0]
        body = re.sub(r"\s\[[^\]]+\]\([^)]+\)\s*$", "", body)
        i["text"] = plain(body).strip()
    return items


def rss(title, link, desc, items):
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">', "<channel>",
           f"<title>{escape(title)}</title>", f"<link>{link}</link>",
           f'<atom:link href="{link}feed.xml" rel="self" type="application/rss+xml"/>',
           f"<description>{escape(desc)}</description>", "<language>it</language>"]
    for it in items:
        out += ["<item>", f"<title>{escape(it['title'])}</title>", f"<link>{escape(it['link'])}</link>",
                f'<guid isPermaLink="false">{escape(it["guid"])}</guid>', f"<pubDate>{it['date']}</pubDate>",
                f"<description>{escape(it['html'])}</description>", "</item>"]
    out += ["</channel>", "</rss>", ""]
    return "\n".join(out)


def daily():
    base = SITE + "quotidiano/"
    issues = json.loads((ROOT / "quotidiano/data/issues.json").read_text())["issues"]
    issues.sort(key=lambda x: x["date"], reverse=True)
    items = []
    for x in issues[:30]:
        stories = parse_daily(x["markdown"])
        main = [s for s in stories if s["section"] not in SIDE] or stories
        if not main:
            continue
        lead = main[0]
        lis = "".join(f'<li><a href="{base}#n-{x["date"]}-{s["k"]}">{escape(s["title"])}</a></li>' for s in stories)
        items.append({
            "title": f"{day_it(x['date']).capitalize()}: {lead['title']}",
            "link": f"{base}#e-{x['date']}", "guid": f"quotidiano-{x['date']}",
            "date": pub_date(x["date"], 6),
            "html": f"<p>{escape(lead['text'])}</p><p>In questa edizione:</p><ul>{lis}</ul>",
        })
    (ROOT / "quotidiano/feed.xml").write_text(rss(
        "Il Quotidiano dell'AI", base,
        "Le notizie sull'intelligenza artificiale, ogni mattina. Basato sulla newsletter Daily Brief di PierG.", items))


def weekly():
    base = SITE + "settimanale/"
    issues = json.loads((ROOT / "settimanale/data/issues.json").read_text())["issues"]
    issues.sort(key=lambda x: x["date"], reverse=True)
    items = []
    for e in issues[:30]:
        arts = [e["cover"], *e.get("features", []), e["opinion"]]
        lis = "".join(f'<li><a href="{base}#a-{e["date"]}-{a["id"]}">{escape(a["title"])}</a>: {escape(a["standfirst"])}</li>' for a in arts)
        items.append({
            "title": f"N. {e['n']}, {e['range']}: {e['cover']['title']}",
            "link": f"{base}#n-{e['date']}", "guid": f"settimanale-{e['date']}",
            "date": pub_date(e["date"], 7),
            "html": f"<p>{escape(e['cover']['standfirst'])}</p><p>In questo numero:</p><ul>{lis}</ul>",
        })
    (ROOT / "settimanale/feed.xml").write_text(rss(
        "Il Settimanale dell'AI", base,
        "Il riassunto ragionato della settimana dell'intelligenza artificiale, ogni domenica.", items))


if __name__ == "__main__":
    daily()
    weekly()
