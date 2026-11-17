/* Home page (IT e EN): riempie le due card con l'edizione più recente.
   Se i dati non si caricano, restano le card statiche. */
(function () {
  const EN = document.documentElement.lang === 'en';
  const ROOT = EN ? '../' : '';
  const T = EN
    ? { months: ['January','February','March','April','May','June','July','August','September','October','November','December'],
        days: ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
        lead: 'Today’s lead story, in Italian', cover: 'Cover story', issue: 'No.' }
    : { months: ['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre'],
        days: ['domenica','lunedì','martedì','mercoledì','giovedì','venerdì','sabato'],
        lead: 'Oggi in apertura', cover: 'In copertina', issue: 'N.' };
  // stessi colori del Quotidiano (quotidiano/index.html, DAY_COLORS)
  const COLORS = [
    ['#16171b', '#f4f1e8', '#ff6a3d'], ['#d2452b', '#f4f1e8', '#ffd23f'], ['#1f7a4f', '#f4f1e8', '#ffd23f'],
    ['#f2b632', '#16171b', '#1739c9'], ['#6d3fc0', '#f4f1e8', '#ffd23f'], ['#1739c9', '#f4f1e8', '#ff6a3d'],
    ['#0f6b78', '#f4f1e8', '#ffd23f']];
  const $ = (id) => document.getElementById(id);
  const day = (iso) => new Date(iso + 'T12:00:00Z');
  const label = (iso) => { const d = day(iso); return `${T.days[d.getUTCDay()]} ${d.getUTCDate()} ${T.months[d.getUTCMonth()]}`; };
  const plain = (s) => s.replace(/\[([^\]]+)\]\([^)\s]+\)/g, '$1').replace(/\*\*/g, '');
  const get = (u) => fetch(u, { cache: 'no-store' }).then((r) => (r.ok ? r.json() : Promise.reject(r.status)));

  get(ROOT + 'quotidiano/data/issues.json').then((d) => {
    const e = (d.issues || [])[0]; if (!e) return;
    const card = $('daily'); const [pb, pf, px] = COLORS[day(e.date).getUTCDay()];
    card.style.setProperty('--bg', pb); card.style.setProperty('--fg', pf); card.style.setProperty('--hi', px);
    const m = (e.markdown || '').match(/^\*\*(.+)\*\*\s*$/m);
    $('daily-k').textContent = label(e.date);
    if (m) { $('daily-hl').textContent = plain(m[1]); $('daily-lead').textContent = T.lead; card.classList.add('live'); }
  }).catch(() => {});

  const wdir = ROOT + (EN ? 'en/settimanale/' : 'settimanale/');
  get(wdir + 'data/issues.json').then((d) => {
    const e = (d.issues || []).slice().sort((a, b) => b.date.localeCompare(a.date))[0]; if (!e) return;
    const c = e.cover || {};
    $('weekly-k').textContent = `${T.issue} ${e.n} · ${e.range}`;
    if (c.title) { $('weekly-hl').textContent = c.title; $('weekly-lead').textContent = T.cover; $('weekly').classList.add('live'); }
  }).catch(() => {});
})();
