// Anonymisiert die laufende Streamlit-App für README-Screenshots.
// Verwendung: Seite öffnen, gewünschten Tab anzeigen, dieses Skript in der
// Browser-Konsole (F12) ausführen, dann Screenshot erstellen.
//
// Es werden NUR die Darstellung im Browser verändert – keine Daten, keine Dateien.
//  - Schulnamen in Tabellen: Spalte "name" wird mit einem Blur überdeckt
//  - Kennzahlen (st.metric): durch Platzhalterwerte ersetzt
//  - Schulname im Detail-Tab + Mutter/Tochter-Auswahl: ersetzt bzw. geblurrt
//  - Plotly-Charts: Wertebeschriftungen und Zahlen-Achsen ausgeblendet
(() => {
  const MARK = "data-anon";
  document.querySelectorAll(`[${MARK}]`).forEach((el) => el.remove());

  const blurBox = (parent, left, top, width, height) => {
    const box = document.createElement("div");
    box.setAttribute(MARK, "");
    Object.assign(box.style, {
      position: "absolute", left: `${left}px`, top: `${top}px`,
      width: `${width}px`, height: `${height}px`, zIndex: 50,
      backdropFilter: "blur(7px)", background: "rgba(128,128,128,.12)",
      borderRadius: "4px", pointerEvents: "none",
    });
    if (getComputedStyle(parent).position === "static") parent.style.position = "relative";
    parent.appendChild(box);
  };

  // 1) Spalte "name" in allen st.dataframe-Tabellen überdecken
  document.querySelectorAll('[data-testid="stDataFrame"]').forEach((grid) => {
    const firstRow = grid.querySelector("table tr");
    const headers = [...(firstRow?.children || [])].map((th) => th.innerText.trim());
    const col = headers.indexOf("name");
    const canvases = [...grid.querySelectorAll("canvas")];
    const header = canvases.find((c) => c.getBoundingClientRect().height < 60);
    if (col < 0 || !header) return;
    // Spaltentrenner aus der Header-Canvas lesen
    const ctx = header.getContext("2d");
    const { width: W, height: H } = header;
    const d = ctx.getImageData(0, 0, W, H).data;
    const px = (x, y) => d.slice((y * W + x) * 4, (y * W + x) * 4 + 4).join();
    const bg = px(5, 4);
    const lines = [];
    for (let x = 0; x < W; x++) {
      const a = px(x, 4);
      if (a !== bg && a === px(x, Math.floor(H / 3)) && a === px(x, H - 8)
          && (!lines.length || x - lines[lines.length - 1] > 2)) lines.push(x);
    }
    const scale = W / header.getBoundingClientRect().width;
    // Spalte 0 = Auswahl-Checkbox, danach die Datenspalten
    const bounds = [0, ...lines];
    const start = bounds[col + 1], end = bounds[col + 2] ?? W;
    if (start === undefined) return;
    const gr = grid.getBoundingClientRect(), hr = header.getBoundingClientRect();
    const host = header.parentElement.parentElement;
    const hostR = host.getBoundingClientRect();
    blurBox(host, hr.left - hostR.left + start / scale + 2, hr.bottom - hostR.top,
      (end - start) / scale - 4, gr.bottom - hr.bottom + 12);
  });

  // 2) Kennzahlen durch Platzhalter ersetzen
  const fake = {
    "Total aktive Schulen:": "1'234", "Total aktive Lehrpersonen": "12'345",
    "Total aktive Schüler": "123'456", "Total aktive Eltern": "98'765",
    "Aktive Lehrer": "42", "Aktive Schüler": "512", "Aktive Eltern": "730",
    "Rechnungsbetrag (Historie)": "CHF 1'234.00",
    "Hohe Gesamtfehlzeiten Aktiviert": "123", "Absenzmuster erkennen Aktiviert": "45",
  };
  document.querySelectorAll('[data-testid="stMetric"]').forEach((m) => {
    const label = m.querySelector('[data-testid="stMetricLabel"]')?.innerText.trim();
    const value = m.querySelector('[data-testid="stMetricValue"] div, [data-testid="stMetricValue"]');
    if (label in fake && value) value.innerText = fake[label];
  });

  // 3) Detail-Tab: Schulname ersetzen, Mutter/Tochter-Auswahl blurren
  const DUMMY = "Musterschule (anonymisiert)";
  const detailPanel = [...document.querySelectorAll('[role="tabpanel"]')]
    .find((p) => [...p.querySelectorAll("label")].some((l) => l.innerText.startsWith("Schule suchen")));
  detailPanel?.querySelectorAll('[data-testid="stHeading"] h2').forEach((h) => {
    const anchor = h.querySelector("a");
    h.firstChild.textContent = DUMMY;
    if (anchor) h.appendChild(anchor);
  });
  document.querySelectorAll('[data-testid="stSelectbox"]').forEach((sb) => {
    const label = sb.querySelector("label")?.innerText || "";
    const shown = sb.querySelector('[data-baseweb="select"] [value], [data-baseweb="select"] div[title]');
    if (label.startsWith("Schule suchen") && shown) {
      shown.textContent = DUMMY; shown.title = DUMMY;
    }
    if (/Mutterschule|Tochterschule/.test(label)) {
      const sel = sb.querySelector('[data-baseweb="select"]');
      blurBox(sel, 0, 0, sel.offsetWidth, sel.offsetHeight);
    }
  });

  // 4) Plotly: absolute Zahlen ausblenden, nur Proportionen bleiben sichtbar
  const style = document.createElement("style");
  style.setAttribute(MARK, "");
  style.textContent = `
    .js-plotly-plot .bartext, .js-plotly-plot .textpoint, .js-plotly-plot .xtick text { visibility: hidden !important; }`;
  document.head.appendChild(style);

  return "anonymisiert";
})();
