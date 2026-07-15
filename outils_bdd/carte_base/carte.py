# -*- coding: utf-8 -*-
"""Carte visuelle de la base aSchool.

Lit la structure REELLE de la base (information_schema) — jamais un .md, jamais
une supposition — puis regenere `carte_base.html` a cote de ce script et l'ouvre
dans Edge. Lit `DATABASE_URL` du .env, comme l'application.

Usage (depuis la racine du depot) :
    python outils_bdd/carte_base/carte.py            # regenere + ouvre Edge
    python outils_bdd/carte_base/carte.py --no-open  # regenere seulement
"""
import os
import sys
import json
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]  # outils_bdd/carte_base -> racine du depot
OUT = HERE / "carte_base.html"
MERMAID_LIB = HERE / "vendor" / "mermaid.min.js"  # moteur de dessin embarque (hors ligne)

# ---------------------------------------------------------------------------
# 1. LECTURE DE LA BASE REELLE (structure uniquement : tables, colonnes, FK)
# ---------------------------------------------------------------------------
def lire_schema() -> dict:
    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("ARRET : DATABASE_URL absente du .env — on ne sait pas quelle base viser.")
    if not url.startswith("postgresql"):
        sys.exit(f"ARRET : DATABASE_URL = '{url.split('://')[0]}://...', PostgreSQL exige.")

    eng = create_engine(url)
    out = {"tables": {}, "fks": []}
    with eng.connect() as c:
        cols = c.execute(text("""
            SELECT table_name, column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """))
        for t, col, dt, nullable, maxlen in cols:
            out["tables"].setdefault(t, [])
            out["tables"][t].append({"name": col, "type": dt,
                                     "nullable": nullable == "YES", "maxlen": maxlen})

        pks = c.execute(text("""
            SELECT tc.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public'
        """))
        pkset = {(t, col) for t, col in pks}
        for t, coldefs in out["tables"].items():
            for cd in coldefs:
                cd["pk"] = (t, cd["name"]) in pkset

        fks = c.execute(text("""
            SELECT tc.table_name AS src_table, kcu.column_name AS src_col,
                   ccu.table_name AS dst_table, ccu.column_name AS dst_col
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
        """))
        for src_t, src_c, dst_t, dst_c in fks:
            out["fks"].append({"src_table": src_t, "src_col": src_c,
                               "dst_table": dst_t, "dst_col": dst_c})

    # nombre de lignes par table (volume, pas contenu) -> suivre le remplissage
    with eng.connect() as c:
        for t in out["tables"]:
            try:
                n = c.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
            except Exception:
                n = None
            out["tables"][t] = {"columns": out["tables"][t], "rows": n}
    return out


# ---------------------------------------------------------------------------
# 2. CLASSEMENT PAR DOMAINE METIER (5 domaines colores)
#    Toute table inconnue tombe dans "systeme" (garde-fou : jamais un oubli muet,
#    une nouvelle table apparait quand meme sur la carte).
# ---------------------------------------------------------------------------
DOMAINS = {
    "comptes":  ("Comptes & securite", "#2563eb", "#dbeafe", "#1e3a8a",
        ["users", "refresh_tokens", "email_tokens", "connexion_logs",
         "failed_login_attempts", "user_sessions", "admin_audit_log", "admin_alerts"]),
    "peda":     ("Structure pedagogique", "#16a34a", "#dcfce7", "#14532d",
        ["cycles", "niveaux", "matieres", "matiere_niveaux", "matieres_candidates",
         "user_enseignements", "familles", "famille_couples", "fiches_matieres"]),
    "ref":      ("Referentiels & RAG", "#d97706", "#fef3c7", "#78350f",
        ["referentiels", "referentiel_chunks", "arbitrage_demandes"]),
    "contenu":  ("Contenu prof & retours", "#9333ea", "#f3e8ff", "#581c87",
        ["activites_sauvegardees", "sequences_sauvegardees", "feedbacks",
         "feedback_statuts", "feature_votes", "few_shot_milestones", "tool_usage_logs"]),
    "systeme":  ("Config, e-mail & systeme", "#e11d48", "#ffe4e6", "#881337",
        ["settings", "ai_fournisseurs", "ai_modeles", "email_templates",
         "email_envois", "alembic_version"]),
}

TYPE_MAP = {
    "integer": "int", "character varying": "varchar", "text": "text",
    "boolean": "bool", "timestamp without time zone": "timestamp",
    "double precision": "float", "USER-DEFINED": "vector",
}


def short_type(t: str) -> str:
    return TYPE_MAP.get(t, t.replace(" ", "_"))


def espace_milliers(n: int) -> str:
    return f"{n:,}".replace(",", " ")


# ---------------------------------------------------------------------------
# 3. CONSTRUCTION DU HTML
# ---------------------------------------------------------------------------
def construire_html(data: dict) -> str:
    tables = data["tables"]
    fks = data["fks"]

    table_domain = {}
    for key, (_, _, _, _, tlist) in DOMAINS.items():
        for t in tlist:
            table_domain[t] = key
    unknown = [t for t in tables if t not in table_domain]
    for t in unknown:
        table_domain[t] = "systeme"  # garde-fou : nouvelle table -> visible quand meme

    fk_cols_by_table = {}
    for fk in fks:
        fk_cols_by_table.setdefault(fk["src_table"], set()).add(fk["src_col"])

    total_rows = sum((v.get("rows") or 0) for v in tables.values())
    n_tables = len(tables)
    n_fks = len(fks)

    # ---- Vue epuree : flowchart colore, tables + relations ----
    lines = ["flowchart LR",
             "%%{init: {'theme':'base','flowchart':{'htmlLabels':true,'curve':'basis',"
             "'nodeSpacing':38,'rankSpacing':70},'themeVariables':{'lineColor':'#94a3b8',"
             "'fontSize':'13px'}}}%%"]
    for key, (_, stroke, fill, txt, _t) in DOMAINS.items():
        lines.append(f"classDef {key} fill:{fill},stroke:{stroke},color:{txt},"
                     f"stroke-width:1.5px,rx:6,ry:6;")
    for t in sorted(tables):
        rows = tables[t].get("rows")
        badge = espace_milliers(rows) if rows is not None else "?"
        lines.append(f'{t}["<b>{t}</b><br/><span style=\'font-size:11px;opacity:.7\'>'
                     f'{badge} lignes</span>"]:::{table_domain[t]}')
    for fk in fks:
        lines.append(f'{fk["src_table"]} -->|{fk["src_col"]}| {fk["dst_table"]}')
    epure = "\n".join(lines)

    # ---- Vue complete : erDiagram avec colonnes ----
    er = ["erDiagram"]
    for t in sorted(tables):
        er.append(f"  {t} {{")
        for col in tables[t]["columns"]:
            marks = []
            if col["pk"]:
                marks.append("PK")
            if col["name"] in fk_cols_by_table.get(t, set()):
                marks.append("FK")
            er.append(f'    {short_type(col["type"])} {col["name"]} {", ".join(marks)}'.rstrip())
        er.append("  }")
    for fk in fks:
        src_def = next((c for c in tables[fk["src_table"]]["columns"]
                        if c["name"] == fk["src_col"]), None)
        left = "|o" if (src_def and src_def["nullable"]) else "||"
        er.append(f'  {fk["dst_table"]} {left}--o{{ {fk["src_table"]} : "{fk["src_col"]}"')
    complet = "\n".join(er)

    # ---- Vue detaillee : description claire de chaque table (tableaux HTML) ----
    #      Lisible et cherchable (Ctrl+F), la ou le diagramme ER reste dense.
    fk_target = {}
    for fk in fks:
        fk_target[(fk["src_table"], fk["src_col"])] = fk["dst_table"]
    detail_cards = []
    for t in sorted(tables):
        cols = tables[t]["columns"]
        rows = tables[t].get("rows")
        rows_txt = espace_milliers(rows) if rows is not None else "?"
        lignes_html = []
        for col in cols:
            typ = short_type(col["type"])
            if col["maxlen"]:
                typ += f"({col['maxlen']})"
            requis = "non" if col["nullable"] else "oui"
            req_cls = "req-no" if col["nullable"] else "req-yes"
            cles = []
            if col["pk"]:
                cles.append('<span class="key pk">PK</span>')
            if col["name"] in fk_cols_by_table.get(t, set()):
                dst = fk_target.get((t, col["name"]))
                cles.append(f'<span class="key fk">FK &rarr; {dst}</span>' if dst
                            else '<span class="key fk">FK</span>')
            lignes_html.append(
                f'<tr><td class="cn">{col["name"]}</td><td class="ct">{typ}</td>'
                f'<td class="{req_cls}">{requis}</td><td class="ck">{"".join(cles)}</td></tr>')
        stroke = DOMAINS[table_domain[t]][1]
        detail_cards.append(
            f'<section class="tbl-card" style="--c:{stroke}" id="t-{t}">'
            f'<header><h3>{t}</h3><span class="tbl-meta">{len(cols)} colonnes &middot; '
            f'{rows_txt} lignes</span></header>'
            f'<table class="tbl-cols"><thead><tr><th>Colonne</th><th>Type</th>'
            f'<th>Requis</th><th>Cl&eacute;</th></tr></thead>'
            f'<tbody>{"".join(lignes_html)}</tbody></table></section>')
    tables_detail = "\n".join(detail_cards)

    # ---- Legende + index des volumes par domaine ----
    legend_cards, domain_index = [], []
    for key, (label, stroke, fill, txt, tlist) in DOMAINS.items():
        present = [t for t in tlist if t in tables]
        dom_rows = sum((tables[t].get("rows") or 0) for t in present)
        legend_cards.append(
            f'<div class="chip" style="--c:{stroke}"><span class="dot"></span>{label}'
            f'<span class="chip-n">{len(present)}</span></div>')
        rows_html = "".join(
            f'<li><span class="tname">{t}</span>'
            f'<span class="trows">{espace_milliers(tables[t].get("rows") or 0)}</span></li>'
            for t in sorted(present))
        domain_index.append(
            f'<section class="dom-card" style="--c:{stroke};--bg:{fill};--tx:{txt}">'
            f'<header><h3>{label}</h3><span class="dom-meta">{len(present)} tables · '
            f'{espace_milliers(dom_rows)} lignes</span></header>'
            f'<ul class="dom-list">{rows_html}</ul></section>')

    # tables non classees : signalees dans le pied (jamais un oubli muet)
    note_unknown = ""
    if unknown:
        note_unknown = ("<p class=\"foot warn\">Tables non encore classees dans un domaine "
                        "(rangees par defaut dans « systeme ») : "
                        + ", ".join(sorted(unknown)) + ".</p>")

    # Moteur de dessin embarque. Echappe `</script` pour ne pas fermer la balise
    # prematurement (technique standard d'inlining d'un bundle JS).
    engine = MERMAID_LIB.read_text(encoding="utf-8").replace("</script", "<\\/script")

    html = _TEMPLATE
    for token, value in {
        "__NTABLES__": str(n_tables),
        "__NFKS__": str(n_fks),
        "__NROWS__": espace_milliers(total_rows),
        "__LEGEND__": "\n".join(legend_cards),
        "__EPURE__": epure,
        "__COMPLET__": complet,
        "__TABLES__": tables_detail,
        "__INDEX__": "\n".join(domain_index),
        "__NOTE_UNKNOWN__": note_unknown,
        "__MERMAID_ENGINE__": engine,
    }.items():
        html = html.replace(token, value)
    return html


_TEMPLATE = r"""<title>Carte de la base - aSchool</title>
<style>
  :root{
    --bg:#f6f7fb; --panel:#ffffff; --ink:#161c2b; --muted:#5b6577;
    --line:#e4e8f0; --accent:#2563eb;
    --shadow:0 1px 2px rgba(18,25,45,.05),0 8px 24px rgba(18,25,45,.06);
    --mono:ui-monospace,"SF Mono","Cascadia Code","JetBrains Mono",Menlo,Consolas,monospace;
    --sans:ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  }
  @media (prefers-color-scheme:dark){
    :root{--bg:#0e1220;--panel:#161b2c;--ink:#e8ecf5;--muted:#9aa5bd;
      --line:#252c40;--accent:#6ea0ff;
      --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);}
  }
  :root[data-theme="dark"]{--bg:#0e1220;--panel:#161b2c;--ink:#e8ecf5;--muted:#9aa5bd;
      --line:#252c40;--accent:#6ea0ff;
      --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);}
  :root[data-theme="light"]{--bg:#f6f7fb;--panel:#ffffff;--ink:#161c2b;--muted:#5b6577;
      --line:#e4e8f0;--accent:#2563eb;
      --shadow:0 1px 2px rgba(18,25,45,.05),0 8px 24px rgba(18,25,45,.06);}

  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
    line-height:1.5;-webkit-font-smoothing:antialiased}
  .wrap{max-width:1180px;margin:0 auto;padding:32px 24px 80px}

  header.top{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:8px}
  .eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 6px}
  h1{font-size:30px;line-height:1.1;margin:0;letter-spacing:-.02em;text-wrap:balance}
  .sub{color:var(--muted);margin:6px 0 0;font-size:14px;max-width:60ch}

  .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin:24px 0}
  .stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;box-shadow:var(--shadow)}
  .stat .n{font-size:26px;font-weight:650;font-variant-numeric:tabular-nums;letter-spacing:-.01em}
  .stat .l{font-size:12px;color:var(--muted);margin-top:2px;text-transform:uppercase;letter-spacing:.06em}

  .legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px}
  .chip{display:inline-flex;align-items:center;gap:8px;background:var(--panel);border:1px solid var(--line);
    border-radius:999px;padding:6px 12px;font-size:13px;font-weight:500}
  .chip .dot{width:10px;height:10px;border-radius:50%;background:var(--c)}
  .chip-n{font-family:var(--mono);font-size:11px;color:var(--muted);background:var(--bg);border-radius:999px;padding:1px 7px}

  .toolbar{display:flex;gap:8px;position:sticky;top:0;z-index:5;padding:10px 0;
    background:linear-gradient(var(--bg) 70%,transparent)}
  .toolbar a{font-size:14px;font-weight:550;text-decoration:none;color:var(--ink);
    border:1px solid var(--line);background:var(--panel);border-radius:10px;padding:9px 16px;box-shadow:var(--shadow)}
  .toolbar a:hover{border-color:var(--accent);color:var(--accent)}
  .toolbar a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .toolbar a .k{font-family:var(--mono);font-size:11px;color:var(--muted);margin-left:8px}

  .panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);
    margin:16px 0 28px;overflow:hidden}
  .panel > .ph{display:flex;align-items:baseline;justify-content:space-between;gap:12px;
    padding:16px 20px;border-bottom:1px solid var(--line)}
  .panel h2{margin:0;font-size:17px;letter-spacing:-.01em}
  .panel .ph small{color:var(--muted);font-size:13px}
  .diagram{overflow:auto;padding:18px;max-height:82vh}
  .diagram pre.mermaid{margin:0;background:transparent;min-width:640px}
  .diagram svg{max-width:none !important;height:auto}

  .grid-dom{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;margin-top:16px}
  .dom-card{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--c);
    border-radius:12px;padding:14px 16px;box-shadow:var(--shadow)}
  .dom-card header{display:flex;flex-direction:column;gap:2px;margin-bottom:10px}
  .dom-card h3{margin:0;font-size:15px}
  .dom-meta{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
  .dom-list{list-style:none;margin:0;padding:0;font-family:var(--mono);font-size:12.5px}
  .dom-list li{display:flex;justify-content:space-between;padding:4px 0;border-top:1px dashed var(--line)}
  .dom-list li:first-child{border-top:0}
  .tname{color:var(--ink)}
  .trows{color:var(--muted);font-variant-numeric:tabular-nums}

  .grid-tbl{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px;margin-top:16px}
  .tbl-card{background:var(--panel);border:1px solid var(--line);border-top:3px solid var(--c);
    border-radius:12px;box-shadow:var(--shadow);overflow:hidden}
  .tbl-card header{display:flex;align-items:baseline;justify-content:space-between;gap:10px;
    padding:12px 16px;border-bottom:1px solid var(--line)}
  .tbl-card h3{margin:0;font-size:15px;font-family:var(--mono)}
  .tbl-meta{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap}
  table.tbl-cols{width:100%;border-collapse:collapse;font-size:12.5px}
  table.tbl-cols th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.05em;
    color:var(--muted);font-weight:600;padding:8px 16px;background:var(--bg)}
  table.tbl-cols td{padding:6px 16px;border-top:1px solid var(--line);vertical-align:top}
  table.tbl-cols .cn{font-family:var(--mono);color:var(--ink)}
  table.tbl-cols .ct{font-family:var(--mono);color:var(--muted)}
  .req-yes{color:#16a34a;font-weight:600}
  .req-no{color:var(--muted)}
  .key{display:inline-block;font-family:var(--mono);font-size:10.5px;font-weight:600;
    border-radius:5px;padding:1px 6px;margin-right:4px;white-space:nowrap}
  .key.pk{background:#dcfce7;color:#14532d}
  .key.fk{background:#dbeafe;color:#1e3a8a}

  .foot{margin-top:36px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}
  .foot.warn{color:#b45309;border-top:0;margin-top:12px;padding-top:0}
  h2.sec{font-size:20px;letter-spacing:-.01em;margin:36px 0 4px}
  .sec-sub{color:var(--muted);font-size:14px;margin:0}
</style>

<div class="wrap">
  <header class="top">
    <div>
      <p class="eyebrow">Base de donnees - PostgreSQL 16</p>
      <h1>Carte de la base aSchool</h1>
      <p class="sub">La structure reelle de la base, lue directement dans PostgreSQL. Chaque table, ses colonnes, et les traits qui relient les tables entre elles.</p>
    </div>
  </header>

  <div class="stats">
    <div class="stat"><div class="n">__NTABLES__</div><div class="l">Tables</div></div>
    <div class="stat"><div class="n">__NFKS__</div><div class="l">Relations</div></div>
    <div class="stat"><div class="n">5</div><div class="l">Domaines</div></div>
    <div class="stat"><div class="n">__NROWS__</div><div class="l">Lignes au total</div></div>
  </div>

  <div class="legend">
    __LEGEND__
  </div>

  <nav class="toolbar">
    <a href="#carte">Vue epuree <span class="k">tables + liens</span></a>
    <a href="#detail">Vue complete <span class="k">colonnes</span></a>
    <a href="#tables">Detail par table <span class="k">colonnes en clair</span></a>
    <a href="#volumes">Volumes <span class="k">par domaine</span></a>
  </nav>

  <section id="carte" class="panel">
    <div class="ph"><h2>Vue epuree - la carte</h2><small>d'un coup d'oeil : qui est relie a qui</small></div>
    <div class="diagram"><pre class="mermaid">__EPURE__</pre></div>
  </section>

  <section id="detail" class="panel">
    <div class="ph"><h2>Vue complete - le detail (MLD)</h2><small>toutes les colonnes - PK = cle primaire - FK = cle etrangere</small></div>
    <div class="diagram"><pre class="mermaid">__COMPLET__</pre></div>
  </section>

  <h2 class="sec" id="tables">Detail par table</h2>
  <p class="sec-sub">Chaque table et ses colonnes, en clair : le type, si le champ est requis, et les cles (PK = cle primaire, FK = cle etrangere avec sa table cible).</p>
  <div class="grid-tbl">
    __TABLES__
  </div>

  <h2 class="sec" id="volumes">Volumes par domaine</h2>
  <p class="sec-sub">Le nombre de lignes de chaque table - pour suivre le remplissage dans le temps.</p>
  <div class="grid-dom">
    __INDEX__
  </div>
  __NOTE_UNKNOWN__

  <p class="foot">Genere a partir de la base reelle (information_schema). Pour mettre la carte a jour apres une evolution du schema, relancer outils_bdd/carte_base/carte.py - la carte se redessine sur l'etat exact de la base.</p>
</div>

<script>
  (function(){
    function reduce(){ return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches; }
    document.querySelectorAll('.toolbar a').forEach(function(a){
      a.addEventListener('click', function(e){
        var el = document.querySelector(a.getAttribute('href'));
        if(el){ e.preventDefault(); el.scrollIntoView({behavior: reduce()?'auto':'smooth', block:'start'}); }
      });
    });
  })();
</script>

<!-- Moteur de dessin Mermaid embarque (hors ligne, sans CDN). -->
<script>__MERMAID_ENGINE__</script>
<script>
  // Dessine les schemas au chargement. mermaid.run() marque les blocs deja traites
  // (data-processed) : aucun double-rendu si un autre moteur est deja passe.
  window.addEventListener('DOMContentLoaded', function(){
    if (!window.mermaid) return;
    try {
      var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      var attr = document.documentElement.getAttribute('data-theme');
      if (attr) dark = (attr === 'dark');
      mermaid.initialize({ startOnLoad:false, securityLevel:'loose',
                           theme:'base', fontFamily:'ui-sans-serif, -apple-system, Segoe UI, sans-serif' });
      mermaid.run({ querySelector: 'pre.mermaid' });
    } catch (e) { console.error('Mermaid:', e); }
  });
</script>
"""


# ---------------------------------------------------------------------------
# 4. POINT D'ENTREE
# ---------------------------------------------------------------------------
def main() -> None:
    data = lire_schema()
    OUT.write_text(construire_html(data), encoding="utf-8")
    n_t = len(data["tables"])
    n_f = len(data["fks"])
    n_r = sum((v.get("rows") or 0) for v in data["tables"].values())
    print(f"Carte regeneree : {n_t} tables, {n_f} relations, {n_r} lignes")
    print(f"  -> {OUT}")

    if "--no-open" not in sys.argv:
        # Ouverture dans Edge (navigateur du projet).
        subprocess.run(["cmd", "/c", "start", "", "msedge", str(OUT)], check=False)


if __name__ == "__main__":
    main()
