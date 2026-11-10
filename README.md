# ai-newspaper

Web view over PierG AI newsletter :-)

I giornali dell'AI di Carlo, generati da Claude a partire dalla newsletter *Daily Brief* di PierG, pubblicati con GitHub Pages.

| Percorso | Cosa contiene |
|---|---|
| `index.html` | Pagina d'ingresso con i link ai giornali |
| `quotidiano/` | **Il Quotidiano dell'AI**: `index.html`, `data/issues.json` (edizioni, la più recente per prima), `img/<data>.jpg` (foto di apertura) |
| `settimanale/` | **Il Settimanale dell'AI**: `index.html`, `data/issues.json` (numeri, il più recente per primo), `img/<data>-<pezzo>.jpg` |
| `atlas/` | **AI Atlas** (in inglese): mappa navigabile di cosa succede nell'AI in dieci campi. `index.html` è la pagina, `fields/<campo>.json` i dati di ogni campo, `layout.json` posizioni, collegamenti, percorsi e punti di vista. Dopo una modifica: `node atlas/build.js` rigenera `atlas/atlas-data.js`; `node atlas/check-links.js` controlla che fonti e link di approfondimento rispondano ancora |
| `scripts/foto.py` | Cerca e scarica da Wikimedia Commons una foto con licenza libera per l'apertura |
| `scripts/feeds.py` | Genera `quotidiano/feed.xml` e `settimanale/feed.xml` (lo lancia la GitHub Action `feeds.yml` a ogni nuova edizione) |
| `*/img/og.png`, `og.png` | Immagini di anteprima per i link condivisi (WhatsApp, social) |

## Aggiornamento

Un'attività pianificata di Claude ogni mattina legge la nuova newsletter, aggiunge l'edizione a `quotidiano/data/issues.json`, scarica la foto con `scripts/foto.py` e fa commit su `main`. GitHub Pages pubblica il sito dalla radice di `main`.

Formato di un'edizione:

```json
{"date": "YYYY-MM-DD", "markdown": "...", "photo": {"file": "img/YYYY-MM-DD.jpg", "author": "...", "license": "...", "source": "Wikimedia Commons", "page": "...", "alt": "...", "caption": "Immagine di repertorio: ..."}}
```

Il Settimanale ha lo stesso schema (`settimanale/data/issues.json`). Sotto il commento, il campo facoltativo `opinion.counter` = `{"title": "...", "body": ["paragrafo", ...]}` diventa il riquadro «Un'altra lettura»: l'obiezione più forte alla tesi del commento. Nelle brevi la testata viene ricavata dall'url; per forzarla, aggiungere `"source": "Nome testata"`.

I due giornali si leggono a vicenda: il Quotidiano segnala le notizie riprese dal Settimanale, il Settimanale rimanda alle notizie del Quotidiano da cui nasce (confrontando gli url delle fonti).

## Anteprima locale

```sh
python3 -m http.server 8000
# poi apri http://localhost:8000/quotidiano/
```
