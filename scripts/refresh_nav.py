#!/usr/bin/env python3
"""Refresh the historical-date navigation across ALL daily report HTML files.

Problem: each daily report page is generated on its day, so its sidebar only
contains dates up to that day. Older pages (pre-2026-07-17) have no sidebar at
all. Clicking into an old report strands the user -- they can't reach newer dates.

Fix: scan repo for all available dates, then for every report HTML:
  - NEW design (has <aside class="sidebar">): replace sidebar-nav + mobile-dates-nav
    link lists with the FULL date list, highlight the page's own date as current.
  - OLD design (no sidebar): inject a self-contained top date navbar (light theme
    to match the old design), with all dates + a "home/today" link.

Re-runnable: run after each daily publish to keep every page's nav in sync.
"""
import re
from pathlib import Path

REPO = Path(r"D:/project/papers/neurovfm/x-ai-feed-repo")

# 1. collect all available dates from reports/*.html
dates = []
for f in (REPO / "reports").glob("*.html"):
    m = re.match(r"(\d{4}-\d{2}-\d{2})\.html", f.name)
    if m:
        dates.append(m.group(1))
dates = sorted(set(dates), reverse=True)
latest = dates[0] if dates else ""
print(f"available dates ({len(dates)}): {dates[0]} .. {dates[-1] if dates else '?'}")


def make_desktop_links(current):
    links = []
    for d in dates:
        cls = "date-link current" if d == current else "date-link"
        badge = ' <span class="date-badge">今日</span>' if d == current else ""
        links.append(f'        <a href="/reports/{d}.html" class="{cls}">{d}{badge}</a>')
    return "\n".join(links)


def make_mobile_links(current):
    links = []
    for d in dates:
        cls = "date-link current" if d == current else "date-link"
        badge = ' <span class="date-badge">今日</span>' if d == current else ""
        links.append(f'<a href="/reports/{d}.html" class="{cls}">{d}{badge}</a>')
    return "\n".join(links)


NAVBAR_CSS = """<style id="xnav-style">
.xnav-bar{position:sticky;top:0;z-index:99999;background:rgba(255,255,255,.94);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid #d9e1e8;padding:8px 12px;display:flex;align-items:center;gap:6px;overflow-x:auto;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif}
.xnav-bar::-webkit-scrollbar{height:6px}
.xnav-bar::-webkit-scrollbar-thumb{background:#c4ccd4;border-radius:3px}
.xnav-label{color:#5f6b76;font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;white-space:nowrap;padding-right:8px;border-right:1px solid #d9e1e8;margin-right:4px}
.xnav-bar a{color:#1f2933;text-decoration:none;padding:6px 11px;border-radius:8px;font-size:13px;white-space:nowrap;border:1px solid transparent;transition:.15s}
.xnav-bar a:hover{background:#e5f4f1;color:#0f766e}
.xnav-bar a.xnav-current{background:#0f766e;color:#fff;border-color:#0f766e;font-weight:600}
.xnav-bar a.xnav-home{background:#e5f4f1;color:#0f766e;border:1px solid #b3d9d2;font-weight:600}
.xnav-date-badge{display:inline-block;margin-left:5px;font-size:10px;background:#fff;color:#0f766e;padding:1px 5px;border-radius:4px;font-weight:700;vertical-align:middle}
</style>"""


def make_navbar(current):
    links = []
    for d in dates:
        cls = "xnav-current" if d == current else ""
        badge = ' <span class="xnav-date-badge">今日</span>' if d == current else ""
        links.append(f'  <a href="/reports/{d}.html" class="{cls}">{d}{badge}</a>')
    return "\n".join([
        NAVBAR_CSS,
        '<nav class="xnav-bar" aria-label="历史日报导航">',
        '  <span class="xnav-label">历史日报</span>',
        '  <a href="/" class="xnav-home">🏠 今日</a>',
        *links,
        '</nav>',
    ])


def current_for(fn):
    m = re.search(r"(2026-07-\d{2})", fn)
    if m:
        return m.group(1)
    m = re.search(r"(202607\d{2})", fn)
    if m:
        s = m.group(1)
        return s[:4] + "-" + s[4:6] + "-" + s[6:8]
    return latest


def process_new(h, current):
    new_sidebar = '<nav class="sidebar-nav">\n' + make_desktop_links(current) + '\n    </nav>'
    h2 = re.sub(r'<nav class="sidebar-nav">[\s\S]*?</nav>',
                lambda m: new_sidebar, h, count=1)
    new_mobile = '<nav class="mobile-dates-nav">\n      ' + make_mobile_links(current) + '\n    </nav>'
    h2 = re.sub(r'<nav class="mobile-dates-nav">[\s\S]*?</nav>',
                lambda m: new_mobile, h2, count=1)
    return h2


def process_old(h, current):
    # strip any previous injection (idempotent)
    h = re.sub(r'<style id="xnav-style">[\s\S]*?</style>\s*', '', h)
    h = re.sub(r'<nav class="xnav-bar"[\s\S]*?</nav>\s*', '', h)
    navbar = make_navbar(current)
    # inject right after <body...>
    def inj(m):
        return m.group(0) + "\n" + navbar
    h2 = re.sub(r'<body[^>]*>', inj, h, count=1)
    return h2


# gather target files: root *.html + reports/*.html (skip carousel/)
targets = []
for f in REPO.glob("*.html"):
    targets.append(f)
for f in (REPO / "reports").glob("*.html"):
    targets.append(f)

new_count = old_count = skip = 0
for p in targets:
    rel = p.relative_to(REPO).as_posix()
    h = p.read_text(encoding="utf-8")
    current = current_for(rel)
    is_new = '<aside class="sidebar"' in h
    if is_new:
        h2 = process_new(h, current)
        tag = "NEW"
    else:
        h2 = process_old(h, current)
        tag = "OLD"
    if h2 != h:
        p.write_text(h2, encoding="utf-8")
        if tag == "NEW":
            new_count += 1
        else:
            old_count += 1
        print(f"  [{tag}] {rel:38} current={current}  (updated)")
    else:
        skip += 1
        print(f"  [{tag}] {rel:38} current={current}  (no change)")

print(f"\nDone. updated NEW={new_count}, OLD={old_count}, skipped={skip}, total={len(targets)}")
