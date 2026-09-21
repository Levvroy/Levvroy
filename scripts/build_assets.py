"""Generate semua aset SVG profil dari profile.json.

Arah visual: PCB beneran. Soldermask hijau, jalur tembaga di bawah mask
(hijau lebih terang), pad emas (ENIG), silkscreen putih, designator komponen.
Tidak ada glow, gradient teks, atau blob. Animasi cuma LED status dan satu
sinyal di satu jalur.

Jalankan dari root repo:  python3 scripts/build_assets.py
Hanya pakai standard library.
"""

import json
import os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")

# ---- palet (satu tempat untuk mengubah semuanya) ----
MASK = "#0d2a1f"       # soldermask
MASK_DARK = "#081d15"  # bukaan mask di sekitar fiducial
TRACE = "#1f4d38"      # tembaga di bawah mask
GOLD = "#c9a14a"       # pad ENIG
HOLE = "#04100b"
SILK = "#ece8dc"       # silkscreen utama
SILK_2 = "#9fb3a6"     # silkscreen sekunder
LED = "#e5484d"
SIGNAL = "#e8c77e"

FONT = "Consolas, 'SF Mono', Menlo, 'DejaVu Sans Mono', 'Liberation Mono', monospace"
CHAR_W = 0.6  # perkiraan lebar karakter monospace relatif ke font-size


def text_w(s, size):
    return len(s) * size * CHAR_W


def svg(w, h, body, label, style=""):
    style_block = f"<style>{style}</style>" if style else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img" aria-label="{escape(label)}" '
        f'font-family="{FONT}">{style_block}{body}</svg>\n'
    )


def t(x, y, s, size, fill=SILK, weight=400, anchor="start", spacing=0):
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}" '
        f'letter-spacing="{spacing}">{escape(s)}</text>'
    )


def mount_hole(x, y, r=13):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{GOLD}"/><circle cx="{x}" cy="{y}" r="{r * 0.55:.1f}" fill="{HOLE}"/>'


def fiducial(x, y):
    return f'<circle cx="{x}" cy="{y}" r="9" fill="{MASK_DARK}"/><circle cx="{x}" cy="{y}" r="4" fill="{GOLD}"/>'


def via(x, y):
    return f'<circle cx="{x}" cy="{y}" r="6" fill="{GOLD}"/><circle cx="{x}" cy="{y}" r="2.6" fill="{HOLE}"/>'


def tht_pad(x, y, square=False):
    if square:  # pin 1 selalu persegi
        shape = f'<rect x="{x - 10}" y="{y - 10}" width="20" height="20" rx="2" fill="{GOLD}"/>'
    else:
        shape = f'<circle cx="{x}" cy="{y}" r="10" fill="{GOLD}"/>'
    return shape + f'<circle cx="{x}" cy="{y}" r="4.5" fill="{HOLE}"/>'


def chamfer_path(points, c=8):
    """Polyline dengan sudut dipotong 45 derajat, seperti routing PCB."""
    d = f"M{points[0][0]} {points[0][1]}"
    for i in range(1, len(points) - 1):
        (x0, y0), (x1, y1), (x2, y2) = points[i - 1], points[i], points[i + 1]

        def toward(ax, ay, bx, by, dist):
            dx, dy = bx - ax, by - ay
            ln = max((dx * dx + dy * dy) ** 0.5, 1e-9)
            dist = min(dist, ln / 2)
            return ax + dx / ln * dist, ay + dy / ln * dist

        px, py = toward(x1, y1, x0, y0, c)
        nx, ny = toward(x1, y1, x2, y2, c)
        d += f" L{px:.1f} {py:.1f} L{nx:.1f} {ny:.1f}"
    d += f" L{points[-1][0]} {points[-1][1]}"
    return d


def board(w, h, rx):
    return f'<rect width="{w}" height="{h}" rx="{rx}" fill="{MASK}"/>'


LED_STYLE = (
    ".led{animation:blink 2s steps(1) infinite}"
    "@keyframes blink{50%{opacity:.22}}"
)


def smd_led(x, y, label, designator):
    return (
        f'<rect x="{x - 14}" y="{y - 6}" width="9" height="12" rx="1" fill="{GOLD}"/>'
        f'<rect x="{x + 5}" y="{y - 6}" width="9" height="12" rx="1" fill="{GOLD}"/>'
        f'<rect class="led" x="{x - 5}" y="{y - 5}" width="10" height="10" rx="1.5" fill="{LED}"/>'
        + t(x, y - 14, label, 11, SILK, anchor="middle")
        + t(x, y + 24, designator, 11, SILK_2, anchor="middle")
    )


def smd_part(x, y, designator):
    return (
        f'<rect x="{x - 12}" y="{y - 6}" width="9" height="12" rx="1" fill="{GOLD}"/>'
        f'<rect x="{x + 3}" y="{y - 6}" width="9" height="12" rx="1" fill="{GOLD}"/>'
        f'<rect x="{x - 16}" y="{y - 10}" width="32" height="20" rx="2" fill="none" stroke="{SILK}" stroke-opacity=".55" stroke-width="1.2"/>'
        + t(x, y + 24, designator, 11, SILK_2, anchor="middle")
    )


# ---------------------------------------------------------------- header
def build_header(cfg):
    W, H = 1200, 360
    b = [board(W, H, 16)]
    b += [mount_hole(34, 34), mount_hole(W - 34, 34), mount_hole(34, H - 34), mount_hole(W - 34, H - 34)]
    b += [fiducial(96, 330), fiducial(1110, 36)]

    # silkscreen kiri atas
    if cfg.get("board_id"):
        b.append(t(70, 60, cfg["board_id"], 14, SILK, spacing=1))
    if cfg.get("revision"):
        rx = 70 + (text_w(cfg["board_id"], 14) + 24 if cfg.get("board_id") else 0)
        b.append(t(rx, 60, cfg["revision"], 14, SILK_2, spacing=1))

    # nama + tagline
    b.append(t(66, 160, cfg["name"], 62, SILK, weight=700, spacing=-1))
    y = 204
    for i, line in enumerate(cfg["tagline"]):
        b.append(t(70, y, line, 19 if i == 0 else 17, SILK if i == 0 else SILK_2))
        y += 30

    # modul ESP32 (U1)
    mx, my, mw, mh = 850, 62, 240, 250
    pad_ys = [290 - k * 20 for k in range(6)]  # pad kiri modul, bawah ke atas

    # jalur dari konektor J1 ke pad modul, dirouting tanpa saling silang
    pins_x = [70 + k * 36 for k in range(6)]
    traces = []
    for k in range(6):
        level = 346 - k * 7
        riser = 830 - k * 12
        pts = [(pins_x[k], 292), (pins_x[k], level), (riser, level), (riser, pad_ys[k]), (mx, pad_ys[k])]
        traces.append(chamfer_path(pts))
    for d in traces:
        b.append(f'<path d="{d}" fill="none" stroke="{TRACE}" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/>')
    # satu sinyal lewat di jalur TX
    b.append(
        f'<path class="sig" d="{traces[2]}" fill="none" stroke="{SIGNAL}" stroke-width="3.2" '
        f'stroke-linecap="round" pathLength="1000"/>'
    )

    # outline silkscreen modul + designator
    b.append(f'<rect x="{mx - 12}" y="{my - 12}" width="{mw + 24}" height="{mh + 24}" rx="4" fill="none" stroke="{SILK}" stroke-opacity=".6" stroke-width="1.4"/>')
    b.append(t(mx - 12, my - 20, "U1", 12, SILK_2))
    # PCB modul + antena meander
    b.append(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="4" fill="#12181b"/>')
    ant = f"M{mx + 30} {my + 48} V{my + 18} H{mx + 60} V{my + 48} H{mx + 90} V{my + 18} H{mx + 120} V{my + 48} H{mx + 150} V{my + 18} H{mx + 180} V{my + 48} H{mx + 210}"
    b.append(f'<path d="{ant}" fill="none" stroke="#9c7338" stroke-width="3"/>')
    # shield logam
    sx, sy = mx + 16, my + 72
    b.append(f'<rect x="{sx}" y="{sy}" width="{mw - 32}" height="{mh - 88}" rx="3" fill="#b3b7b8"/>')
    b.append(f'<rect x="{sx}" y="{sy}" width="{mw - 32}" height="{mh - 88}" rx="3" fill="none" stroke="#8d9192" stroke-width="1"/>')
    b.append(t(sx + 16, sy + 34, "ESP32-WROOM-32E", 15, "#3a3f41", weight=700))
    b.append(t(sx + 16, sy + 56, "Wi-Fi + BT", 12, "#555a5c"))
    # castellated pads
    for k in range(8):
        py = my + 100 + k * 20
        b.append(f'<rect x="{mx - 5}" y="{py - 4}" width="12" height="8" rx="1" fill="{GOLD}"/>')
        b.append(f'<rect x="{mx + mw - 7}" y="{py - 4}" width="12" height="8" rx="1" fill="{GOLD}"/>')

    # konektor J1
    b.append(t(pins_x[0] - 22, 272, "J1", 11, SILK_2, anchor="end"))
    for k, lab in enumerate(cfg["connector_labels"][:6]):
        b.append(t(pins_x[k], 268, lab, 10, SILK, anchor="middle"))
    b.append(f'<rect x="{pins_x[0] - 16}" y="276" width="{pins_x[5] - pins_x[0] + 32}" height="32" rx="2" fill="none" stroke="{SILK}" stroke-opacity=".55" stroke-width="1.2"/>')
    for k, px in enumerate(pins_x):
        b.append(tht_pad(px, 292, square=(k == 0)))

    # komponen kecil
    b.append(smd_led(330, 292, "STAT", "D1"))
    b.append(smd_part(400, 292, "R1"))
    b.append(smd_part(460, 292, "C1"))

    b.append(t(W - 70, 346, cfg["site"], 12, SILK_2, anchor="end"))

    style = LED_STYLE + (
        ".sig{stroke-dasharray:40 960;animation:sig 4.5s linear infinite}"
        "@keyframes sig{from{stroke-dashoffset:40}to{stroke-dashoffset:-1000}}"
    )
    return svg(W, H, "".join(b), f"{cfg['name']}, {cfg['tagline'][0]}", style)


# ---------------------------------------------------------------- section divider
def build_section(sec):
    W, H = 1200, 64
    b = [board(W, H, 10)]
    b.append(tht_pad(34, 32, square=True))
    b.append(tht_pad(62, 32))
    title_x = 96
    b.append(t(title_x, 39, sec["num"], 18, SILK_2))
    tx = title_x + text_w(sec["num"], 18) + 16
    b.append(t(tx, 39, sec["title"], 20, SILK, weight=700, spacing=1))
    end = tx + text_w(sec["title"], 20) + len(sec["title"])  # + letter-spacing
    if sec.get("note"):
        b.append(t(end + 8, 38, sec["note"], 13, SILK_2))
        end += 8 + text_w(sec["note"], 13)
    b.append(f'<path d="M{end + 24:.0f} 32 H{W - 48}" stroke="{TRACE}" stroke-width="3.2" stroke-linecap="round"/>')
    b.append(via(W - 40, 32))
    return svg(W, H, "".join(b), f"{sec['num']} {sec['title']}")


# ---------------------------------------------------------------- project card
def wrap(s, max_chars):
    lines, cur = [], ""
    for word in s.split():
        if len(cur) + len(word) + (1 if cur else 0) > max_chars:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    if cur:
        lines.append(cur)
    return lines


def build_card(p, idx):
    W, H = 600, 250
    running = p.get("status", "").upper() != "SELESAI"
    b = [board(W, H, 12)]
    b += [mount_hole(W - 26, 26, 9), mount_hole(W - 26, H - 26, 9)]
    b.append(t(30, 40, f"P{idx}", 12, SILK_2))
    b.append(f'<rect x="{30 + text_w(f"P{idx}", 12) + 10}" y="31" width="10" height="10" rx="1" fill="{GOLD}"/>')
    # status: LED hijau = selesai, kuning berkedip = masih berjalan
    if p.get("status"):
        sx = W - 52
        b.append(t(sx, 40, p["status"], 11, SILK_2, anchor="end", spacing=1))
        lx = sx - text_w(p["status"], 11) - len(p["status"]) - 16
        color = "#e0a82e" if running else "#46a06b"
        cls = ' class="led"' if running else ""
        b.append(f'<rect{cls} x="{lx:.0f}" y="31" width="10" height="10" rx="1.5" fill="{color}"/>')
    b.append(t(28, 84, p["name"], 26, SILK, weight=700))
    if p.get("meta"):
        b.append(t(30, 110, p["meta"], 13, GOLD))
    y = 142
    for line in wrap(p["desc"], 56)[:3]:
        b.append(t(30, y, line, 15, SILK_2))
        y += 21
    x = 30
    for s_ in p["stack"]:
        b.append(f'<rect x="{x}" y="206" width="10" height="10" rx="1" fill="{GOLD}"/>')
        b.append(t(x + 16, 215, s_, 13, SILK))
        x += 16 + text_w(s_, 13) + 22
    b.append(t(W - 52, 215, "REPO ->", 12, SILK_2, anchor="end"))
    return svg(W, H, "".join(b), p["name"], LED_STYLE if running else "")


# ---------------------------------------------------------------- CTA (tactile switch)
def build_cta(c):
    W, H = 400, 120
    b = [board(W, H, 12)]
    # footprint tact switch 6x6: outline silk, 4 pad, cap bulat
    cx, cy = 66, 60
    b.append(f'<rect x="{cx - 34}" y="{cy - 34}" width="68" height="68" rx="3" fill="none" stroke="{SILK}" stroke-opacity=".6" stroke-width="1.4"/>')
    for dx in (-34, 34):
        for dy in (-22, 22):
            b.append(f'<rect x="{cx + dx - 7}" y="{cy + dy - 5}" width="14" height="10" rx="1" fill="{GOLD}"/>')
    b.append(f'<rect x="{cx - 24}" y="{cy - 24}" width="48" height="48" rx="4" fill="#1a1f21" stroke="#2c3336" stroke-width="1.5"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="15" fill="#252b2e" stroke="#3a4245" stroke-width="1.5"/>')
    b.append(t(128, 46, f'{c["ref"]}  {c["label"]}', 12, SILK_2, spacing=1))
    size = 22 if len(c["text"]) <= 18 else 18
    b.append(t(128, 80, c["text"], size, SILK, weight=700))
    b.append(t(W - 22, 46, "->", 13, GOLD, anchor="end"))
    return svg(W, H, "".join(b), f'{c["label"]}: {c["text"]}')


# ---------------------------------------------------------------- toolkit (BOM)
def build_bom(rows):
    W = 1200
    H = 90 + len(rows) * 46
    b = [board(W, H, 12)]
    cols = [(48, "REF"), (150, "GROUP"), (400, "PARTS")]
    for x, lab in cols:
        b.append(t(x, 46, lab, 13, SILK_2, spacing=2))
    b.append(f'<path d="M40 62 H{W - 40}" stroke="{SILK}" stroke-opacity=".35" stroke-width="1.2"/>')
    y = 100
    for r in rows:
        b.append(t(48, y, r["ref"], 16, SILK_2))
        b.append(t(150, y, r["group"], 17, SILK, weight=700))
        x = 400
        for part in r["parts"]:
            b.append(f'<rect x="{x}" y="{y - 11}" width="10" height="10" rx="1" fill="{GOLD}"/>')
            b.append(t(x + 18, y, part, 17, SILK))
            x += 18 + text_w(part, 17) + 34
        y += 46
    return svg(W, H, "".join(b), "Toolkit")


# ---------------------------------------------------------------- footer
def build_footer(cfg):
    W, H = 1200, 80
    b = [board(W, H, 12)]
    b.append(mount_hole(30, 40, 10))
    b.append(mount_hole(W - 30, 40, 10))
    left = cfg["name"] + (f" · {cfg['board_id']}" if cfg.get("board_id") else "")
    b.append(t(60, 45, left, 13, SILK_2))
    right_w = text_w(cfg["site"], 13)
    b.append(t(W - 60, 45, cfg["site"], 13, SILK_2, anchor="end"))
    start = 60 + text_w(left, 13) + 28
    stop = W - 60 - right_w - 28
    mid = (start + stop) / 2
    b.append(f'<path d="M{start:.0f} 40 H{mid - 40:.0f}" stroke="{TRACE}" stroke-width="3.2" stroke-linecap="round"/>')
    b.append(f'<path d="M{mid + 40:.0f} 40 H{stop:.0f}" stroke="{TRACE}" stroke-width="3.2" stroke-linecap="round"/>')
    b.append(
        f'<rect x="{mid - 24}" y="34" width="9" height="12" rx="1" fill="{GOLD}"/>'
        f'<rect x="{mid + 15}" y="34" width="9" height="12" rx="1" fill="{GOLD}"/>'
        f'<rect class="led" x="{mid - 5}" y="35" width="10" height="10" rx="1.5" fill="{LED}"/>'
    )
    return svg(W, H, "".join(b), "footer", LED_STYLE)


def main():
    with open(os.path.join(ROOT, "profile.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    os.makedirs(OUT, exist_ok=True)

    files = {"header.svg": build_header(cfg), "footer.svg": build_footer(cfg), "toolkit.svg": build_bom(cfg["toolkit"])}
    for sec in cfg["sections"]:
        files[sec["file"] + ".svg"] = build_section(sec)
    for i, p in enumerate(cfg["projects"], start=1):
        files[f"project-{i}.svg"] = build_card(p, i)
    for c in cfg.get("contact", []):
        files[f"cta-{c['label'].lower()}.svg"] = build_cta(c)

    for name, content in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(content)
        print("wrote assets/" + name)


if __name__ == "__main__":
    main()
