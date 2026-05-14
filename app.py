import csv
import sys
import os
import io
import base64
import math
from collections import Counter

import matplotlib
matplotlib.use("Agg")           # sin ventana gráfica, solo genera imágenes
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ─── CONFIGURACIÓN VISUAL (estilo oscuro consistente) ─────────────────────────
BG      = "#0b0f1a"
SURFACE = "#111827"
BORDER  = "#1e293b"
TEXT    = "#e2e8f0"
MUTED   = "#64748b"
C1, C2, C3, C4 = "#00e5ff", "#ff6b6b", "#a3e635", "#f59e0b"
COLOR_MAP = {"Blanco": "#e2e8f0", "Amarillo": "#f59e0b", "Verde": "#a3e635"}

plt.rcParams.update({
    "figure.facecolor":  BG,
    "axes.facecolor":    SURFACE, #color de las barras
    "axes.edgecolor":    BORDER,
    "axes.labelcolor":   TEXT,
    "xtick.color":       MUTED,
    "ytick.color":       MUTED,
    "text.color":        TEXT,
    "grid.color":        BORDER,  #Grid es el cuadro de la tabla
    "grid.linewidth":    0.8,
    "font.family":       "monospace",
    "font.size":         10,
    "legend.facecolor":  SURFACE,
    "legend.edgecolor":  BORDER,
    "legend.labelcolor": TEXT,
})

# ─── ARGUMENTOS ───────────────────────────────────────────────────────────────
csv_path  = sys.argv[1] if len(sys.argv) > 1 else "datos.csv"
html_path = sys.argv[2] if len(sys.argv) > 2 else "analisis_estadistico.html"

# ─── LEER CSV ─────────────────────────────────────────────────────────────────
NA_VALUES = {"na", "n/a", "nan", "null", "none", ""}

def leer_csv(path):
    if not os.path.exists(path):
        print(f"  Archivo no encontrado: {path}"); sys.exit(1)
    registros = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [c.strip().lower() for c in reader.fieldnames]
        req = {"peso","altura","velocidad","color"}
        if not req.issubset(set(reader.fieldnames)):
            print(f"  Faltan columnas: {req - set(reader.fieldnames)}"); sys.exit(1)
        for fila in reader:
            pn = lambda v: None if v.strip().lower() in NA_VALUES else float(v.strip()) #strip().lower() para normalizar el texto
            ps = lambda v: None if v.strip().lower() in NA_VALUES else v.strip()
            registros.append({
                "peso":      pn(fila["peso"]),
                "altura":    pn(fila["altura"]),
                "velocidad": pn(fila["velocidad"]),
                "color":     ps(fila["color"]),
            })
    print(f"  CSV leído: {path}  ({len(registros)} registros)")
    return registros

# ─── ESTADÍSTICAS ─────────────────────────────────────────────────────────────
def media(lst):    return round(sum(lst)/len(lst), 4)
def mediana(lst):
    s = sorted(lst); n = len(s)
    return round((s[n//2-1]+s[n//2])/2, 4) if n%2==0 else round(s[n//2], 4)
def moda(lst):
    c = Counter(lst); mf = max(c.values())
    return sorted(k for k,v in c.items() if v==mf), mf
def frec_abs(lst):  return dict(sorted(Counter(lst).items()))
def frec_rel(lst):
    c=Counter(lst); n=len(lst)
    return {k: round(v/n,4) for k,v in sorted(c.items())}
def frec_acum(lst):
    acum=0; res={}
    for k,v in frec_abs(lst).items(): acum+=v; res[k]=acum
    return res
def intervalos(lst, n=6):
    mn,mx = min(lst),max(lst); amp=(mx-mn)/n; ivs=[]
    for i in range(n):
        li=round(mn+i*amp,2); ls=round(mn+(i+1)*amp,2)
        freq=sum(1 for x in lst if (li<=x<ls if i<n-1 else li<=x<=ls))
        ivs.append({"li":li,"ls":ls,"marca":round((li+ls)/2,2),"freq":freq,
                    "label":f"[{li}–{ls})"})
    acum=0
    for iv in ivs: acum+=iv["freq"]; iv["acum"]=acum; iv["rel"]=round(iv["freq"]/len(lst),4)
    return ivs

# ─── UTILIDAD: figura → base64 PNG ────────────────────────────────────────────
def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=130, facecolor=BG)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{b64}"

# ─── PROCESAR DATOS ───────────────────────────────────────────────────────────
registros = leer_csv(csv_path)
peso      = [r["peso"]      for r in registros if r["peso"]      is not None]
altura    = [r["altura"]    for r in registros if r["altura"]    is not None]
velocidad = [r["velocidad"] for r in registros if r["velocidad"] is not None]
color     = [r["color"]     for r in registros if r["color"]     is not None]

stats = {}
for nombre, lst in [("peso",peso),("altura",altura),("velocidad",velocidad)]:
    m,mf = moda(lst)
    stats[nombre] = {
        "n":len(lst), "media":media(lst), "mediana":mediana(lst),
        "moda_vals":m, "moda_freq":mf,
        "min":min(lst), "max":max(lst), "ivs":intervalos(lst),
    }

cfa  = frec_abs(color)
cfr  = frec_rel(color)
cacum= frec_acum(color)
colores_keys = list(cfa.keys())

print(f"\n{'─'*50}")
for v,s in stats.items():
    print(f"  {v.capitalize():12} n={s['n']:3}  media={s['media']:.2f}  "
          f"mediana={s['mediana']:.2f}  moda={s['moda_vals']}")
print(f"  Color  — {dict(Counter(color))}")
print(f"{'─'*50}\n")


#  GRÁFICAS


# helper de ejes 
def estilo_ax(ax, titulo=""):
    ax.set_facecolor(SURFACE)
    for spine in ax.spines.values(): spine.set_edgecolor(BORDER)
    ax.tick_params(colors=MUTED)
    ax.yaxis.label.set_color(TEXT)
    ax.xaxis.label.set_color(TEXT)
    if titulo: ax.set_title(titulo, color=TEXT, fontsize=11, pad=10)
    ax.grid(axis="y", color=BORDER, linewidth=0.8)

# G1  Frecuencia Absoluta — Barras de colo
def graf_barras_color():
    fig, ax = plt.subplots(figsize=(6,4), facecolor=BG)
    bar_colors = [COLOR_MAP.get(k, MUTED) for k in colores_keys]
    bars = ax.bar(colores_keys, [cfa[k] for k in colores_keys],
                  color=bar_colors, edgecolor=BG, linewidth=1.5, width=0.5)
    for bar, val in zip(bars, [cfa[k] for k in colores_keys]):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.15,
                str(val), ha="center", va="bottom", color=TEXT, fontsize=10)
    ax.set_ylabel("Frecuencia"); ax.set_ylim(0, max(cfa.values())+2)
    estilo_ax(ax, "Frecuencia Absoluta por Color")
    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# G2  Frecuencia Relativa — Pastel
# ─────────────────────────────────────────────────────────────────────────────
def graf_pastel_color():
    fig, ax = plt.subplots(figsize=(6,4), facecolor=BG)
    pie_colors = [COLOR_MAP.get(k, MUTED) for k in colores_keys]
    wedges, texts, autotexts = ax.pie(
        [cfr[k] for k in colores_keys],
        labels=colores_keys,
        colors=pie_colors,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"edgecolor": BG, "linewidth": 2},
        textprops={"color": TEXT},
        pctdistance=0.75,
    )
    for at in autotexts: at.set_color(BG); at.set_fontweight("bold")
    ax.set_title("Frecuencia Relativa por Color", color=TEXT, fontsize=11, pad=10)
    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# G3  Frecuencia Acumulada — Color
# ─────────────────────────────────────────────────────────────────────────────
def graf_acum_color():
    fig, ax = plt.subplots(figsize=(6,4), facecolor=BG)
    x = np.arange(len(colores_keys))
    bars = ax.bar(x, [cfa[k] for k in colores_keys],
                  color=C1, alpha=0.4, edgecolor=C1, linewidth=1.5,
                  width=0.4, label="Absoluta")
    ax.plot(x, [cacum[k] for k in colores_keys],
            color=C4, marker="o", linewidth=2.5,
            markersize=7, markerfacecolor=C4, label="Acumulada")
    for xi, k in enumerate(colores_keys):
        ax.text(xi, cacum[k]+0.3, str(cacum[k]), ha="center",
                color=C4, fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(colores_keys)
    ax.set_ylabel("Registros")
    ax.legend()
    estilo_ax(ax, "Frecuencia Acumulada por Color")
    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# G4  Histograma
# ─────────────────────────────────────────────────────────────────────────────
def graf_histograma(nombre, ivs, color_barra):
    fig, ax = plt.subplots(figsize=(6,4), facecolor=BG)
    labels = [iv["label"] for iv in ivs]
    freqs  = [iv["freq"]  for iv in ivs]
    x = np.arange(len(labels))
    bars = ax.bar(x, freqs, color=color_barra, alpha=0.55,
                  edgecolor=color_barra, linewidth=1.5, width=0.6)
    for bar, val in zip(bars, freqs):
        if val > 0:
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1,
                    str(val), ha="center", va="bottom", color=TEXT, fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Frecuencia")
    estilo_ax(ax, f"Histograma — {nombre.capitalize()}")
    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# G5  Polígono de frecuencias
# ─────────────────────────────────────────────────────────────────────────────
def graf_poligono(nombre, ivs, color_linea):
    fig, ax = plt.subplots(figsize=(6,4), facecolor=BG)
    marcas = [iv["marca"] for iv in ivs]
    freqs  = [iv["freq"]  for iv in ivs]
    acums  = [iv["acum"]  for iv in ivs]
    ax.fill_between(marcas, freqs, alpha=0.15, color=color_linea)
    ax.plot(marcas, freqs,  color=color_linea, marker="o", linewidth=2.5,
            markersize=6, markerfacecolor=color_linea, label="Frec. Abs.")
    ax.plot(marcas, acums,  color=C4, marker="s", linewidth=2,
            markersize=5, markerfacecolor=C4, linestyle="--", label="Frec. Acum.")
    ax.set_xlabel("Marca de clase"); ax.set_ylabel("Frecuencia")
    ax.legend()
    estilo_ax(ax, f"Polígono de Frecuencias — {nombre.capitalize()}")
    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# G6  Radar — Estadísticas normalizadas por variable
# ─────────────────────────────────────────────────────────────────────────────
def graf_radar_stats():
    categorias  = ["Peso", "Altura", "Velocidad"]
    vars_keys   = ["peso", "altura", "velocidad"]
    maximos     = [stats[v]["max"] for v in vars_keys]

    media_norm   = [stats[v]["media"]         / maximos[i] for i,v in enumerate(vars_keys)]
    mediana_norm = [stats[v]["mediana"]        / maximos[i] for i,v in enumerate(vars_keys)]
    moda_norm    = [stats[v]["moda_vals"][0]   / maximos[i] for i,v in enumerate(vars_keys)]

    N = len(categorias)
    angulos = [n/N*2*math.pi for n in range(N)]
    angulos += angulos[:1]   # cerrar el polígono

    fig, ax = plt.subplots(figsize=(5,5), subplot_kw={"polar": True}, facecolor=BG)
    ax.set_facecolor(SURFACE)

    for serie, label, color in [
        (media_norm,   "Media",   C1),
        (mediana_norm, "Mediana", C2),
        (moda_norm,    "Moda",    C3),
    ]:
        vals = serie + serie[:1]
        ax.plot(angulos, vals, color=color, linewidth=2.5, linestyle="solid")
        ax.fill(angulos, vals, color=color, alpha=0.12)
        ax.scatter(angulos[:-1], serie, color=color, s=60, zorder=5)

    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(categorias, color=TEXT, fontsize=11)
    ax.set_yticklabels(
        [f"{int(t*100)}%" for t in ax.get_yticks()],
        color=MUTED, fontsize=8
    )
    ax.spines["polar"].set_color(BORDER)
    ax.yaxis.grid(color=BORDER, linewidth=0.8)
    ax.xaxis.grid(color=BORDER, linewidth=0.8)

    leg = ax.legend(
        [mpatches.Patch(color=C1), mpatches.Patch(color=C2), mpatches.Patch(color=C3)],
        ["Media","Mediana","Moda"],
        loc="upper right", bbox_to_anchor=(1.3, 1.15), framealpha=0.3
    )
    ax.set_title("Radar — Estadísticas normalizadas", color=TEXT, fontsize=11, pad=20)
    fig.tight_layout()
    return fig_to_b64(fig)

# ─────────────────────────────────────────────────────────────────────────────
# G7  Radar — Frecuencias por color
# ─────────────────────────────────────────────────────────────────────────────
def graf_radar_color():
    N = len(colores_keys)
    angulos = [n/N*2*math.pi for n in range(N)]
    angulos += angulos[:1]

    max_abs  = max(cfa.values())
    max_acum = max(cacum.values())

    abs_norm  = [cfa[k]/max_abs   for k in colores_keys]
    rel_vals  = [cfr[k]           for k in colores_keys]
    acum_norm = [cacum[k]/max_acum for k in colores_keys]

    fig, ax = plt.subplots(figsize=(5,5), subplot_kw={"polar": True}, facecolor=BG)
    ax.set_facecolor(SURFACE)

    for serie, label, color in [
        (abs_norm,  "Frec. Absoluta (norm.)",  C4),
        (rel_vals,  "Frec. Relativa",          "#c084fc"),
        (acum_norm, "Frec. Acumulada (norm.)", "#fb923c"),
    ]:
        vals = serie + serie[:1]
        ax.plot(angulos, vals, color=color, linewidth=2.5)
        ax.fill(angulos, vals, color=color, alpha=0.12)
        ax.scatter(angulos[:-1], serie, color=color, s=60, zorder=5)

    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(colores_keys, color=TEXT, fontsize=11)
    ax.set_yticklabels(
        [f"{int(t*100)}%" for t in ax.get_yticks()],
        color=MUTED, fontsize=8
    )
    ax.spines["polar"].set_color(BORDER)
    ax.yaxis.grid(color=BORDER, linewidth=0.8)
    ax.xaxis.grid(color=BORDER, linewidth=0.8)

    leg = ax.legend(
        [mpatches.Patch(color=C4), mpatches.Patch(color="#c084fc"), mpatches.Patch(color="#fb923c")],
        ["Frec. Abs.","Frec. Rel.","Frec. Acum."],
        loc="upper right", bbox_to_anchor=(1.45, 1.15), framealpha=0.3
    )
    ax.set_title("Radar — Frecuencias por Color", color=TEXT, fontsize=11, pad=20)
    fig.tight_layout()
    return fig_to_b64(fig)

# GENERAR TODAS LAS IMÁGENES

print("  Generando gráficas con Matplotlib...")

img = {
    "barColor":   graf_barras_color(),
    "pieColor":   graf_pastel_color(),
    "acumColor":  graf_acum_color(),
    "histPeso":   graf_histograma("peso",      stats["peso"]["ivs"],      C1),
    "polyPeso":   graf_poligono("peso",        stats["peso"]["ivs"],      C1),
    "histAltura": graf_histograma("altura",    stats["altura"]["ivs"],    C2),
    "polyAltura": graf_poligono("altura",      stats["altura"]["ivs"],    C2),
    "histVel":    graf_histograma("velocidad", stats["velocidad"]["ivs"], C3),
    "polyVel":    graf_poligono("velocidad",   stats["velocidad"]["ivs"], C3),
    "radarStats": graf_radar_stats(),
    "radarColor": graf_radar_color(),
}
print(f"  {len(img)} imágenes generadas")

# TABLA HTML genérica

def tabla_intervalos(ivs):
    filas = ""
    for i, iv in enumerate(ivs):
        filas += f"""<tr>
          <td>{i+1}</td><td>{iv['label']}</td><td>{iv['marca']}</td>
          <td>{iv['freq']}</td><td>{iv['rel']*100:.1f}%</td><td>{iv['acum']}</td>
        </tr>"""
    return f"""
    <table>
      <thead><tr>
        <th>#</th><th>Intervalo</th><th>Marca</th>
        <th>Frec. Abs.</th><th>Frec. Rel.</th><th>Frec. Acum.</th>
      </tr></thead>
      <tbody>{filas}</tbody>
    </table>"""

def tabla_raw():
    filas = ""
    for i, r in enumerate(registros):
        def na(v): return str(v) if v is not None else '<span class="na">NA</span>'
        c = r["color"] or ""
        dot_color = COLOR_MAP.get(c, MUTED)
        dot = f'<span class="dot" style="background:{dot_color}"></span>' if c else ""
        filas += f"""<tr>
          <td class="num">{i+1}</td>
          <td>{na(r['peso'])}</td><td>{na(r['altura'])}</td>
          <td>{na(r['velocidad'])}</td>
          <td>{dot}{na(r['color'])}</td>
        </tr>"""
    return f"""
    <table>
      <thead><tr><th>#</th><th>Peso</th><th>Altura</th><th>Velocidad</th><th>Color</th></tr></thead>
      <tbody>{filas}</tbody>
    </table>"""


# GENERAR HTML COMPLETO

def stat_card(titulo, emoji, clase, key, sfx):
    s = stats[key]
    moda_txt = ", ".join(str(v) for v in s["moda_vals"]) + f" (f={s['moda_freq']})"
    return f"""
    <div class="stat-card {clase}">
      <h3>{emoji} {titulo}</h3>
      <div class="stat-row"><span class="label">N válidos</span><span class="val">{s['n']}</span></div>
      <div class="stat-row"><span class="label">Media</span><span class="val hi">{s['media']:.2f}</span></div>
      <div class="stat-row"><span class="label">Mediana</span><span class="val">{s['mediana']:.2f}</span></div>
      <div class="stat-row"><span class="label">Moda</span><span class="val">{moda_txt}</span></div>
      <div class="stat-row"><span class="label">Mín / Máx</span><span class="val">{s['min']} / {s['max']}</span></div>
    </div>"""

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>Análisis Estadístico</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600;800&display=swap" rel="stylesheet"/>
  <style>
    :root{{
      --bg:#0b0f1a;--surface:#111827;--surface2:#1a2236;
      --accent1:#00e5ff;--accent2:#ff6b6b;--accent3:#a3e635;--accent4:#f59e0b;
      --text:#e2e8f0;--muted:#64748b;--border:#1e293b;--radius:14px;
      --mono:'Space Mono',monospace;--sans:'DM Sans',sans-serif;
    }}
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:var(--bg);color:var(--text);font-family:var(--sans);font-size:15px;line-height:1.6;overflow-x:hidden}}

    .hero{{position:relative;padding:80px 40px 60px;text-align:center;overflow:hidden}}
    .hero::before{{content:'';position:absolute;inset:0;
      background:radial-gradient(ellipse 70% 50% at 50% 0%,rgba(0,229,255,.12),transparent),
                 radial-gradient(ellipse 50% 40% at 80% 80%,rgba(163,230,53,.07),transparent);
      pointer-events:none}}
    .hero h1{{font-family:var(--sans);font-weight:800;font-size:clamp(2rem,5vw,3.5rem);
      letter-spacing:-1px;background:linear-gradient(135deg,var(--accent1) 0%,#7c3aed 60%,var(--accent2) 100%);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
    .hero p{{margin-top:14px;color:var(--muted);font-size:1.05rem}}
    .csv-tag{{display:inline-block;margin-top:10px;padding:4px 14px;border-radius:999px;
      font-family:var(--mono);font-size:.75rem;
      background:rgba(0,229,255,.1);border:1px solid rgba(0,229,255,.25);color:var(--accent1)}}
    .badge-row{{margin-top:24px;display:flex;justify-content:center;gap:10px;flex-wrap:wrap}}
    .badge{{padding:5px 16px;border-radius:999px;font-size:.75rem;font-family:var(--mono);font-weight:700;letter-spacing:.5px;text-transform:uppercase}}
    .b1{{background:rgba(0,229,255,.15);color:var(--accent1);border:1px solid rgba(0,229,255,.3)}}
    .b2{{background:rgba(255,107,107,.15);color:var(--accent2);border:1px solid rgba(255,107,107,.3)}}
    .b3{{background:rgba(163,230,53,.15);color:var(--accent3);border:1px solid rgba(163,230,53,.3)}}
    .b4{{background:rgba(245,158,11,.15);color:var(--accent4);border:1px solid rgba(245,158,11,.3)}}
    .b5{{background:rgba(192,132,252,.15);color:#c084fc;border:1px solid rgba(192,132,252,.3)}}

    .container{{max-width:1200px;margin:0 auto;padding:0 24px 80px}}
    .section-title{{font-size:1.05rem;font-family:var(--mono);color:var(--accent1);
      text-transform:uppercase;letter-spacing:2px;margin:56px 0 24px;
      display:flex;align-items:center;gap:12px}}
    .section-title::after{{content:'';flex:1;height:1px;background:linear-gradient(to right,var(--border),transparent)}}

    .stat-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}}
    .stat-card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
      padding:28px;position:relative;overflow:hidden;transition:transform .2s,border-color .2s}}
    .stat-card:hover{{transform:translateY(-3px);border-color:var(--accent1)}}
    .stat-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px}}
    .stat-card.c1::before{{background:linear-gradient(90deg,var(--accent1),#7c3aed)}}
    .stat-card.c2::before{{background:linear-gradient(90deg,var(--accent2),#ec4899)}}
    .stat-card.c3::before{{background:linear-gradient(90deg,var(--accent3),var(--accent4))}}
    .stat-card h3{{font-size:.75rem;font-family:var(--mono);letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:18px}}
    .stat-row{{display:flex;justify-content:space-between;align-items:baseline;padding:7px 0;border-bottom:1px solid var(--border)}}
    .stat-row:last-child{{border-bottom:none}}
    .stat-row .label{{color:var(--muted);font-size:.88rem}}
    .stat-row .val{{font-family:var(--mono);font-size:1.05rem;font-weight:700}}
    .stat-row .val.hi{{color:var(--accent1)}}

    .chart-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:20px}}
    .chart-card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:24px}}
    .chart-card h4{{font-size:.78rem;font-family:var(--mono);letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);margin-bottom:16px}}
    .chart-card img{{width:100%;border-radius:8px;display:block}}

    .tabs{{display:flex;gap:4px;margin-bottom:20px;flex-wrap:wrap}}
    .tab-btn{{padding:8px 18px;border-radius:8px;border:1px solid var(--border);background:transparent;
      color:var(--muted);font-family:var(--mono);font-size:.78rem;cursor:pointer;transition:all .2s}}
    .tab-btn:hover{{border-color:var(--accent1);color:var(--accent1)}}
    .tab-btn.active{{background:var(--accent1);color:#000;border-color:var(--accent1);font-weight:700}}
    .tab-panel{{display:none}}.tab-panel.active{{display:block}}

    .table-wrap{{overflow-x:auto;margin-top:16px}}
    table{{width:100%;border-collapse:collapse;font-size:.88rem}}
    thead th{{background:var(--surface2);color:var(--accent1);font-family:var(--mono);font-size:.72rem;
      letter-spacing:1.5px;text-transform:uppercase;padding:12px 16px;text-align:left;border-bottom:2px solid var(--border)}}
    tbody tr{{border-bottom:1px solid var(--border);transition:background .15s}}
    tbody tr:hover{{background:var(--surface2)}}
    tbody td{{padding:10px 16px;font-family:var(--mono)}}
    tbody td.num{{color:var(--muted);font-size:.8rem}}
    .na{{color:var(--muted)}}
    .dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:middle}}

    .py-badge{{display:inline-flex;align-items:center;gap:6px;padding:3px 12px;border-radius:999px;
      font-family:var(--mono);font-size:.7rem;
      background:rgba(163,230,53,.1);border:1px solid rgba(163,230,53,.25);color:var(--accent3);
      margin-left:10px;vertical-align:middle}}

    footer{{text-align:center;padding:32px;color:var(--muted);font-size:.8rem;
      border-top:1px solid var(--border);font-family:var(--mono)}}
  </style>
</head>
<body>

<div class="hero">
  <h1>Análisis Estadístico</h1>
  <p>Peso · Altura · Velocidad · Color</p>
  <div class="csv-tag">📂 {os.path.basename(csv_path)} — {len(registros)} registros</div>
  <div class="badge-row">
    <span class="badge b1">Frecuencias Absolutas</span>
    <span class="badge b2">Frecuencias Relativas</span>
    <span class="badge b3">Frecuencias Acumuladas</span>
    <span class="badge b4">Media · Mediana · Moda</span>
    <span class="badge b5">🐍 Gráficas con Matplotlib</span>
  </div>
</div>

<div class="container">

  <!-- 01 TENDENCIA CENTRAL -->
  <div class="section-title">01 — Medidas de Tendencia Central</div>
  <div class="stat-grid">
    {stat_card("Peso (kg)",      "⚖️",  "c1", "peso",      "peso")}
    {stat_card("Altura (cm)",    "📏",  "c2", "altura",    "altura")}
    {stat_card("Velocidad (m/s)","⚡",  "c3", "velocidad", "vel")}
  </div>

  <!-- 02 FRECUENCIAS COLOR -->
  <div class="section-title">
    02 — Frecuencias por Color
    <span class="py-badge">🐍 matplotlib</span>
  </div>
  <div class="chart-grid">
    <div class="chart-card">
      <h4>📊 Frecuencia Absoluta — Barras</h4>
      <img src="{img['barColor']}" alt="Barras color"/>
    </div>
    <div class="chart-card">
      <h4>🥧 Frecuencia Relativa — Pastel</h4>
      <img src="{img['pieColor']}" alt="Pastel color"/>
    </div>
    <div class="chart-card">
      <h4>📈 Frecuencia Acumulada</h4>
      <img src="{img['acumColor']}" alt="Acumulada color"/>
    </div>
  </div>

  <!-- 03 DISTRIBUCIÓN NUMÉRICA -->
  <div class="section-title">
    03 — Distribución Numérica (Intervalos)
    <span class="py-badge">🐍 matplotlib</span>
  </div>
  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('peso',event)">Peso</button>
    <button class="tab-btn" onclick="switchTab('altura',event)">Altura</button>
    <button class="tab-btn" onclick="switchTab('velocidad',event)">Velocidad</button>
  </div>

  <div id="tab-peso" class="tab-panel active">
    <div class="chart-grid">
      <div class="chart-card"><h4>📊 Histograma — Peso</h4><img src="{img['histPeso']}" alt="Hist Peso"/></div>
      <div class="chart-card"><h4>📐 Polígono — Peso</h4><img src="{img['polyPeso']}" alt="Poly Peso"/></div>
    </div>
    <div class="chart-card" style="margin-top:18px">
      <h4>📋 Tabla de Frecuencias — Peso</h4>
      <div class="table-wrap">{tabla_intervalos(stats['peso']['ivs'])}</div>
    </div>
  </div>

  <div id="tab-altura" class="tab-panel">
    <div class="chart-grid">
      <div class="chart-card"><h4>📊 Histograma — Altura</h4><img src="{img['histAltura']}" alt="Hist Altura"/></div>
      <div class="chart-card"><h4>📐 Polígono — Altura</h4><img src="{img['polyAltura']}" alt="Poly Altura"/></div>
    </div>
    <div class="chart-card" style="margin-top:18px">
      <h4>📋 Tabla de Frecuencias — Altura</h4>
      <div class="table-wrap">{tabla_intervalos(stats['altura']['ivs'])}</div>
    </div>
  </div>

  <div id="tab-velocidad" class="tab-panel">
    <div class="chart-grid">
      <div class="chart-card"><h4>📊 Histograma — Velocidad</h4><img src="{img['histVel']}" alt="Hist Vel"/></div>
      <div class="chart-card"><h4>📐 Polígono — Velocidad</h4><img src="{img['polyVel']}" alt="Poly Vel"/></div>
    </div>
    <div class="chart-card" style="margin-top:18px">
      <h4>📋 Tabla de Frecuencias — Velocidad</h4>
      <div class="table-wrap">{tabla_intervalos(stats['velocidad']['ivs'])}</div>
    </div>
  </div>

  <!-- 04 RADAR -->
  <div class="section-title">
    04 — Gráficas de Telaraña (Radar)
    <span class="py-badge">🐍 matplotlib</span>
  </div>
  <div class="chart-grid">
    <div class="chart-card">
      <h4>🕸️ Radar — Estadísticas Normalizadas</h4>
      <p style="font-size:.8rem;color:var(--muted);margin-bottom:12px;font-family:var(--mono)">
        Media, Mediana y Moda normalizadas (0–100%) por variable.
      </p>
      <img src="{img['radarStats']}" alt="Radar stats"/>
    </div>
    <div class="chart-card">
      <h4>🕸️ Radar — Frecuencias por Color</h4>
      <p style="font-size:.8rem;color:var(--muted);margin-bottom:12px;font-family:var(--mono)">
        Frec. Absoluta, Relativa y Acumulada por color normalizadas.
      </p>
      <img src="{img['radarColor']}" alt="Radar color"/>
    </div>
  </div>

  <!-- 05 DATOS ORIGINALES -->
  <div class="section-title">05 — Datos Originales</div>
  <div class="chart-card">
    <div class="table-wrap">{tabla_raw()}</div>
  </div>

</div>

<footer>
  Generado con Python + Matplotlib · Fuente: {os.path.basename(csv_path)} · {len(registros)} registros
  · Variables: Peso, Altura, Velocidad, Color · Sin JavaScript para gráficas
</footer>

<script>
function switchTab(name, e) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  e.target.classList.add('active');
}}
</script>
</body>
</html>"""

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅  Página generada: {html_path}")
print(f"   Gráficas incrustadas como PNG base64 (sin dependencia de Chart.js)")