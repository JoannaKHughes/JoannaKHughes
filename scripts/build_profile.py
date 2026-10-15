#!/usr/bin/env python3
"""Build the GitHub profile README and its generated assets.

Runs on magpie (cron, see update_profile.sh) rather than in GitHub Actions:
the lab GitLab server is only reachable from the campus network.

Inputs
  - GitHub daily contributions: GraphQL API when a token is available
    (includes private contributions), otherwise the public contributions page.
  - GitLab daily events: /api/v4/users/:id/events with a read_api token,
    otherwise the public calendar.json (empty when the profile is private).
  - projects.md: hand-maintained Projects tables, copied into the README.

Tokens are read from the environment (PROFILE_TOKEN, GITLAB_TOKEN) or from
~/.config/profile/{github_token,gitlab_token}. They are never printed.

Outputs: README.md, assets/stats.svg, assets/kelp.svg (monthly, as kelp),
assets/school.svg (daily, as a school of fish). Colors: GitHub / GitLab / Private.

--demo: fills in made-up numbers and writes everything to preview/ instead
(plus preview/preview.html to open in a browser). Nothing real is touched and
preview/ is gitignored, so demo numbers never reach the published profile.
"""

import datetime as dt
import html
import json
import math
import os
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GITHUB_USER = "JoannaKHughes"
GITLAB_HOST = os.environ.get("GITLAB_HOST", "https://gitlab.vgl.cvg.ucdavis.edu")
GITLAB_USER = os.environ.get("GITLAB_USER", "joanna")

# LinkedIn custom URL slug (linkedin.com/in/<slug>). Change here if it changes on LinkedIn.
LINKEDIN = "jokhughes"

DEGREES = [
    # (degree, school, year)
    ("M.S. Computer Science", "University of the Pacific", 2025),
    ("B.S. Computer Engineering", "University of the Pacific", 2025),
]

ROOT = Path(__file__).resolve().parent.parent
TOKEN_DIR = Path.home() / ".config" / "profile"
DAYS = 365

# Palette taken from assets/banner.png
BG = "#111a2e"
CARD = "#16213a"
BORDER = "#2a3650"
TEXT = "#e8edf5"
MUTED = "#8b97ad"
TEAL = "#6fd3c1"
LEVELS = ["#1a2540", "#1d4e5a", "#2a7f7a", "#4fb3a3", "#8fe3d3"]
SOURCES = {"GitHub": "#6fd3c1", "GitLab": "#f2a07b", "Private": "#b39cf5"}  # teal, coral, lavender
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_token(env_name, file_name):
    value = os.environ.get(env_name, "").strip()
    if value:
        return value
    path = TOKEN_DIR / file_name
    if path.is_file():
        return path.read_text().strip() or None
    return None


def http_get(url, headers=None, data=None, timeout=30):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    req.add_header("User-Agent", "profile-builder")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8"), resp.headers


def log(msg):
    print(f"[build_profile] {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

def merge(*dicts):
    out = defaultdict(int)
    for d in dicts:
        for k, v in d.items():
            out[k] += v
    return dict(out)


def github_contributions(start, end):
    """Return (public {date: count}, private {date: count}, source, repo_count or None).

    With a token, private-repo commits are split out per day via
    commitContributionsByRepository; the rest of the calendar counts as GitHub.
    Without a token everything on the public page counts as GitHub.
    """
    token = read_token("PROFILE_TOKEN", "github_token")
    if token:
        query = """
        query($login: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $login) {
            repositories(ownerAffiliations: OWNER) { totalCount }
            contributionsCollection(from: $from, to: $to) {
              contributionCalendar {
                weeks { contributionDays { date contributionCount } }
              }
              commitContributionsByRepository(maxRepositories: 100) {
                repository { isPrivate }
                contributions(first: 100) { nodes { occurredAt commitCount } }
              }
            }
          }
        }"""
        body = json.dumps({"query": query, "variables": {
            "login": GITHUB_USER,
            "from": f"{start.isoformat()}T00:00:00Z",
            "to": f"{end.isoformat()}T23:59:59Z",
        }}).encode()
        try:
            text, _ = http_get("https://api.github.com/graphql", data=body, headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
            })
            payload = json.loads(text)
            if "errors" in payload:
                raise RuntimeError(payload["errors"][0].get("message", "GraphQL error"))
            user = payload["data"]["user"]
            coll = user["contributionsCollection"]
            total = {}
            for week in coll["contributionCalendar"]["weeks"]:
                for day in week["contributionDays"]:
                    total[dt.date.fromisoformat(day["date"])] = day["contributionCount"]
            private = defaultdict(int)
            for repo in coll["commitContributionsByRepository"]:
                if repo["repository"]["isPrivate"]:
                    for node in repo["contributions"]["nodes"]:
                        private[dt.date.fromisoformat(node["occurredAt"][:10])] += node["commitCount"]
            public = {k: max(0, v - private.get(k, 0)) for k, v in total.items()}
            return public, dict(private), "GitHub API (private split out)", user["repositories"]["totalCount"]
        except Exception as exc:  # fall back to the public page
            log(f"GitHub API failed ({type(exc).__name__}); using public contributions page")

    text, _ = http_get(f"https://github.com/users/{GITHUB_USER}/contributions"
                       f"?from={start.isoformat()}&to={end.isoformat()}")
    dates = dict(re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*?id="([^"]+)"', text))
    if not dates:
        dates = {d: i for i, d in re.findall(r'id="([^"]+)"[^>]*?data-date="(\d{4}-\d{2}-\d{2})"', text)}
        dates = {v: k for k, v in dates.items()}
    tips = dict(re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', text))
    days = {}
    for date_s, cell_id in dates.items():
        m = re.match(r"(\d+) contribution", tips.get(cell_id, ""))
        days[dt.date.fromisoformat(date_s)] = int(m.group(1)) if m else 0
    return days, {}, "GitHub public page", None


def gitlab_contributions(start, end):
    """Return (public {date: count}, private {date: count}, source).

    Events in private or internal projects count as Private.
    """
    token = read_token("GITLAB_TOKEN", "gitlab_token")
    api = f"{GITLAB_HOST}/api/v4"
    if token:
        try:
            headers = {"PRIVATE-TOKEN": token}
            text, _ = http_get(f"{api}/users?username={urllib.parse.quote(GITLAB_USER)}", headers=headers)
            user_id = json.loads(text)[0]["id"]
            public, private = defaultdict(int), defaultdict(int)
            visibility = {}

            def is_private(project_id):
                if project_id is None:
                    return False
                if project_id not in visibility:
                    try:
                        t, _ = http_get(f"{api}/projects/{project_id}", headers=headers)
                        visibility[project_id] = json.loads(t).get("visibility", "private")
                    except Exception:
                        visibility[project_id] = "private"
                return visibility[project_id] != "public"

            page = 1
            while page:
                url = (f"{api}/users/{user_id}/events?per_page=100&page={page}"
                       f"&after={(start - dt.timedelta(days=1)).isoformat()}"
                       f"&before={(end + dt.timedelta(days=1)).isoformat()}")
                text, resp_headers = http_get(url, headers=headers)
                for event in json.loads(text):
                    day = dt.date.fromisoformat(event["created_at"][:10])
                    if start <= day <= end:
                        (private if is_private(event.get("project_id")) else public)[day] += 1
                nxt = resp_headers.get("X-Next-Page", "")
                page = int(nxt) if nxt.isdigit() else 0
            return dict(public), dict(private), "GitLab API (private split out)"
        except Exception as exc:
            log(f"GitLab API failed ({type(exc).__name__}); using public calendar")

    try:
        text, _ = http_get(f"{GITLAB_HOST}/users/{urllib.parse.quote(GITLAB_USER)}/calendar.json")
        raw = json.loads(text) or {}
        return {dt.date.fromisoformat(k): v for k, v in raw.items()}, {}, "GitLab public calendar"
    except Exception as exc:
        log(f"GitLab calendar unavailable ({type(exc).__name__}); GitLab counted as 0")
        return {}, {}, "GitLab unavailable"


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def svg_open(width, height, label):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(label)}">',
        f'<rect width="{width}" height="{height}" rx="12" fill="{BG}"/>',
    ]


def legend(x, y):
    parts = []
    for name, color in SOURCES.items():
        parts += [
            f'<rect x="{x}" y="{y - 9}" width="10" height="10" rx="2" fill="{color}"/>',
            f'<text x="{x + 15}" y="{y}" fill="{MUTED}" font-family="{FONT}" font-size="12">{name}</text>',
        ]
        x += 24 + 7 * len(name)
    return parts


def stats_svg(cards):
    width, height, gap, pad = 1000, 150, 16, 20
    card_w = (width - 2 * pad - gap * (len(cards) - 1)) / len(cards)
    parts = svg_open(width, height, "Contribution statistics")
    for i, (value, label, color) in enumerate(cards):
        x = pad + i * (card_w + gap)
        parts += [
            f'<rect x="{x:.1f}" y="{pad}" width="{card_w:.1f}" height="{height - 2 * pad}" rx="10" '
            f'fill="{CARD}" stroke="{BORDER}"/>',
            f'<rect x="{x:.1f}" y="{pad}" width="{card_w:.1f}" height="3" rx="1.5" fill="{color}"/>',
            f'<text x="{x + 16:.1f}" y="{pad + 55}" fill="{TEXT}" font-family="{FONT}" '
            f'font-size="32" font-weight="600">{html.escape(str(value))}</text>',
            f'<text x="{x + 16:.1f}" y="{pad + 86}" fill="{MUTED}" font-family="{FONT}" '
            f'font-size="13">{html.escape(label)}</text>',
        ]
    parts.append("</svg>")
    return "\n".join(parts)


def kelp_svg(by_source, start, end):
    """Monthly contributions as a kelp forest: one swaying stalk per month,
    stacked GitHub / GitLab / Private from the seafloor up."""
    months = []
    d = dt.date(start.year, start.month, 1)
    while d <= end:
        months.append(d)
        d = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    counts = [[sum(v for k, v in src.items() if (k.year, k.month) == (m.year, m.month))
               for src in by_source.values()] for m in months]
    top = max([sum(c) for c in counts] + [1])

    width, height, pad = 1000, 340, 30
    floor, max_h = height - 50, 220
    spacing = (width - 2 * pad) / len(months)
    colors = list(SOURCES.values())
    parts = svg_open(width, height, "Kelp forest: monthly contributions by source")
    parts += [
        f'<defs><linearGradient id="water" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#16325a"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{width}" height="{floor}" rx="12" fill="url(#water)"/>',
        f'<text x="{pad}" y="28" fill="{TEXT}" font-family="{FONT}" font-size="16" '
        f'font-weight="600">Kelp forest: monthly contributions</text>',
    ]
    parts += legend(width - pad - 230, 27)

    for i, (m, cs) in enumerate(zip(months, counts)):
        base_x = pad + spacing * (i + 0.5)
        total = sum(cs)
        h = max(8, total / top * max_h) if total else 8
        sway = 1.5 + (i % 3) * 0.6
        parts.append(f'<g><animateTransform attributeName="transform" type="rotate" '
                     f'values="-{sway} {base_x:.1f} {floor};{sway} {base_x:.1f} {floor};-{sway} {base_x:.1f} {floor}" '
                     f'dur="{5 + (i % 4) * 0.7:.1f}s" repeatCount="indefinite"/>')

        def pt(y_off):  # point on the wavy stalk, y_off measured up from the floor
            return base_x + 5 * math.sin(y_off / 22 + i), floor - y_off

        # stalk segments, bottom to top: GitHub, GitLab, Private
        y0 = 0.0
        seg_bounds = []
        for c, color in zip(cs, colors):
            seg_h = h * c / total if total else 0
            if seg_h > 0:
                seg_bounds.append((y0, y0 + seg_h, color))
                pts = [pt(y0 + (seg_h * s / 12)) for s in range(13)]
                parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" '
                             f'fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round"/>')
            y0 += seg_h
        if not total:
            x, y = pt(h)
            parts.append(f'<line x1="{base_x:.1f}" y1="{floor}" x2="{x:.1f}" y2="{y:.1f}" '
                         f'stroke="{BORDER}" stroke-width="4" stroke-linecap="round"/>')

        # blades every 16 px, alternating sides, colored by the segment they grow from
        y_off, side = 12.0, 1
        while y_off < h - 6:
            color = next((col for a, b, col in seg_bounds if a <= y_off < b), BORDER)
            x, y = pt(y_off)
            parts.append(f'<ellipse cx="{x + side * 8:.1f}" cy="{y:.1f}" rx="9" ry="3.2" fill="{color}" '
                         f'opacity="0.8" transform="rotate({-side * 30} {x + side * 8:.1f} {y:.1f})"/>')
            y_off += 16
            side = -side
        if total:
            x, y = pt(h)
            parts += [
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{seg_bounds[-1][2]}"/>',
                f'<ellipse cx="{x + 4:.1f}" cy="{y - 9:.1f}" rx="12" ry="3.5" fill="{seg_bounds[-1][2]}" '
                f'opacity="0.85" transform="rotate(-60 {x + 4:.1f} {y - 9:.1f})"/>',
                f'<text x="{x:.1f}" y="{y - 22:.1f}" fill="{MUTED}" font-family="{FONT}" font-size="11" '
                f'text-anchor="middle">{total}</text>',
            ]
        parts.append("</g>")
        parts.append(f'<text x="{base_x:.1f}" y="{floor + 32}" fill="{MUTED}" font-family="{FONT}" '
                     f'font-size="11" text-anchor="middle">{m.strftime("%b %y")}</text>')

    # seafloor with a few rocks
    parts.append(f'<path d="M0 {floor} Q {width / 4} {floor - 6} {width / 2} {floor} T {width} {floor} '
                 f'V {height - 12} Q {width} {height} {width - 12} {height} H 12 Q 0 {height} 0 {height - 12} Z" '
                 f'fill="#1c2742"/>')
    for k in range(9):
        rx = pad + k * (width - 2 * pad) / 8
        parts.append(f'<ellipse cx="{rx:.1f}" cy="{floor + 4}" rx="{7 + k % 3 * 3}" ry="4" fill="{BORDER}"/>')
    for k, m in enumerate(months):  # redraw month labels over the sand
        parts.append(f'<text x="{pad + spacing * (k + 0.5):.1f}" y="{floor + 32}" fill="{MUTED}" '
                     f'font-family="{FONT}" font-size="11" text-anchor="middle">{m.strftime("%b %y")}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def school_svg(by_source, start, end):
    """Daily contributions as a school of fish: one fish per active day,
    colored by that day's main source, brighter on busier days."""
    cell, gap, left, top = 16, 2, 20, 44
    first = start - dt.timedelta(days=(start.weekday() + 1) % 7)  # Sunday-aligned
    n_weeks = ((end - first).days // 7) + 1
    width = left * 2 + n_weeks * (cell + gap)
    height = top + 7 * (cell + gap) + 16
    colors = list(SOURCES.values())

    totals = merge(*by_source.values())
    nonzero = sorted(v for v in totals.values() if v > 0)

    def level(v):
        if v <= 0 or not nonzero:
            return 0
        q = [nonzero[max(0, int(len(nonzero) * f) - 1)] for f in (0.25, 0.5, 0.75)]
        return 1 + sum(v > t for t in q)

    opacity = [0, 0.4, 0.6, 0.8, 1.0]
    parts = svg_open(width, height, "School of fish: daily contributions by source")
    parts.append(f'<text x="{left}" y="26" fill="{TEXT}" font-family="{FONT}" font-size="16" '
                 f'font-weight="600">Daily contributions, last 12 months</text>')
    parts += legend(width - left - 230, 25)

    for w in range(n_weeks):
        # each week column bobs a little, out of phase with its neighbours
        parts.append(f'<g><animateTransform attributeName="transform" type="translate" '
                     f'values="0 0;0 -1.5;0 0;0 1.5;0 0" dur="4s" begin="-{(w * 0.15) % 4:.2f}s" '
                     f'repeatCount="indefinite"/>')
        for r in range(7):
            day = first + dt.timedelta(days=w * 7 + r)
            if not start <= day <= end:
                continue
            cx = left + w * (cell + gap) + cell / 2
            cy = top + r * (cell + gap) + cell / 2
            v = totals.get(day, 0)
            if not v:
                parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.6" fill="{BORDER}"/>')
                continue
            src = max(range(len(colors)), key=lambda i: list(by_source.values())[i].get(day, 0))
            col, op = colors[src], opacity[level(v)]
            parts.append(
                f'<g fill="{col}" opacity="{op}">'
                f'<ellipse cx="{cx + 1:.1f}" cy="{cy:.1f}" rx="5.3" ry="3.6"/>'
                f'<polygon points="{cx - 3.4:.1f},{cy:.1f} {cx - 7.4:.1f},{cy - 3.7:.1f} {cx - 7.4:.1f},{cy + 3.7:.1f}"/>'
                f'</g><circle cx="{cx + 3.8:.1f}" cy="{cy - 0.9:.1f}" r="0.9" fill="{BG}"/>'
            )
        parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts)


def readme(projects_md, updated):
    degrees = "\n".join(f"- {d}, {s}, {y}" for d, s, y in DEGREES)
    return f"""<p align="center">
  <img src="assets/banner.png" alt="Joanna Hughes" width="100%">
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/{LINKEDIN}"><img src="https://img.shields.io/badge/LinkedIn-{LINKEDIN.replace('-', '--')}-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"></a>
</p>

## Degrees

{degrees}

## Stats

<p align="center">
  <img src="assets/stats.svg" alt="Contribution statistics" width="100%">
</p>

<p align="center">
  <img src="assets/kelp.svg" alt="Monthly contributions by source, drawn as kelp" width="100%">
</p>

<p align="center">
  <img src="assets/school.svg" alt="Daily contributions by source, drawn as a school of fish" width="100%">
</p>

{projects_md.strip()}

<sub>Updated {updated} · generated by <code>scripts/build_profile.py</code></sub>
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def demo_data(start):
    """Made-up daily counts for previewing the layout (--demo only)."""
    import random
    rng = random.Random(7)
    github, gitlab, private = {}, {}, {}
    for i in range(DAYS):
        day = start + dt.timedelta(days=i)
        busy = 1.0 if day.weekday() < 5 else 0.3
        if rng.random() < 0.35 * busy:
            github[day] = rng.randint(1, 9)
        if rng.random() < 0.45 * busy:
            gitlab[day] = rng.randint(1, 14)
        if rng.random() < 0.3 * busy:
            private[day] = rng.randint(1, 8)
    return github, gitlab, private, 28


def preview_html(demo_note):
    degrees = "".join(f"<li>{html.escape(d)}, {html.escape(s)}, {y}</li>" for d, s, y in DEGREES)
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Profile preview</title>
<style>body{{background:#0d1117;color:{TEXT};font-family:{FONT};max-width:1000px;margin:24px auto;padding:0 16px}}
img{{width:100%;margin:6px 0}} .note{{background:#5a1d1d;padding:8px 12px;border-radius:6px}}</style></head>
<body><p class="note">{demo_note}</p>
<img src="assets/banner.png" alt="banner"><h2>Degrees</h2><ul>{degrees}</ul>
<h2>Stats</h2><img src="assets/stats.svg" alt="stats">
<img src="assets/kelp.svg" alt="kelp"><img src="assets/school.svg" alt="school">
<p><small>Projects tables: see projects.md</small></p></body></html>
"""


def main():
    end = dt.date.today()
    start = end - dt.timedelta(days=DAYS - 1)
    demo = "--demo" in sys.argv[1:]
    out = ROOT / "preview" if demo else ROOT
    (out / "assets").mkdir(parents=True, exist_ok=True)

    if demo:
        github, gitlab, private, repo_count = demo_data(start)
        log("DEMO: made-up numbers")
    else:
        github, gh_private, gh_source, repo_count = github_contributions(start, end)
        gitlab, gl_private, gl_source = gitlab_contributions(start, end)
        private = merge(gh_private, gl_private)
        log(f"GitHub from {gh_source}; GitLab from {gl_source}")
    in_range = lambda d: {k: v for k, v in d.items() if start <= k <= end}
    by_source = dict(zip(SOURCES, (in_range(github), in_range(gitlab), in_range(private))))
    log(", ".join(f"{k}: {sum(v.values())}" for k, v in by_source.items()))

    totals = merge(*by_source.values())
    # Private only gets a card once it has data (it needs tokens); GitHub and
    # GitLab always show, even at 0, per Joanna.
    cards = [(f"{sum(v.values()):,}", f"{k} contributions", SOURCES[k])
             for k, v in by_source.items() if k != "Private" or sum(v.values())]
    cards.append((f"{sum(1 for v in totals.values() if v):,}", "Active days, 12 months", TEXT))
    if repo_count is not None:
        cards.append((f"{repo_count:,}", "GitHub repositories", MUTED))

    (out / "assets" / "stats.svg").write_text(stats_svg(cards))
    (out / "assets" / "kelp.svg").write_text(kelp_svg(by_source, start, end))
    (out / "assets" / "school.svg").write_text(school_svg(by_source, start, end))
    projects = (ROOT / "projects.md").read_text()
    (out / "README.md").write_text(readme(projects, end.isoformat()))
    for old in ("sea-serpent.svg",):  # replaced by school.svg
        (out / "assets" / old).unlink(missing_ok=True)
    if demo:
        (out / "assets" / "banner.png").write_bytes((ROOT / "assets" / "banner.png").read_bytes())
        (out / "preview.html").write_text(preview_html("DEMO: all numbers on this page are made up."))
    log(f"wrote README.md, assets/stats.svg, assets/kelp.svg, assets/school.svg in {out}")


if __name__ == "__main__":
    main()
