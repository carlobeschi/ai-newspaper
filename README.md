# ai-newspaper

I giornali dell'AI di Carlo, generati da Claude a partire dalla newsletter *Daily Brief* di PierG, pubblicati con GitHub Pages.

| Percorso | Cosa contiene |
|---|---|
| `index.html` | Pagina d'ingresso con i link ai giornali |
| `quotidiano/` | **Il Quotidiano dell'AI**: `index.html`, `data/issues.json` (edizioni, la più recente per prima), `img/<data>.jpg` (foto di apertura) |
| `settimanale/` | **Il Settimanale dell'AI**: `index.html`, `data/issues.json` (numeri, il più recente per primo), `img/<data>-<pezzo>.jpg` |
| `scripts/foto.py` | Cerca e scarica da Wikimedia Commons una foto con licenza libera per l'apertura |

## Aggiornamento

Un'attività pianificata di Claude ogni mattina legge la nuova newsletter, aggiunge l'edizione a `quotidiano/data/issues.json`, scarica la foto con `scripts/foto.py` e fa commit su `main`. GitHub Pages pubblica il sito dalla radice di `main`.

Formato di un'edizione:

```json
{"date": "YYYY-MM-DD", "markdown": "...", "photo": {"file": "img/YYYY-MM-DD.jpg", "author": "...", "license": "...", "source": "Wikimedia Commons", "page": "...", "alt": "...", "caption": "Immagine di repertorio: ..."}}
```

## Anteprima locale

```sh
python3 -m http.server 8000
# poi apri http://localhost:8000/quotidiano/
```
