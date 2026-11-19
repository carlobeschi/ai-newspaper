"""Builds en/quotidiano/index.html from quotidiano/index.html (string swaps). Run from repo root."""
import re, sys
s = open('quotidiano/index.html').read()
R = [
('<html lang="it">', '<html lang="en">'),
("<title>Il Quotidiano dell'AI</title>", "<title>The AI Daily</title>"),
('content="Le notizie sull\'intelligenza artificiale, ogni mattina, impaginate come un manifesto. Un\'idea di Carlo, generata da Claude, basata sulla newsletter Daily Brief di PierG."', 'content="Artificial intelligence news every morning, laid out like a poster. English edition of Il Quotidiano dell\'AI, based on PierG\'s Daily Brief newsletter."'),
('content="I giornali dell\'AI"', 'content="The AI papers"'),
('<meta property="og:title" content="Il Quotidiano dell\'AI">', '<meta property="og:title" content="The AI Daily">'),
('content="Le notizie sull\'intelligenza artificiale, ogni mattina. Basato sulla newsletter Daily Brief di PierG."', 'content="Artificial intelligence news, every morning. Based on PierG\'s Daily Brief newsletter."'),
('content="https://carlobeschi.github.io/ai-newspaper/quotidiano/">', 'content="https://carlobeschi.github.io/ai-newspaper/en/quotidiano/">'),
('content="it_IT"', 'content="en_GB"'),
('<link rel="alternate" type="application/rss+xml" title="Il Quotidiano dell\'AI" href="feed.xml">\n', ''),
('../assets/', '../../assets/'),
# header / credit
('<a class="who" href="../chi-siamo/">Chi siamo</a>Un\'idea di Carlo, generata da Claude, basata sulla newsletter <em>Daily Brief</em> di PierG (Piergiorgio Grossi).</span>',
 '<a class="who" href="../chi-siamo/">About</a>English edition · an idea by Carlo, written by Claude, based on the <em>Daily Brief</em> newsletter by PierG (Piergiorgio Grossi).</span>'),
('aria-label="Tema della pagina">Tema: auto</button><a href="../en/quotidiano/" hreflang="en" lang="en" onclick="this.href=this.href.split(\'#\')[0]+location.hash">English</a><a href="../settimanale/">Il Settimanale dell\'AI →</a>',
 'aria-label="Page theme">Theme: auto</button><a href="../../quotidiano/" hreflang="it" lang="it" onclick="this.href=this.href.split(\'#\')[0]+location.hash">Italiano</a><a href="../settimanale/">AI Weekly →</a>'),
('alt="" onerror="this.remove()">Il Quotidiano dell\'AI</a>', 'alt="" onerror="this.remove()">The AI Daily</a>'),
('aria-label="Sezioni"', 'aria-label="Sections"'),
('<strong id="today">Edizione del giorno</strong>', '<strong id="today">Today\'s edition</strong>'),
('aria-label="Edizioni"', 'aria-label="Editions"'),
('<label for="q">Cerca</label>', '<label for="q">Search</label>'),
('placeholder="Nell\'archivio, es. Nvidia"', 'placeholder="In the archive, e.g. Nvidia"'),
('Caricamento dell\'edizione…', 'Loading the edition…'),
# footer
('<h4>Come è fatto</h4>', '<h4>How it is made</h4>'),
]
for a, b in R:
    if a not in s: print('MISSING', a[:70])
    s = s.replace(a, b)
# footer paragraphs
a = s.index('<h4>How it is made</h4>'); b = s.index('</section>', a)
s = s[:a] + '''<h4>How it is made</h4>
    <p>Every morning Claude reads the <em>Daily Brief</em> newsletter by Piergiorgio Grossi (PierG), which gathers and sums up in Italian the previous day's artificial intelligence news, and lays it out like a poster: one lead story, the number of the day, the rest in an index. This English edition is written by Claude from the Italian one and, where the original English source can be read, checked against it. Every story links to its original sources.</p>
    <p>Each day of the week has its own colour. Lead images are Midjourney illustrations or Wikimedia Commons photos under free licences, printed in two colours: they are stock images chosen for the subject, not photos of the event.</p>
    <p>The Italian edition is <a href="../../quotidiano/">Il Quotidiano dell'AI</a>; on Sundays there is <a href="../settimanale/">AI Weekly</a>.</p>
    <p>Keyboard: <kbd>/</kbd> to search, <kbd>J</kbd> and <kbd>K</kbd> (or the arrow keys) to move to the next or previous story.</p>
    <p>The site only remembers, in your own browser, the last edition you saw and the stories you opened, to flag what is new. It sends this to no one.</p>
  ''' + s[b:]
R2 = [
('<h4>Sezioni</h4>', '<h4>Sections</h4>'), ('<h4>Argomenti</h4>\n    <ul id="foot-topics">', '<h4>Topics</h4>\n    <ul id="foot-topics">'),
("<span>Il Quotidiano dell'AI · un'idea di Carlo, generata da Claude<span", "<span>The AI Daily · an idea by Carlo, written by Claude<span"),
# sections
('{ it: "Economia & Startup",', '{ it: "Business & Startups",'), ('{ it: "Modelli & Agenti",', '{ it: "Models & Agents",'),
('{ it: "AI in locale",', '{ it: "Local AI",'), ('{ it: "Imprese che cambiano",', '{ it: "Companies changing",'),
('{ it: "Altre notizie",', '{ it: "Other news",'), ('"In breve":                       { it: "In breve",', '"In breve":                       { it: "In brief",'),
('{ it: "Segnali deboli",', '{ it: "Weak signals",'), ('{ it: "Dai social",', '{ it: "From social media",'),
# topics
('it: "Nvidia e chip",        re: /Nvidia|\\bGPU|\\bTPU|semicondutt|', 'it: "Nvidia and chips",     re: /Nvidia|\\bGPU|\\bTPU|semicondu|'),
('it: "Musk e xAI",', 'it: "Musk and xAI",'),
('it: "Cina",                 re: /DeepSeek|\\bCina\\b|cines[ei]|', 'it: "China",                re: /DeepSeek|\\bChina\\b|Chinese|'),
('it: "Data center ed energia", re: /data cent|centr[oi] (dati|di calcolo)|gigawatt|\\bGW\\b|energ|elettric|nuclear/i', 'it: "Data centres and energy", re: /data cent|gigawatt|\\bGW\\b|energ|electric|power grid|nuclear/i'),
('it: "Agenti",               re: /\\bagent[ei]|agentic/i', 'it: "Agents",               re: /\\bagents?\\b|agentic/i'),
('it: "Regole e politica",    re: /regol|normativ|\\blegge\\b|govern|Washington|Casa Bianca|Congresso|Commissione europea|antitrust|tribunal|export|elezion|midterm/i', 'it: "Rules and politics",   re: /regulat|\\blaw\\b|\\bbill\\b|govern|Washington|White House|Congress|European Commission|antitrust|court|lawsuit|sues\\b|export|election|midterm/i'),
('it: "Modelli aperti e locali", re: /in locale|local LLM|open[- ]?source|pesi aperti|', 'it: "Open and local models", re: /locally|local LLM|open[- ]?source|'),
('it: "Soldi e investimenti", re: /miliard|investiment|\\bround\\b|valutazion|\\bIPO\\b|bolla|ricavi|finanzi|debito/i', 'it: "Money and investment", re: /billion|invest|\\bround\\b|valuation|\\bIPO\\b|bubble|revenue|financ|debt/i'),
('it: "Lavoro e imprese",     re: /lavorator|dipendent|licenzi|occupazion|produttivit|assunzion|\\bteam\\b/i', 'it: "Work and business",    re: /worker|employee|layoff|\\bjobs?\\b|productivit|hiring|\\bteams?\\b/i'),
# heuristics
('const WHY = /\\b(dimostr|segnal[ai]|conferm|signific|potrebb|rischi|indica\\b|indicano|evidenzi|suggerisc|mostra|spinge|costring|rappresent|sottoline|implic|obblig|testimon|apre (la strada|le porte|a)|rende |rendono|permett|consente|consentono|alimenta|priva|trasform|ridefinisc|mette in|accelera|cambia\\b)/i;',
 'const WHY = /\\b(shows?|signals?|confirms?|means|could|risks?|indicates?|highlights?|suggests?|pushes|forces?|represents?|underlines?|implies|requires|opens (the way|the door|up)|makes |allows?|enables?|fuels?|deprives|transforms?|redefines?|puts |accelerates?|changes)\\b/i;'),
('(?:miliardi|milioni|mila|%|per cento|GW|MW|gigawatt|token al secondo|dollari|euro|volte)', '(?:trillion|billion|million|thousand|%|per cent|GW|MW|gigawatts?|tokens per second|dollars|euros|times|bn|m)'),
('(?:tra|dopo|mentre|per|con|contro|grazie a|ma|e il|e la)', '(?:as|after|while|for|with|against|thanks to|but|amid|to)'),
# rendering strings
('Ne parla il Settimanale n. ${w.n} →', 'Covered in AI Weekly No. ${w.n} →'),
('min di lettura</span>', 'min read</span>'),
('data-listen="${sid(date, i.k)}">Ascolta</button>', 'data-listen="${sid(date, i.k)}">Listen</button>'),
('data-link="${sid(date, i.k)}">Copia link</button>', 'data-link="${sid(date, i.k)}">Copy link</button>'),
('`${a}post originale${b}`', '`${a}original post${b}`'),
('/(<a [^>]*>)\\s*fonte\\s*(<\\/a>)/gi', '/(<a [^>]*>)\\s*(?:fonte|source)\\s*(<\\/a>)/gi'),
('${n > 1 ? "Fonti" : "Fonte"}:', '${n > 1 ? "Sources" : "Source"}:'),
('title="L\'hai già aperta">✓ letta</span>', 'title="You have already opened it">✓ read</span>'),
('<b>Perché conta</b>', '<b>Why it matters</b>'),
('"Illustrazione generata con Midjourney."', '"Illustration generated with Midjourney."'),
('Immagine di riserva, generata con Midjourney: questa notizia non ha una foto.', 'Fallback image, generated with Midjourney: this story has no photo.'),
('${esc(ph.caption || "")} Foto: <a', '${esc(ph.caption || "")} Photo: <a'),
('· Apertura${readMark', '· Lead story${readMark'),
('<span>Il resto dell\'edizione</span><span>${rest.length} ${rest.length === 1 ? "notizia" : "notizie"}</span>', '<span>The rest of the edition</span><span>${rest.length} ${rest.length === 1 ? "story" : "stories"}</span>'),
('<span aria-hidden="true">Leggi <span class="go">', '<span aria-hidden="true">Read <span class="go">'),
('<span class="src">Fonte: <a href="${esc(url)}"', '<span class="src">Source: <a href="${esc(url)}"'),
('<b>Bentornato</b><span>Dalla tua ultima visita (${esc(short(PREV_SEEN))}) ${fresh.length === 1 ? "è uscita 1 edizione nuova" : `sono uscite ${fresh.length} edizioni nuove`}: ${links}</span><button type="button" data-close-since>Chiudi ✕</button>',
 '<b>Welcome back</b><span>Since your last visit (${esc(short(PREV_SEEN))}) ${fresh.length === 1 ? "1 new edition has come out" : `${fresh.length} new editions have come out`}: ${links}</span><button type="button" data-close-since>Close ✕</button>'),
('aria-label="Il numero del giorno"', 'aria-label="The number of the day"'),
('<span class="k">Il numero del giorno · ', '<span class="k">The number of the day · '),
('${esc(f.s)} <a href="#${sid(issue.date, f.i.k)}">Leggi →</a>', '${esc(f.s)} <a href="#${sid(issue.date, f.i.k)}">Read →</a>'),
('<h4>Il numero del giorno</h4>', '<h4>The number of the day</h4>'),
('<section class="box week"><h4>Argomenti</h4>', '<section class="box week"><h4>Topics</h4>'),
('<h4>Dal Settimanale</h4>', '<h4>From AI Weekly</h4>'),
('<span class="n">N. ${esc(w.n)}', '<span class="n">No. ${esc(w.n)}'),
('c.title || "Il Settimanale dell\'AI"', 'c.title || "AI Weekly"'),
('<h4>I temi della settimana</h4>', '<h4>This week\'s themes</h4>'),
('<p>Gli argomenti più presenti nelle ${recent.length === 1 ? "notizie di oggi" : "ultime " + recent.length + " edizioni"}.</p>', '<p>The topics that came up most in ${recent.length === 1 ? "today\'s news" : "the last " + recent.length + " editions"}.</p>'),
('aria-label="Nella stessa edizione"', 'aria-label="In the same edition"'),
('<span>← Precedente</span>', '<span>← Previous</span>'), ('<span>Successiva →</span>', '<span>Next →</span>'),
('<h3>Sullo stesso argomento</h3>', '<h3>On the same topic</h3>'),
('<b class="lbl">Il fatto</b>', '<b class="lbl">The fact</b>'), ('<b class="lbl">Nel dettaglio</b>', '<b class="lbl">In detail</b>'),
('<b class="lbl">Perché conta</b>', '<b class="lbl">Why it matters</b>'),
("← Torna all'edizione di ${esc(cap(fmtDay(date)))}", "← Back to the edition of ${esc(cap(fmtDay(date)))}"),
("document.title = i.title + \" · Il Quotidiano dell'AI\";", "document.title = i.title + \" · The AI Daily\";"),
("← Torna all'edizione di oggi</a><p class=\"kicker\">Argomento</p>", "← Back to today's edition</a><p class=\"kicker\">Topic</p>"),
('${n} ${n === 1 ? "notizia" : "notizie"} in ${ISSUES.length} edizioni in archivio</p>${html || `<p class="empty">Nessuna notizia su questo argomento.</p>`}', '${n} ${n === 1 ? "story" : "stories"} in ${ISSUES.length} archived ${ISSUES.length === 1 ? "edition" : "editions"}</p>${html || `<p class="empty">No stories on this topic.</p>`}'),
("← Torna all'edizione di oggi</a><p class=\"kicker\">Ricerca</p>", "← Back to today's edition</a><p class=\"kicker\">Search</p>"),
('${n ? `${n} ${n === 1 ? "notizia trovata" : "notizie trovate"} in ${ISSUES.length} edizioni` : "Nessuna notizia trovata. Prova con un nome di azienda o una parola più corta."}', '${n ? `${n} ${n === 1 ? "story found" : "stories found"} in ${ISSUES.length} ${ISSUES.length === 1 ? "edition" : "editions"}` : "No stories found. Try a company name or a shorter word."}'),
("document.title = \"Il Quotidiano dell'AI\";", "document.title = \"The AI Daily\";"),
('"· le notizie del " + issue.parsed.newsDate', '"· news from " + issue.parsed.newsDate'),
('<span class="lab">Edizioni</span>', '<span class="lab">Editions</span>'),
('title="Uscita dopo la tua ultima visita"', 'title="Out since your last visit"'),
('class="sr-only">Edizioni precedenti</label><select id="older"><option value="">Precedenti…</option>', 'class="sr-only">Earlier editions</label><select id="older"><option value="">Earlier…</option>'),
('u.lang = "it-IT";', 'u.lang = "en-GB";'), ('/^it/i.test(v.lang)', '/^en/i.test(v.lang)'),
('btn.textContent = "Ascolta"; };', 'btn.textContent = "Listen"; };'),
('btn.textContent = "Ferma la lettura";', 'btn.textContent = "Stop reading";'),
('b.textContent = "Ascolta"', 'b.textContent = "Listen"'),
('cp.textContent = "Link copiato"; setTimeout(() => cp.textContent = "Copia link"', 'cp.textContent = "Link copied"; setTimeout(() => cp.textContent = "Copy link"'),
('const THEMES = { auto: "auto", light: "chiaro", dark: "scuro" };', 'const THEMES = { auto: "auto", light: "light", dark: "dark" };'),
('$("theme").textContent = "Tema: "', '$("theme").textContent = "Theme: "'),
('<div class="empty">Nessuna edizione disponibile.</div>', '<div class="empty">No editions available.</div>'),
('" edizione in archivio" : " edizioni in archivio"', '" edition in the archive" : " editions in the archive"'),
('<div class="empty">Non è stato possibile caricare le notizie. Ricarica la pagina.</div>', '<div class="empty">Could not load the news. Please reload the page.</div>'),
('toLocaleDateString("it-IT", { weekday: "long", day: "numeric", month: "long", year: "numeric" })', 'toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" })'),
('toLocaleDateString("it-IT", { weekday: "short", day: "numeric", month: "short" })', 'toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" })'),
('return "Oggi";', 'return "Today";'), ('return "Ieri";', 'return "Yesterday";'),
('/deed.it`', '/deed.en`'), ('/zero/1.0/deed.it"', '/zero/1.0/deed.en"'),
('store.get("lastSeen", null)', 'store.get("en.lastSeen", null)'), ('store.set("lastSeen",', 'store.set("en.lastSeen",'),
('store.get("read", [])', 'store.get("en.read", [])'), ('store.set("read",', 'store.set("en.read",'),
('store.get("sinceClosed", "")', 'store.get("en.sinceClosed", "")'), ('store.set("sinceClosed",', 'store.set("en.sinceClosed",'),
('{ it: "domenica",', '{ it: "Sunday",'), ('{ it: "lunedì",', '{ it: "Monday",'), ('{ it: "martedì",', '{ it: "Tuesday",'),
('{ it: "mercoledì",', '{ it: "Wednesday",'), ('{ it: "giovedì",', '{ it: "Thursday",'), ('{ it: "venerdì",', '{ it: "Friday",'), ('{ it: "sabato",', '{ it: "Saturday",'),
('${isLead ? " · Apertura" : ""}', '${isLead ? " · Lead story" : ""}'),
('const dash = body.search(/\\s—\\s(fonti:|\\[fonte\\])/);', 'const dash = body.search(/\\s—\\s(fonti:|sources:|\\[fonte\\]|\\[source\\])/);'),
('src = body.slice(dash + 3).replace(/^fonti:\\s*/, "");', 'src = body.slice(dash + 3).replace(/^(?:fonti|sources):\\s*/, "");'),
('<span>${n} notizie</span></li>', '<span>${n} ${n === 1 ? "story" : "stories"}</span></li>'),
('$("today").textContent = `N° ${p2(d.getDate())}·${p2(d.getMonth() + 1)}·${String(d.getFullYear()).slice(2)} · `', '$("today").textContent = `No. ${p2(d.getDate())}·${p2(d.getMonth() + 1)}·${String(d.getFullYear()).slice(2)} · `'),
]
for a, b in R2:
    if a not in s: print('MISSING', a[:80])
    s = s.replace(a, b)
open('en/quotidiano/index.html', 'w').write(s)
left = [l.strip()[:110] for l in s.split('\n') if re.search(r'[àèéìòù]|\b(della|delle|notizi|edizion|Torna|Leggi|Chiudi|Cerca)\b', l) and not l.strip().startswith('//') and not l.strip().startswith('/*')]
print(len(left)); print('\n'.join(left[:40]))
