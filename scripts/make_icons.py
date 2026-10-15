#!/usr/bin/env python3
"""Generate the small project icons used in projects.md and projects/*.md.

Each icon is a 64x64 rounded card in the profile palette with one simple
line-art glyph. Edit ICONS (name -> (glyph, color)) and rerun:
    python3 scripts/make_icons.py
Writes assets/icons/<name>.svg.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "icons"

CARD, BORDER = "#16213a", "#2a3650"
TEAL, CORAL, LAVENDER, GOLD, SKY = "#6fd3c1", "#f2a07b", "#b39cf5", "#f2d07b", "#7bb8f2"


def stroke(c, w=3):
    return f'fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"'


def helix(c):
    a = "M18 12 C 46 22, 18 42, 46 52"
    b = "M46 12 C 18 22, 46 42, 18 52"
    rungs = "".join(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{c}" stroke-width="2" opacity=".55"/>'
                    for x1, x2, y in [(24, 40, 18), (22, 42, 32), (24, 40, 46)])
    return f'<path d="{a}" {stroke(c)}/><path d="{b}" {stroke(c)} opacity=".7"/>{rungs}'


def pipeline(c):
    nodes = [(14, 32), (28, 18), (28, 46), (42, 32), (52, 32)]
    lines = "".join(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{c}" stroke-width="2.5"/>'
                    for a, b in [(nodes[0], nodes[1]), (nodes[0], nodes[2]), (nodes[1], nodes[3]),
                                 (nodes[2], nodes[3]), (nodes[3], nodes[4])])
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="5" fill="{CARD}" stroke="{c}" stroke-width="2.5"/>' for x, y in nodes)
    return lines + dots


def magnifier(c):
    return (f'<path d="M14 14 C 30 20, 14 30, 30 36" {stroke(c, 2.5)} opacity=".6"/>'
            f'<circle cx="28" cy="28" r="12" {stroke(c)}/><line x1="37" y1="37" x2="50" y2="50" {stroke(c, 4)}/>')


def book(c):
    return (f'<path d="M32 18 C 26 14, 16 14, 12 16 V 48 C 16 46, 26 46, 32 50 Z" {stroke(c)}/>'
            f'<path d="M32 18 C 38 14, 48 14, 52 16 V 48 C 48 46, 38 46, 32 50" {stroke(c)}/>')


def grid_check(c):
    cells = "".join(f'<rect x="{12 + i * 14}" y="{12 + j * 14}" width="10" height="10" rx="2" '
                    f'fill="{c}" opacity="{.25 if (i + j) % 2 else .8}"/>' for i in range(3) for j in range(3))
    return cells + f'<path d="M36 46 l5 5 l10 -12" {stroke(GOLD, 3.5)}/>'


def bars(c):
    return "".join(f'<rect x="{12 + i * 10}" y="{52 - h}" width="7" height="{h}" rx="2" fill="{c}" opacity="{o}"/>'
                   for i, (h, o) in enumerate([(14, .5), (28, .7), (20, .6), (38, 1), (24, .7)]))


def chip(c):
    pins = "".join(f'<line x1="{x}" y1="10" x2="{x}" y2="18" {stroke(c, 2.5)}/><line x1="{x}" y1="46" x2="{x}" y2="54" {stroke(c, 2.5)}/>'
                   f'<line x1="10" y1="{x}" x2="18" y2="{x}" {stroke(c, 2.5)}/><line x1="46" y1="{x}" x2="54" y2="{x}" {stroke(c, 2.5)}/>'
                   for x in (24, 32, 40))
    return pins + f'<rect x="18" y="18" width="28" height="28" rx="4" {stroke(c)}/><rect x="26" y="26" width="12" height="12" rx="2" fill="{c}"/>'


def note(c):
    return (f'<path d="M26 44 V 16 L 48 12 V 40" {stroke(c)}/>'
            f'<ellipse cx="21" cy="44" rx="6" ry="5" fill="{c}"/><ellipse cx="43" cy="40" rx="6" ry="5" fill="{c}"/>')


def lights(c):
    return "".join(f'<path d="M{10 + i * 15} 22 h11 l-4 10 l4 10 h-11 l4 -10 z" fill="{c}" opacity="{o}"/>'
                   for i, o in enumerate([1, .6, .3]))


def wheel(c):
    spokes = "".join(f'<line x1="30" y1="36" x2="{30 + 13 * dx}" y2="{36 + 13 * dy}" stroke="{c}" stroke-width="2"/>'
                     for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1), (.7, .7), (-.7, .7), (.7, -.7), (-.7, -.7)])
    return (f'<circle cx="30" cy="36" r="15" {stroke(c)}/>{spokes}'
            f'<path d="M22 12 V 24 H 44 L 50 44" {stroke(c)}/><circle cx="50" cy="48" r="4" fill="{c}"/>')


def tree(c):
    return (f'<circle cx="32" cy="24" r="13" fill="{c}" opacity=".85"/><line x1="32" y1="36" x2="32" y2="52" {stroke(c, 4)}/>'
            f'<text x="32" y="28" text-anchor="middle" font-family="Arial,sans-serif" font-size="10" font-weight="700" fill="{CARD}">CO2</text>')


def cloud(c):
    return f'<path d="M20 44 h26 a9 9 0 0 0 0 -18 a12 12 0 0 0 -23 -3 a8 8 0 0 0 -3 21 z" {stroke(c)}/>'


def bucket(c):
    return (f'<ellipse cx="32" cy="16" rx="16" ry="5" {stroke(c)}/>'
            f'<path d="M16 16 L 20 48 C 22 52, 42 52, 44 48 L 48 16" {stroke(c)}/>'
            f'<path d="M18 30 C 26 34, 38 34, 46 30" {stroke(c, 2)} opacity=".6"/>')


def terminal(c):
    return (f'<rect x="10" y="14" width="44" height="36" rx="5" {stroke(c)}/>'
            f'<path d="M18 26 l7 6 l-7 6" {stroke(c)}/><line x1="30" y1="40" x2="44" y2="40" {stroke(c)}/>')


def gpu(c):
    return (f'<rect x="10" y="18" width="44" height="28" rx="4" {stroke(c)}/>'
            f'<circle cx="24" cy="32" r="7" {stroke(c, 2.5)}/><circle cx="42" cy="32" r="7" {stroke(c, 2.5)}/>'
            f'<line x1="14" y1="50" x2="14" y2="54" {stroke(c, 2.5)}/><line x1="22" y1="50" x2="22" y2="54" {stroke(c, 2.5)}/>')


def gauge(c):
    return (f'<path d="M12 42 A 20 20 0 0 1 52 42" {stroke(c)}/><line x1="32" y1="42" x2="42" y2="26" {stroke(GOLD, 3.5)}/>'
            f'<circle cx="32" cy="42" r="3.5" fill="{c}"/>')


def whale(c):
    return (f'<path d="M10 36 C 12 22, 40 18, 48 32 C 52 38, 50 44, 44 46 H 20 C 14 46, 10 42, 10 36 Z" fill="{c}"/>'
            f'<path d="M48 32 l8 -8 v14 z" fill="{c}"/><circle cx="20" cy="34" r="2" fill="{CARD}"/>'
            f'<path d="M26 18 C 24 12, 30 10, 30 6 M26 18 C 28 12, 22 10, 22 6" {stroke(SKY, 2)}/>')


def chat(c):
    return (f'<path d="M12 16 h40 v24 h-22 l-10 8 v-8 h-8 z" {stroke(c)}/>'
            + "".join(f'<circle cx="{x}" cy="28" r="2.5" fill="{c}"/>' for x in (22, 32, 42)))


def chat_widget(c):
    return chat(c) + f'<rect x="38" y="38" width="16" height="16" rx="3" fill="{c}"/><path d="M42 46 h8 M46 42 v8" {stroke(CARD, 2.5)}/>'


def checks(c):
    return "".join(f'<path d="M14 {y} l4 4 l8 -9" {stroke(c, 3)}/><line x1="32" y1="{y}" x2="50" y2="{y}" {stroke(c, 2.5)} opacity=".6"/>'
                   for y in (18, 32, 46))


def shield(c):
    return (f'<path d="M32 10 L 50 16 V 30 C 50 42, 42 50, 32 54 C 22 50, 14 42, 14 30 V 16 Z" {stroke(c)}/>'
            f'<path d="M22 26 h20 v14 h-20 z M22 26 l10 8 l10 -8" {stroke(c, 2)}/>')


def bank(c):
    return (f'<path d="M10 24 L 32 12 L 54 24 Z" {stroke(c)}/><line x1="10" y1="50" x2="54" y2="50" {stroke(c)}/>'
            + "".join(f'<line x1="{x}" y1="28" x2="{x}" y2="46" {stroke(c)}/>' for x in (18, 28, 36, 46)))


def globe(c):
    return (f'<circle cx="32" cy="32" r="20" {stroke(c)}/><ellipse cx="32" cy="32" rx="9" ry="20" {stroke(c, 2)}/>'
            f'<line x1="12" y1="32" x2="52" y2="32" {stroke(c, 2)}/>')


def pedigree(c):
    pts = [(32, 14), (20, 32), (44, 32), (14, 50), (26, 50), (38, 50), (50, 50)]
    lines = "".join(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{c}" stroke-width="2"/>'
                    for a, b in [(pts[0], pts[1]), (pts[0], pts[2]), (pts[1], pts[3]), (pts[1], pts[4]), (pts[2], pts[5]), (pts[2], pts[6])])
    return lines + "".join(f'<circle cx="{x}" cy="{y}" r="4.5" fill="{c}"/>' for x, y in pts)


def array_dots(c):
    return "".join(f'<circle cx="{14 + i * 9}" cy="{14 + j * 9}" r="3" fill="{c}" opacity="{.35 + .65 * ((i * 3 + j * 5) % 4 == 0)}"/>'
                   for i in range(5) for j in range(5))


def array_check(c):
    return array_dots(c) + f'<circle cx="46" cy="46" r="11" fill="{CARD}"/><path d="M40 46 l4 4 l8 -9" {stroke(GOLD, 3.5)}/>'


def goat(c):
    return (f'<path d="M22 22 C 14 18, 12 10, 18 8 M42 22 C 50 18, 52 10, 46 8" {stroke(c, 3)}/>'
            f'<path d="M20 22 h24 l-4 20 c -2 8, -14 8, -16 0 z" fill="{c}"/>'
            f'<path d="M28 50 l4 8 l4 -8" fill="{c}"/><circle cx="27" cy="30" r="2" fill="{CARD}"/><circle cx="37" cy="30" r="2" fill="{CARD}"/>')


def trio(c):
    return (f'<circle cx="20" cy="22" r="7" fill="{c}"/><circle cx="44" cy="22" r="7" fill="{c}" opacity=".7"/>'
            f'<circle cx="32" cy="46" r="7" fill="{GOLD}"/>'
            f'<path d="M20 29 L 32 39 M44 29 L 32 39" {stroke(c, 2.5)}/>')


def dice(c):
    return (f'<rect x="14" y="14" width="36" height="36" rx="7" {stroke(c)}/>'
            + "".join(f'<circle cx="{x}" cy="{y}" r="3" fill="{c}"/>' for x, y in [(23, 23), (32, 32), (41, 41), (41, 23), (23, 41)]))


def shortreads(c):
    return "".join(f'<line x1="{x}" y1="{y}" x2="{x + 12}" y2="{y}" {stroke(c, 3.5)} opacity="{o}"/>'
                   for x, y, o in [(10, 18, 1), (26, 18, .6), (16, 28, .8), (34, 28, 1), (12, 38, .6), (28, 38, .9), (20, 48, 1), (38, 48, .6)])


ICONS = {
    # genomics
    "pacer": (pipeline, TEAL), "research": (helix, LAVENDER),
    "tutorials": (book, TEAL), "vcf": (grid_check, SKY), "pangcontrol": (magnifier, TEAL),
    "chromosome": (bars, LAVENDER),
    # cloud
    "mapping-aws": (cloud, SKY), "basecall-aws": (gpu, TEAL), "wgs-s3": (bucket, CORAL),
    "shortread": (shortreads, LAVENDER), "orchestrator": (terminal, TEAL), "mcp": (gauge, SKY),
    # genotyping
    "snp-array": (array_check, TEAL),
    "pv-study": (trio, LAVENDER), "snp-sim": (dice, SKY), "pedigree": (pedigree, CORAL),
    # software
    "whale": (whale, SKY), "vgl-chatbot": (chat_widget, TEAL), "chatbot": (chat, LAVENDER),
    "phish": (shield, CORAL), "banking": (bank, GOLD), "website": (globe, SKY),
    # embedded
    "mp3": (note, LAVENDER), "taillights": (lights, CORAL), "wheelchair": (wheel, TEAL), "co2": (tree, TEAL),
    # category headers
    "cat-genomics": (helix, TEAL), "cat-cloud": (cloud, SKY), "cat-genotyping": (array_dots, LAVENDER),
    "cat-software": (terminal, CORAL), "cat-embedded": (chip, GOLD),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (glyph, color) in ICONS.items():
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'
               f'<rect x="1" y="1" width="62" height="62" rx="12" fill="{CARD}" stroke="{BORDER}" stroke-width="2"/>'
               f'{glyph(color)}</svg>\n')
        (OUT / f"{name}.svg").write_text(svg)
    print(f"wrote {len(ICONS)} icons to {OUT}")


if __name__ == "__main__":
    main()
