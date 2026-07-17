#!/usr/bin/env python3
"""
Build an immersive, cutting-edge X AI daily feed HTML from x-feed-data.json.
Uses: Three.js WebGL neural-network background, CSS scroll-driven animations,
View Transitions, glassmorphism, 3D tilt cards, CSS @property, oklch colors.
"""
import json, html, os, re, math
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA = Path(r"D:/project/papers/neurovfm/x-feed-data.json")
VIDEOS = Path(r"D:/project/papers/neurovfm/videos")
OUT = Path(r"D:/project/papers/neurovfm/x-ai-feed-2026-07-17.html")
TODAY = "2026-07-17"
BJ = timezone(timedelta(hours=8))

CATS = ["⭐ AI 大佬动态", "🧠 LLM", "🤖 AI Agent", "🎨 Vibe Coding", "🌍 世界模型"]
CAT_META = {
    "⭐ AI 大佬动态": ("leaders", "AI 领袖与资深从业者的发声", "amber"),
    "🧠 LLM": ("llm", "大模型发布、能力与评测", "cyan"),
    "🤖 AI Agent": ("agent", "Agent 框架、工具调用与自动化", "violet"),
    "🎨 Vibe Coding": ("vibe", "Vibe Coding 工具与实践", "rose"),
    "🌍 世界模型": ("world", "世界模型、机器人与具身智能", "emerald"),
}
CAT_COLOR = {
    "amber": "#f59e0b",
    "cyan": "#06b6d4",
    "violet": "#8b5cf6",
    "rose": "#ec4899",
    "emerald": "#10b981",
}
CAT_OKLCH = {
    "amber": "oklch(72.5% 0.17 80)",
    "cyan": "oklch(72.5% 0.17 200)",
    "violet": "oklch(72.5% 0.17 300)",
    "rose": "oklch(72.5% 0.17 350)",
    "emerald": "oklch(72.5% 0.17 150)",
}

d = json.loads(DATA.read_text(encoding="utf-8"))
items = d["items"]


def fmt(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "0"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(int(n))


def fmt_time(iso):
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(BJ)
        return f"{dt.month}/{dt.day} {dt.hour:02d}:{dt.minute:02d}"
    except ValueError:
        return ""


def esc(s):
    return html.escape(str(s or ""))


def linkify(text):
    s = esc(text)
    s = re.sub(r"(https?://t\.co/\S+)", r'<a href="\1" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r"@([A-Za-z0-9_]+)", r'<a href="https://x.com/\1" target="_blank" rel="noopener">@\1</a>', s)
    return s


def media_block(it):
    media = it.get("media", [])
    if not media:
        return ""
    screen = it["author"].get("screenName", "unknown")
    tid = it["id"]
    first = media[0]
    mtype = first.get("type")
    xurl = f"https://x.com/{screen}/status/{tid}"
    if mtype == "video":
        fn = f"{screen}_{tid}.mp4"
        local = VIDEOS / fn
        if local.exists() and local.stat().st_size > 5000:
            return (
                f'<div class="media">\n'
                f'  <div class="video-frame" data-fallback="{xurl}">\n'
                f'    <video controls preload="metadata" playsinline onerror="handleVideoError(this)">\n'
                f'      <source src="videos/{fn}" type="video/mp4">\n'
                f'    </video>\n'
                f'    <div class="video-fallback" style="display:none">\n'
                f'      <p>⚠️ 当前环境无法直接播放此视频（可能是 HTTPS 证书过渡期或浏览器缺少 MP4 解码器）。</p>\n'
                f'      <a href="videos/{fn}" target="_blank" rel="noopener">⬇ 下载/播放 MP4</a>\n'
                f'      <a href="{xurl}" target="_blank" rel="noopener">▶ 在 X 上观看</a>\n'
                f'    </div>\n'
                f'  </div>\n'
                f'  <div class="media-meta"><a href="{xurl}" target="_blank" rel="noopener">@{esc(screen)} · 在 X 上查看原文 →</a></div>\n'
                f'</div>'
            )
        return f'<a href="{xurl}" target="_blank" rel="noopener" class="video-thumb">▶ 在 X 上观看视频</a>'
    if mtype == "photo":
        photo_url = first.get("url") or first.get("mediaUrl")
        return (
            f'<div class="media">\n'
            f'  <a href="{xurl}" target="_blank" rel="noopener" class="tweet-photo">\n'
            f'    <img src="{esc(photo_url)}" alt="tweet image" loading="lazy">\n'
            f'  </a>\n'
            f'  <div class="media-meta"><a href="{xurl}" target="_blank" rel="noopener">@{esc(screen)} · 在 X 上查看原文 →</a></div>\n'
            f'</div>'
        )
    return ""


def card(it, idx):
    a = it["author"]
    m = it.get("metrics") or {}
    screen = a.get("screenName", "unknown")
    name = a.get("name", screen)
    pimg = a.get("profileImageUrl", "")
    verified = a.get("verified")
    t = fmt_time(it.get("createdAtISO"))
    score = it.get("score", 0)
    age = it.get("ageHours", 0)
    heat = it.get("heat", 0)
    zh = it.get("textZh") or it["text"]
    en = it["text"]
    xurl = it.get("url") or f"https://x.com/{screen}/status/{it['id']}"
    cat_color = CAT_COLOR.get(CAT_META[it["category"]][2], "#fff")
    v_html = '<span class="verified" aria-label="verified">✓</span>' if verified else ""
    media = media_block(it)
    bm = m.get("bookmarks")
    bm_html = f'<span class="stat">🔖 {fmt(bm)}</span>' if bm is not None else ""
    return (
        f'<article class="tweet-card" id="tweet-{esc(it["id"])}" data-category="{esc(CAT_META[it["category"]][0])}" data-score="{score:.2f}" style="--card-glow:{cat_color}">\n'
        f'  <div class="card-border" aria-hidden="true"></div>\n'
        f'  <div class="card-inner">\n'
        f'    <div class="card-head">\n'
        f'      <div class="avatar-wrap">\n'
        f'        <img src="{esc(pimg)}" alt="" loading="lazy">\n'
        f'        <div class="avatar-glow" style="background:{cat_color}"></div>\n'
        f'      </div>\n'
        f'      <div class="meta-text">\n'
        f'        <div class="name-line">\n'
        f'          <span class="name">{esc(name)}</span>\n'
        f'          {v_html}\n'
        f'          <span class="uname">@{esc(screen)}</span>\n'
        f'        </div>\n'
        f'        <div class="time-line">\n'
        f'          <span class="time">{esc(t)}</span>\n'
        f'          <span class="age-badge">{age:.1f}h</span>\n'
        f'        </div>\n'
        f'      </div>\n'
        f'      <div class="score-badge" title="综合热度 = 热度 × 时效">\n'
        f'        <span class="score-val">{score:.0f}</span>\n'
        f'        <span class="score-label">SCORE</span>\n'
        f'      </div>\n'
        f'    </div>\n'
        f'    <div class="text-zh">{linkify(zh)}</div>\n'
        f'    {media}\n'
        f'    <details class="en-details">\n'
        f'      <summary>\n'
        f'        <span class="summary-text">原文 English</span>\n'
        f'        <span class="summary-icon" aria-hidden="true"></span>\n'
        f'      </summary>\n'
        f'      <div class="text-en">{linkify(en)}</div>\n'
        f'    </details>\n'
        f'    <div class="card-stats">\n'
        f'      <div class="stat-group">\n'
        f'        <span class="stat" title="热度 = likes + 2×retweets + 0.5×replies + 0.001×views">🔥 {fmt(heat)}</span>\n'
        f'        <span class="stat">💬 {fmt(m.get("replies"))}</span>\n'
        f'        <span class="stat">🔁 {fmt(m.get("retweets"))}</span>\n'
        f'        <span class="stat">❤️ {fmt(m.get("likes"))}</span>\n'
        f'        {bm_html}\n'
        f'        <span class="stat">👁 {fmt(m.get("views"))}</span>\n'
        f'      </div>\n'
        f'      <a class="orig-link" href="{xurl}" target="_blank" rel="noopener">Open on X</a>\n'
        f'    </div>\n'
        f'  </div>\n'
        f'</article>'
    )


# Stats
total = len(items)
counts = {c: sum(1 for x in items if x["category"] == c) for c in CATS}
videos = sum(1 for x in items for mm in x.get("media", []) if mm.get("type") == "video")
used_fb = d.get("usedFallback", False)
total_heat = sum(x.get("heat", 0) for x in items)
total_views = sum((x.get("metrics") or {}).get("views", 0) for x in items)

# Top contributors by aggregated heat
contrib = {}
for x in items:
    a = x["author"]
    key = (a.get("screenName", "unknown"), a.get("name", a.get("screenName", "unknown")), a.get("profileImageUrl", ""))
    contrib[key] = contrib.get(key, 0) + x.get("heat", 0)
top_contrib = sorted(contrib.items(), key=lambda kv: kv[1], reverse=True)[:5]

# Score distribution for chart
scores = [x.get("score", 0) for x in items]
max_score = max(scores) if scores else 1

# Render sections
sections = []
for c in CATS:
    sec_items = [x for x in items if x["category"] == c]
    sec_items.sort(key=lambda x: x.get("score", 0), reverse=True)
    sid, desc, color_key = CAT_META[c]
    color = CAT_COLOR[color_key]
    cards = "\n".join(card(x, i) for i, x in enumerate(sec_items))
    sections.append(
        f'  <section class="feed-section" id="{sid}" data-cat="{sid}" style="--section-color:{color}">\n'
        f'    <div class="section-header">\n'
        f'      <div class="section-title">\n'
        f'        <span class="section-icon" aria-hidden="true"></span>\n'
        f'        <h2>{c}</h2>\n'
        f'        <span class="section-count">{len(sec_items)}</span>\n'
        f'      </div>\n'
        f'      <p class="section-desc">{desc}</p>\n'
        f'    </div>\n'
        f'    <div class="cards-grid">\n'
        f'{cards}\n'
        f'    </div>\n'
        f'  </section>'
    )
sections_html = "\n\n".join(sections)

# Nav pills
pills = []
for c in CATS:
    sid, desc, color_key = CAT_META[c]
    color = CAT_COLOR[color_key]
    pills.append(
        f'<button class="nav-pill" data-filter="{sid}" style="--pill-color:{color}" aria-pressed="false">\n'
        f'  <span class="pill-dot" style="background:{color}"></span>\n'
        f'  {c}\n'
        f'  <span class="pill-count">{counts[c]}</span>\n'
        f'</button>'
    )
pills_html = "\n".join(pills)

# Dashboard category bars
cat_bars = []
max_count = max(counts.values()) if counts.values() else 1
for c in CATS:
    sid, desc, color_key = CAT_META[c]
    color = CAT_COLOR[color_key]
    pct = (counts[c] / max_count) * 100
    cat_bars.append(
        f'<div class="dist-bar">\n'
        f'  <div class="dist-label"><span class="dist-dot" style="background:{color}"></span>{c}</div>\n'
        f'  <div class="dist-track"><div class="dist-fill" style="--fill-pct:{pct:.1f}%;background:{color}"></div></div>\n'
        f'  <div class="dist-num">{counts[c]}</div>\n'
        f'</div>'
    )
cat_bars_html = "\n".join(cat_bars)

# Top contributors HTML
contrib_html = "\n".join(
    f'<div class="contrib-row">\n'
    f'  <img src="{esc(k[2])}" alt="" loading="lazy">\n'
    f'  <div class="contrib-name">\n'
    f'    <span class="c-name">{esc(k[1])}</span>\n'
    f'    <span class="c-uname">@{esc(k[0])}</span>\n'
    f'  </div>\n'
    f'  <div class="contrib-heat">{fmt(v)}</div>\n'
    f'</div>'
    for k, v in top_contrib
)

# Sidebar helpers
def get_available_dates():
    """Scan deployed reports/ directory for historical daily issues."""
    repo = Path(r"D:/project/papers/neurovfm/x-ai-feed-repo")
    reports_dir = repo / "reports"
    dates = []
    if reports_dir.exists():
        for f in reports_dir.glob("*.html"):
            m = re.match(r"(\d{4}-\d{2}-\d{2})\.html", f.name)
            if m:
                dates.append(m.group(1))
    return sorted(set(dates), reverse=True)


def render_sidebar(current_date):
    dates = get_available_dates()
    if current_date not in dates:
        dates.insert(0, current_date)
    dates = sorted(set(dates), reverse=True)
    desktop_links = []
    mobile_links = []
    for d in dates:
        cls = "date-link current" if d == current_date else "date-link"
        badge = ' <span class="date-badge">今日</span>' if d == current_date else ""
        desktop_links.append(f'        <a href="/reports/{d}.html" class="{cls}">{d}{badge}</a>')
        mobile_links.append(f'<a href="/reports/{d}.html" class="{cls}">{d}{badge}</a>')
    desktop = "\n".join([
        '  <aside class="sidebar" aria-label="历史日报">',
        '    <div class="sidebar-header">',
        '      <span class="sidebar-icon" aria-hidden="true">\u2630</span>',
        '      <span>历史日报</span>',
        '    </div>',
        '    <nav class="sidebar-nav">',
        *desktop_links,
        '    </nav>',
        '  </aside>',
    ])
    mobile = "\n".join([
        '  <div class="mobile-dates" aria-label="历史日报">',
        '    <span class="mobile-dates-label">历史日报</span>',
        '    <nav class="mobile-dates-nav">',
        *mobile_links,
        '    </nav>',
        '  </div>',
    ])
    return "\n" + desktop + "\n" + mobile


# Items JSON for JS
items_json = json.dumps(items, ensure_ascii=False, separators=(",", ":"))

src_note = "twitter search 404 → 降级 feed + user-posts" if used_fb else "twitter search"
gen_bj = datetime.now(BJ).strftime("%Y-%m-%d %H:%M 北京时间")

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="X AI 24h 热门动态 - AI HORIZON">
<meta name="theme-color" content="#0a0a0f">
<title>AI HORIZON · X AI 24h 热门动态 · {TODAY}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+SC:wght@400;500;700;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js" defer></script>
<style>
/* === Design tokens === */
@property --gradient-angle {{
  syntax: "<angle>";
  initial-value: 0deg;
  inherits: false;
}}
@property --glow-x {{
  syntax: "<percentage>";
  initial-value: 0%;
  inherits: false;
}}
:root {{
  --bg: #050508;
  --bg-2: #0a0a10;
  --panel: rgba(15, 15, 22, 0.72);
  --panel-strong: rgba(20, 20, 30, 0.88);
  --text: #f5f7ff;
  --text-dim: #a0a8c0;
  --text-muted: #6b7290;
  --line: rgba(255,255,255,0.08);
  --line-strong: rgba(255,255,255,0.16);
  --radius: 18px;
  --radius-sm: 10px;
  --shadow: 0 24px 80px rgba(0,0,0,0.45);
  --shadow-sm: 0 8px 30px rgba(0,0,0,0.25);
  --amber: #f59e0b;
  --cyan: #06b6d4;
  --violet: #8b5cf6;
  --rose: #ec4899;
  --emerald: #10b981;
  --font: "Inter", "Noto Sans SC", -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
  --mono: "SF Mono", ui-monospace, "Cascadia Code", monospace;
}}
*, *::before, *::after {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  padding: 0;
  font-family: var(--font);
  color: var(--text);
  background: var(--bg);
  line-height: 1.65;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
}}

/* === Scrollbar === */
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.18); border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.28); }}

/* === WebGL canvas === */
#neural-canvas {{
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
  opacity: 0.8;
}}

/* === Hero === */
.hero {{
  position: relative;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 6vw;
  z-index: 1;
  overflow: hidden;
}}
.hero::before {{
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 30%, rgba(139,92,246,0.18) 0%, transparent 40%),
    radial-gradient(circle at 80% 70%, rgba(6,182,212,0.14) 0%, transparent 45%),
    radial-gradient(circle at 50% 50%, rgba(236,72,153,0.08) 0%, transparent 50%);
  z-index: -1;
  animation: nebula 18s ease-in-out infinite alternate;
}}
@keyframes nebula {{
  from {{ filter: hue-rotate(0deg) scale(1); }}
  to {{ filter: hue-rotate(25deg) scale(1.08); }}
}}
.hero-content {{
  text-align: center;
  max-width: 900px;
  perspective: 1000px;
}}
.hero-eyebrow {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  border: 1px solid var(--line);
  color: var(--text-dim);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 28px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}}
.hero-eyebrow .pulse {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--emerald);
  box-shadow: 0 0 12px var(--emerald);
  animation: pulse 2s ease-in-out infinite;
}}
@keyframes pulse {{
  0%, 100% {{ opacity: 0.7; transform: scale(1); }}
  50% {{ opacity: 1; transform: scale(1.25); }}
}}
.hero-title {{
  font-size: clamp(48px, 10vw, 112px);
  font-weight: 900;
  line-height: 0.95;
  letter-spacing: -0.04em;
  margin: 0 0 22px;
  background: linear-gradient(var(--gradient-angle), #fff 0%, #a5b4fc 35%, #67e8f9 65%, #c084fc 100%);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-rotate 8s linear infinite;
  filter: drop-shadow(0 0 40px rgba(139,92,246,0.25));
}}
@keyframes gradient-rotate {{
  from {{ --gradient-angle: 0deg; }}
  to {{ --gradient-angle: 360deg; }}
}}
.hero-subtitle {{
  font-size: clamp(18px, 2.6vw, 28px);
  color: var(--text-dim);
  font-weight: 400;
  margin: 0 0 40px;
}}
.hero-subtitle strong {{
  color: var(--text);
  font-weight: 700;
}}
.hero-date {{
  display: inline-block;
  font-family: var(--mono);
  font-size: 16px;
  color: var(--text-muted);
  padding: 12px 24px;
  border-radius: var(--radius-sm);
  background: var(--panel);
  border: 1px solid var(--line);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}}
.scroll-hint {{
  position: absolute;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  animation: float 3s ease-in-out infinite;
}}
@keyframes float {{
  0%, 100% {{ transform: translateX(-50%) translateY(0); }}
  50% {{ transform: translateX(-50%) translateY(-8px); }}
}}
.scroll-hint::after {{
  content: "↓";
  font-size: 18px;
  opacity: 0.7;
}}

/* === Navigation === */
.top-nav {{
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 4vw;
  background: rgba(5,5,8,0.78);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}}
.nav-brand {{
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: -0.02em;
  color: var(--text);
  text-decoration: none;
}}
.nav-brand .brand-dot {{
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--cyan), var(--violet));
  box-shadow: 0 0 18px rgba(6,182,212,0.5);
}}
.nav-pills {{
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 4px;
  scrollbar-width: none;
}}
.nav-pills::-webkit-scrollbar {{ display: none; }}
.nav-pill {{
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--line);
  color: var(--text-dim);
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  white-space: nowrap;
}}
.nav-pill:hover {{
  background: rgba(255,255,255,0.1);
  color: var(--text);
  border-color: var(--pill-color);
  box-shadow: 0 0 20px color-mix(in srgb, var(--pill-color) 25%, transparent);
}}
.nav-pill[aria-pressed="true"] {{
  background: color-mix(in srgb, var(--pill-color) 18%, transparent);
  border-color: var(--pill-color);
  color: var(--text);
  box-shadow: 0 0 24px color-mix(in srgb, var(--pill-color) 30%, transparent);
}}
.pill-dot {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 0 8px currentColor;
}}
.pill-count {{
  display: inline-grid;
  place-items: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(255,255,255,0.1);
  font-size: 11px;
  font-weight: 700;
}}
.search-wrap {{
  position: relative;
  width: 220px;
  flex-shrink: 0;
}}
.search-wrap input {{
  width: 100%;
  padding: 9px 14px 9px 36px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: rgba(255,255,255,0.04);
  color: var(--text);
  font-family: inherit;
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
}}
.search-wrap input:focus {{
  border-color: var(--cyan);
  background: rgba(255,255,255,0.07);
  box-shadow: 0 0 20px rgba(6,182,212,0.15);
}}
.search-wrap::before {{
  content: "🔍";
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 13px;
  opacity: 0.7;
}}

/* === Main layout === */
.page-layout {{
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 4vw 8vw;
}}
.main {{
  min-width: 0;
}}

/* === Sidebar === */
.sidebar {{
  position: sticky;
  top: 84px;
  height: calc(100vh - 104px);
  overflow-y: auto;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 18px;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow: var(--shadow-sm);
}}
.sidebar-header {{
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line);
}}
.sidebar-icon {{
  font-size: 14px;
}}
.sidebar-nav {{
  display: flex;
  flex-direction: column;
  gap: 6px;
}}
.date-link {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  color: var(--text-dim);
  text-decoration: none;
  font-size: 14px;
  font-family: var(--mono);
  transition: all 0.2s;
  border: 1px solid transparent;
}}
.date-link:hover {{
  background: rgba(255,255,255,0.06);
  color: var(--text);
  border-color: var(--line);
}}
.date-link.current {{
  background: rgba(6,182,212,0.12);
  color: var(--cyan);
  border-color: rgba(6,182,212,0.35);
  font-weight: 700;
}}
.date-badge {{
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--cyan);
  color: #000;
  font-weight: 800;
  font-family: var(--font);
}}

/* === Mobile dates === */
.mobile-dates {{
  display: none;
  margin-bottom: 20px;
}}
.mobile-dates-label {{
  display: block;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 10px;
}}
.mobile-dates-nav {{
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 4px 0;
  scrollbar-width: none;
}}
.mobile-dates-nav::-webkit-scrollbar {{ display: none; }}
.mobile-dates-nav .date-link {{
  flex: 0 0 auto;
  white-space: nowrap;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--line);
}}

/* === Dashboard === */
.dashboard {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 64px;
}}
.panel {{
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 24px;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow: var(--shadow-sm);
}}
.panel-title {{
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 0 0 18px;
}}
.kpi-grid {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}}
.kpi {{
  padding: 16px;
  border-radius: var(--radius-sm);
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--line);
}}
.kpi-value {{
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--text);
  line-height: 1.1;
}}
.kpi-label {{
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 6px;
}}
.dist-bar {{
  display: grid;
  grid-template-columns: auto 1fr 28px;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}}
.dist-label {{
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-dim);
  min-width: 120px;
}}
.dist-dot {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
}}
.dist-track {{
  height: 6px;
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  overflow: hidden;
}}
.dist-fill {{
  height: 100%;
  width: 0;
  border-radius: 999px;
  box-shadow: 0 0 12px currentColor;
  animation: fill-bar 1.2s ease-out 0.3s forwards;
}}
@keyframes fill-bar {{
  to {{ width: var(--fill-pct); }}
}}
.dist-num {{
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  text-align: right;
}}
.contrib-row {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--line);
}}
.contrib-row:last-child {{ border-bottom: none; }}
.contrib-row img {{
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.1);
}}
.contrib-name {{
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}}
.c-name {{
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}}
.c-uname {{
  font-size: 12px;
  color: var(--text-muted);
}}
.contrib-heat {{
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--amber);
}}

/* === Feed sections === */
.feed-section {{
  margin-bottom: 80px;
  animation: fade-in-up 0.8s ease-out both;
  animation-timeline: view();
  animation-range: entry 0% cover 20%;
}}
@keyframes fade-in-up {{
  from {{ opacity: 0; transform: translateY(40px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
.section-header {{
  margin-bottom: 28px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--line-strong);
}}
.section-title {{
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}}
.section-icon {{
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--section-color);
  box-shadow: 0 0 20px var(--section-color);
}}
.section-header h2 {{
  font-size: clamp(24px, 3.4vw, 36px);
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 0;
  color: var(--text);
}}
.section-count {{
  display: inline-grid;
  place-items: center;
  min-width: 32px;
  height: 32px;
  padding: 0 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--section-color) 18%, transparent);
  border: 1px solid color-mix(in srgb, var(--section-color) 40%, transparent);
  color: var(--section-color);
  font-size: 14px;
  font-weight: 800;
}}
.section-desc {{
  margin: 0;
  color: var(--text-muted);
  font-size: 15px;
}}
.cards-grid {{
  column-count: 2;
  column-gap: 24px;
}}
.tweet-card {{
  width: 100%;
  break-inside: avoid;
  margin-bottom: 24px;
  transform: translateZ(0); /* fix column clipping on some browsers */
}}
@media (max-width: 820px) {{
  .cards-grid {{ column-count: 1; }}
  .tweet-card {{ width: 100%; }}
}}

/* === Tweet cards === */
.tweet-card {{
  position: relative;
  border-radius: var(--radius);
  transform-style: preserve-3d;
  transition: transform 0.4s cubic-bezier(0.2, 0, 0.2, 1), opacity 0.3s, box-shadow 0.3s;
  animation: card-enter 0.7s ease-out both;
  animation-timeline: view();
  animation-range: entry 0% cover 15%;
}}
@keyframes card-enter {{
  from {{ opacity: 0; transform: translateY(30px) scale(0.96); }}
  to {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
.tweet-card.hidden {{
  display: none;
}}
.tweet-card.dim {{
  opacity: 0.25;
  filter: grayscale(0.6);
}}
.card-border {{
  position: absolute;
  inset: 0;
  border-radius: var(--radius);
  padding: 1px;
  background: linear-gradient(var(--gradient-angle), rgba(255,255,255,0.25), var(--card-glow), rgba(255,255,255,0.15), var(--card-glow));
  background-size: 300% 300%;
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  animation: gradient-rotate 6s linear infinite;
  opacity: 0.6;
  transition: opacity 0.3s;
  pointer-events: none;
}}
.tweet-card:hover .card-border {{
  opacity: 1;
}}
.card-inner {{
  position: relative;
  border-radius: var(--radius);
  background: var(--panel);
  border: 1px solid var(--line);
  padding: 22px;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  overflow: hidden;
}}
.card-inner::before {{
  content: "";
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at var(--glow-x, 0%) 50%, color-mix(in srgb, var(--card-glow) 18%, transparent), transparent 50%);
  opacity: 0;
  transition: opacity 0.4s;
  pointer-events: none;
  animation: glow-move 5s ease-in-out infinite;
}}
.tweet-card:hover .card-inner::before {{
  opacity: 1;
}}
@keyframes glow-move {{
  0%, 100% {{ --glow-x: 0%; }}
  50% {{ --glow-x: 100%; }}
}}
.card-head {{
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 16px;
}}
.avatar-wrap {{
  position: relative;
  flex-shrink: 0;
}}
.avatar-wrap img {{
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.12);
  object-fit: cover;
  position: relative;
  z-index: 1;
}}
.avatar-glow {{
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  filter: blur(10px);
  opacity: 0.5;
  z-index: 0;
  transition: opacity 0.3s;
}}
.tweet-card:hover .avatar-glow {{
  opacity: 0.9;
}}
.meta-text {{
  flex: 1;
  min-width: 0;
}}
.name-line {{
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}}
.name {{
  font-weight: 700;
  color: var(--text);
  font-size: 15px;
}}
.uname {{
  color: var(--text-muted);
  font-size: 13px;
}}
.verified {{
  color: var(--cyan);
  font-size: 12px;
  font-weight: 700;
}}
.time-line {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted);
}}
.age-badge {{
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  border: 1px solid var(--line);
  font-size: 11px;
  font-weight: 600;
}}
.score-badge {{
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  margin-left: auto;
  padding-left: 12px;
}}
.score-val {{
  font-family: var(--mono);
  font-size: 20px;
  font-weight: 800;
  color: var(--amber);
  line-height: 1;
}}
.score-label {{
  font-size: 9px;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  text-transform: uppercase;
}}
.text-zh {{
  font-size: 15px;
  line-height: 1.75;
  color: var(--text);
  margin-bottom: 14px;
  white-space: pre-wrap;
}}
.text-zh a, .text-en a {{
  color: var(--cyan);
  text-decoration: none;
  border-bottom: 1px solid rgba(6,182,212,0.3);
  transition: border-color 0.2s;
}}
.text-zh a:hover, .text-en a:hover {{
  border-color: var(--cyan);
}}
.media {{
  margin: 14px 0;
}}
.video-frame {{
  display: inline-block;
  width: 100%;
  max-width: 420px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--line);
  background: #000;
  position: relative;
}}
.video-frame video {{
  width: 100%;
  max-height: 420px;
  display: block;
  object-fit: contain;
  background: #000;
}}
.video-fallback {{
  padding: 18px;
  text-align: center;
  background: rgba(0,0,0,0.55);
  border-radius: var(--radius-sm);
}}
.video-fallback p {{
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--text-dim);
  line-height: 1.5;
}}
.video-fallback a {{
  display: inline-block;
  margin: 4px;
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  background: rgba(255,255,255,0.08);
  border: 1px solid var(--line-strong);
  color: var(--text);
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s;
}}
.video-fallback a:hover {{
  background: rgba(255,255,255,0.15);
  border-color: var(--cyan);
}}
.video-thumb {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--line);
  background: rgba(255,255,255,0.05);
  color: var(--text);
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s;
}}
.video-thumb:hover {{
  background: rgba(255,255,255,0.1);
  border-color: var(--cyan);
}}
.tweet-photo {{
  display: block;
  max-width: 420px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--line);
}}
.tweet-photo img {{
  width: 100%;
  display: block;
}}
.media-meta {{
  margin-top: 8px;
  font-size: 12px;
  text-align: right;
}}
.media-meta a {{
  color: var(--text-muted);
  text-decoration: none;
}}
.media-meta a:hover {{
  color: var(--cyan);
}}
.en-details {{
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  margin: 14px 0;
  overflow: hidden;
}}
.en-details summary {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(255,255,255,0.03);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-dim);
  list-style: none;
}}
.en-details summary::-webkit-details-marker {{ display: none; }}
.en-details .summary-icon {{
  width: 8px;
  height: 8px;
  border-right: 2px solid var(--text-muted);
  border-bottom: 2px solid var(--text-muted);
  transform: rotate(45deg);
  transition: transform 0.2s;
}}
.en-details[open] .summary-icon {{
  transform: rotate(-135deg);
}}
.text-en {{
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-dim);
  background: rgba(0,0,0,0.15);
  border-top: 1px solid var(--line);
  white-space: pre-wrap;
}}
.card-stats {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
  flex-wrap: wrap;
}}
.stat-group {{
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}}
.stat {{
  font-size: 13px;
  color: var(--text-muted);
  font-family: var(--mono);
}}
.orig-link {{
  padding: 7px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--line-strong);
  color: var(--text);
  text-decoration: none;
  font-size: 12px;
  font-weight: 700;
  transition: all 0.2s;
}}
.orig-link:hover {{
  background: var(--text);
  color: var(--bg);
}}

/* === Footer === */
.footer {{
  text-align: center;
  padding: 60px 4vw;
  color: var(--text-muted);
  font-size: 13px;
  border-top: 1px solid var(--line);
  background: rgba(0,0,0,0.2);
}}
.footer a {{
  color: var(--cyan);
  text-decoration: none;
}}

/* === Utility === */
.back-to-top {{
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid var(--line-strong);
  background: var(--panel-strong);
  color: var(--text);
  display: grid;
  place-items: center;
  cursor: pointer;
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.3s ease;
  z-index: 90;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}}
.back-to-top.visible {{
  opacity: 1;
  transform: translateY(0);
}}
.back-to-top:hover {{
  border-color: var(--cyan);
  box-shadow: 0 0 24px rgba(6,182,212,0.25);
}}

/* === Mobile === */
@media (max-width: 640px) {{
  .top-nav {{
    flex-wrap: wrap;
    padding: 10px 3vw;
  }}
  .search-wrap {{
    width: 100%;
    order: 3;
  }}
  .nav-pills {{
    order: 2;
    width: 100%;
  }}
  .hero-title {{ font-size: 56px; }}
  .hero-subtitle {{ font-size: 18px; }}
  .kpi-grid {{ grid-template-columns: 1fr; }}
  .panel {{ padding: 18px; }}
  .card-head {{ flex-wrap: wrap; }}
  .score-badge {{ width: 100%; flex-direction: row; justify-content: space-between; padding-top: 12px; margin-left: 0; }}
  .page-layout {{ grid-template-columns: 1fr; padding: 0 3vw 8vw; gap: 16px; }}
  .sidebar {{ display: none; }}
  .mobile-dates {{ display: block; }}
}}

/* === Reduced motion === */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }}
}}
</style>
</head>
<body>
<canvas id="neural-canvas"></canvas>

<header class="hero" id="top">
  <div class="hero-content">
    <div class="hero-eyebrow"><span class="pulse"></span> X AI 24h 热门动态</div>
    <h1 class="hero-title">AI HORIZON</h1>
    <p class="hero-subtitle">过去 <strong>24 小时</strong>，X 上最热门的 AI 信号。<br>中文精选 + 原文对照 + 热度排序。</p>
    <div class="hero-date">📅 {TODAY} · {total} 条 · {videos} 个视频 · 数据来源: {src_note}</div>
  </div>
  <div class="scroll-hint">Scroll</div>
</header>

<nav class="top-nav">
  <a class="nav-brand" href="#top">
    <span class="brand-dot"></span>
    AI HORIZON
  </a>
  <div class="nav-pills">
    <button class="nav-pill" data-filter="all" style="--pill-color:#fff" aria-pressed="true">
      <span class="pill-dot" style="background:#fff"></span>
      全部
      <span class="pill-count">{total}</span>
    </button>
{pills_html}
  </div>
  <div class="search-wrap">
    <input type="search" id="search" placeholder="搜索推文、作者、关键词…" aria-label="搜索">
  </div>
</nav>

<div class="page-layout">
{render_sidebar(TODAY)}
  <main class="main">
  <section class="dashboard" aria-label="数据概览">
    <div class="panel">
      <div class="panel-title">今日概览</div>
      <div class="kpi-grid">
        <div class="kpi"><div class="kpi-value">{total}</div><div class="kpi-label">精选推文</div></div>
        <div class="kpi"><div class="kpi-value">{videos}</div><div class="kpi-label">内嵌视频</div></div>
        <div class="kpi"><div class="kpi-value">{fmt(total_heat)}</div><div class="kpi-label">总热度</div></div>
        <div class="kpi"><div class="kpi-value">{fmt(total_views)}</div><div class="kpi-label">总曝光</div></div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-title">分类分布</div>
{cat_bars_html}
    </div>
    <div class="panel">
      <div class="panel-title">热门发声账号</div>
{contrib_html}
    </div>
  </section>

{sections_html}
  </main>
</div>

<footer class="footer">
  <p>AI HORIZON · X AI 日报 · {TODAY} · 生成于 {gen_bj}</p>
  <p>数据来自公开 X 推文，按热度 × 时效排序。部署于 <a href="https://pages.github.com" target="_blank" rel="noopener">GitHub Pages</a>。</p>
</footer>

<button class="back-to-top" id="backToTop" aria-label="回到顶部">↑</button>

<script>
// === Embedded data ===
const FEED_DATA = {items_json};

// === WebGL neural network background ===
(function() {{
  const canvas = document.getElementById('neural-canvas');
  if (!window.THREE || !canvas) return;
  const renderer = new THREE.WebGLRenderer({{ canvas, alpha: true, antialias: true, powerPreference: 'low-power' }});
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 35;

  const count = window.matchMedia('(pointer: coarse)').matches ? 60 : 120;
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const palette = [new THREE.Color('#8b5cf6'), new THREE.Color('#06b6d4'), new THREE.Color('#ec4899'), new THREE.Color('#f59e0b')];

  for (let i = 0; i < count; i++) {{
    positions[i*3] = (Math.random() - 0.5) * 70;
    positions[i*3+1] = (Math.random() - 0.5) * 50;
    positions[i*3+2] = (Math.random() - 0.5) * 30;
    const c = palette[Math.floor(Math.random() * palette.length)];
    colors[i*3] = c.r; colors[i*3+1] = c.g; colors[i*3+2] = c.b;
  }}

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({{
    size: 0.35,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending
  }});
  const points = new THREE.Points(geometry, material);
  scene.add(points);

  const lineGeo = new THREE.BufferGeometry();
  const lineMat = new THREE.LineBasicMaterial({{ color: 0x4f46e5, transparent: true, opacity: 0.12, blending: THREE.AdditiveBlending }});
  const lines = new THREE.LineSegments(lineGeo, lineMat);
  scene.add(lines);

  let mouseX = 0, mouseY = 0;
  document.addEventListener('mousemove', (e) => {{
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  }}, {{ passive: true }});

  let frame = 0;
  function animate() {{
    frame = requestAnimationFrame(animate);
    const t = performance.now() * 0.0001;
    camera.position.x += (mouseX * 6 - camera.position.x) * 0.02;
    camera.position.y += (-mouseY * 4 - camera.position.y) * 0.02;
    camera.lookAt(0, 0, 0);

    const pos = geometry.attributes.position.array;
    for (let i = 0; i < count; i++) {{
      const idx = i * 3;
      pos[idx+1] += Math.sin(t + i) * 0.015;
      pos[idx] += Math.cos(t * 0.7 + i * 0.1) * 0.01;
    }}
    geometry.attributes.position.needsUpdate = true;
    points.rotation.y = t * 0.15;

    const linePos = [];
    const threshold = 9;
    for (let i = 0; i < count; i++) {{
      for (let j = i + 1; j < count; j++) {{
        const dx = pos[i*3] - pos[j*3];
        const dy = pos[i*3+1] - pos[j*3+1];
        const dz = pos[i*3+2] - pos[j*3+2];
        const d2 = dx*dx + dy*dy + dz*dz;
        if (d2 < threshold * threshold) {{
          linePos.push(pos[i*3], pos[i*3+1], pos[i*3+2], pos[j*3], pos[j*3+1], pos[j*3+2]);
        }}
      }}
    }}
    lineGeo.setAttribute('position', new THREE.Float32BufferAttribute(linePos, 3));
    lines.rotation.y = t * 0.15;
    renderer.render(scene, camera);
  }}
  animate();

  window.addEventListener('resize', () => {{
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }});

  document.addEventListener('visibilitychange', () => {{
    if (document.hidden) cancelAnimationFrame(frame);
    else animate();
  }});
}})();

// === Video error fallback ===
function handleVideoError(video) {{
  const frame = video.closest('.video-frame');
  if (!frame) return;
  video.style.display = 'none';
  const fallback = frame.querySelector('.video-fallback');
  if (fallback) fallback.style.display = 'block';
}}

// === 3D tilt cards ===
document.querySelectorAll('.tweet-card').forEach(card => {{
  card.addEventListener('mousemove', (e) => {{
    const r = card.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5;
    const y = (e.clientY - r.top) / r.height - 0.5;
    card.style.transform = `rotateY(${{x * 12}}deg) rotateX(${{-y * 12}}deg) translateZ(20px)`;
  }});
  card.addEventListener('mouseleave', () => {{
    card.style.transform = 'rotateY(0) rotateX(0) translateZ(0)';
  }});
}});

// === Category filtering ===
const filterButtons = document.querySelectorAll('.nav-pill');
const sections = document.querySelectorAll('.feed-section');
const cards = document.querySelectorAll('.tweet-card');
let activeFilter = 'all';

function setFilter(key) {{
  activeFilter = key;
  filterButtons.forEach(btn => {{
    const pressed = btn.dataset.filter === key;
    btn.setAttribute('aria-pressed', String(pressed));
  }});

  const update = () => {{
    sections.forEach(sec => {{
      sec.classList.toggle('hidden', key !== 'all' && sec.dataset.cat !== key);
    }});
    cards.forEach(card => {{
      const match = key === 'all' || card.dataset.category === key;
      card.classList.toggle('hidden', !match);
    }});
  }};

  if (document.startViewTransition) {{
    document.startViewTransition(update);
  }} else {{
    update();
  }}
}}

filterButtons.forEach(btn => {{
  btn.addEventListener('click', () => setFilter(btn.dataset.filter));
}});

// === Search ===
const searchInput = document.getElementById('search');
searchInput.addEventListener('input', () => {{
  const q = searchInput.value.trim().toLowerCase();
  if (!q) {{
    setFilter(activeFilter);
    return;
  }}
  cards.forEach(card => {{
    const text = card.innerText.toLowerCase();
    card.classList.toggle('hidden', !text.includes(q));
  }});
  sections.forEach(sec => {{
    const visible = sec.querySelectorAll('.tweet-card:not(.hidden)').length > 0;
    sec.classList.toggle('hidden', !visible);
  }});
}});

// === Back to top ===
const backTop = document.getElementById('backToTop');
window.addEventListener('scroll', () => {{
  backTop.classList.toggle('visible', window.scrollY > 600);
}}, {{ passive: true }});
backTop.addEventListener('click', () => window.scrollTo({{ top: 0, behavior: 'smooth' }}));
</script>
</body>
</html>
'''

OUT.write_text(HTML, encoding="utf-8")
print(f"Wrote {{OUT}} ({{OUT.stat().st_size}} bytes)")
