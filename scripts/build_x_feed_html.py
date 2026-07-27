#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUT_DIR = Path(r"D:/project/papers/neurovfm")
DATA = OUT_DIR / "x-feed-data.json"
TODAY = datetime.now().strftime("%Y-%m-%d")
HTML_OUT = OUT_DIR / f"x-ai-feed-{TODAY}.html"
CATEGORIES = ["⭐ AI 大佬动态", "🧠 LLM", "🤖 AI Agent", "🎨 Vibe Coding", "🌍 世界模型"]


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def fmt_num(v) -> str:
    try:
        n = float(v or 0)
    except (TypeError, ValueError):
        return "0"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(int(n))


def dt_label(value: str) -> str:
    try:
        dt = datetime.fromisoformat(value).astimezone(timezone(timedelta(hours=8)))
        return dt.strftime("%m/%d %H:%M")
    except Exception:
        return ""


def safe_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s)[:80]


def download_video(url: str, author: str, tid: str) -> str | None:
    """Download+compress. Strict per-video limits; reused from download_videos script.
    Returns the existing file path if already compressed, else attempts download."""
    if not url or not url.startswith("http") or not FFMPEG.exists():
        return None
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    out = VIDEO_DIR / f"{safe_name(author)}_{tid}.mp4"
    if out.exists() and out.stat().st_size > 0:
        return "videos/" + out.name
    raw = VIDEO_DIR / f"{safe_name(author)}_{tid}_raw.mp4"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=40) as r, raw.open("wb") as f:
            shutil.copyfileobj(r, f)
        subprocess.check_call([
            str(FFMPEG), "-y", "-i", str(raw), "-t", "10", "-vf", "scale='min(640,iw)':-2",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "32", "-an", str(out)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=ENV, timeout=50)
        raw.unlink(missing_ok=True)
        if out.exists() and out.stat().st_size > 0:
            return "videos/" + out.name
        return None
    except Exception:
        raw.unlink(missing_ok=True)
        out.unlink(missing_ok=True)
        return None


def media_html(item: dict) -> str:
    author = item.get("author") or {}
    screen = author.get("screenName") or "unknown"
    tid = item.get("id")
    tweet_url = item.get("url") or f"https://x.com/{screen}/status/{tid}"
    media = item.get("media") or []
    if not media:
        return ""
    first = media[0]
    if first.get("type") == "video":
        return f'''<div class="media"><a class="video-thumb" href="{esc(tweet_url)}" target="_blank" rel="noopener" style="display:inline-flex;max-width:360px;width:auto;padding:10px 12px;border-radius:6px;border:1px solid var(--line);background:#fafbfc;color:var(--teal);text-decoration:none;margin:8px 0">打开 X 查看视频 →</a></div>'''
    if first.get("type") == "photo" and first.get("url"):
        return f'''<div class="media"><a href="{esc(tweet_url)}" target="_blank" rel="noopener" class="tweet-photo" style="display:inline-block;max-width:360px;border-radius:8px;overflow:hidden;border:1px solid var(--line);text-decoration:none;margin:8px 0;width:auto"><img src="{esc(first.get('url'))}" alt="tweet image" loading="lazy" style="width:100%;display:block"></a><div style="margin:-6px 0 12px;font-size:12px;color:var(--muted);text-align:right"><a href="{esc(tweet_url)}" target="_blank" rel="noopener" style="color:var(--teal);text-decoration:none">@{esc(screen)} · 在 X 上查看原文 →</a></div></div>'''
    return ""


def card(item: dict) -> str:
    author = item.get("author") or {}
    metrics = item.get("metrics") or {}
    screen = author.get("screenName") or "unknown"
    verified = '<span class="verified">✓</span>' if author.get("verified") else ""
    avatar = author.get("profileImageUrl") or ""
    tweet_url = item.get("url") or f"https://x.com/{screen}/status/{item.get('id')}"
    return f'''<div class="tweet" id="tweet-{esc(item.get('id'))}">
  <div class="head">
    <img src="{esc(avatar)}" alt="" loading="lazy" style="width:28px;height:28px;border-radius:50%;border:1px solid var(--line);flex-shrink:0">
    <span class="name">{esc(author.get('name') or screen)}</span>
    <span class="uname">@{esc(screen)}</span>
    {verified}
    <span class="time">{esc(dt_label(item.get('createdAtISO')))}</span>
    <span class="badge heat" style="margin-left:8px">🔥 {item.get('score', 0):.0f}</span>
    <span class="badge age" style="margin-left:4px">⏱ {item.get('ageHours', 0):.1f}h</span>
  </div>
  <div class="text text-zh">{esc(item.get('textZh'))}</div>
  <details class="en-details"><summary>原文</summary><div class="text text-en">{esc(item.get('text'))}</div></details>
  {media_html(item)}
  <div class="stats">
    <span>💬 {fmt_num(metrics.get('replies'))}</span>
    <span>🔁 {fmt_num(metrics.get('retweets'))}</span>
    <span>❤️ {fmt_num(metrics.get('likes'))}</span>
    <span>🔖 {fmt_num(metrics.get('bookmarks'))}</span>
    <span>👁 {fmt_num(metrics.get('views'))}</span>
  </div>
  <div class="link-row"><a class="orig-link" href="{esc(tweet_url)}" target="_blank" rel="noopener">查看原文 →</a></div>
</div>'''


def main() -> int:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    items = payload["items"]

    sections = []
    counts = {}
    for cat in CATEGORIES:
        rows = [x for x in items if x.get("category") == cat]
        counts[cat] = len(rows)
        section_id = safe_name(cat)
        sections.append(f'''<section id="{section_id}"><h2>{esc(cat)}</h2><p>{len(rows)} 条 · 按综合分 score 降序 · 中文译版 + 原文折叠</p>{''.join(card(x) for x in rows)}</section>''')

    css = '''<style>:root{--ink:#1f2933;--muted:#5f6b76;--line:#d9e1e8;--paper:#fbfcfd;--panel:#fff;--teal:#0f766e;--teal-soft:#e5f4f1;--rose:#b4233a;--rose-soft:#fff0f2;--blue:#1f5f99;--shadow:0 12px 28px rgba(31,41,51,.08);--radius:8px}*{box-sizing:border-box}body{margin:0;padding:0;color:var(--ink);background:var(--paper);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei","PingFang SC",Arial,sans-serif;line-height:1.72}.page{width:min(1180px,calc(100% - 40px));margin:0 auto;padding:30px 0 60px}header{padding:24px 0 20px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#fff 0%,#f7fafb 100%)}.eyebrow{display:inline-flex;gap:8px;color:var(--teal);font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.08em}h1{margin:14px 0 12px;font-size:clamp(26px,3.6vw,40px);line-height:1.18}.subtitle{margin:0 0 14px;color:var(--muted);font-size:16px}.subtitle strong{color:var(--ink)}.meta{display:flex;flex-wrap:wrap;gap:8px;font-size:13px}.pill{display:inline-flex;border:1px solid var(--line);border-radius:999px;padding:3px 10px}.pill strong{font-weight:600}section{margin:28px 0}section h2{font-size:22px;margin-bottom:8px;display:flex;align-items:center;gap:8px}section>p{color:var(--muted);font-size:14px;margin:0 0 14px}.tweet{border:1px solid var(--line);border-radius:var(--radius);background:var(--panel);padding:14px 16px;margin:10px 0;box-shadow:0 4px 12px rgba(31,41,51,.06)}.tweet .head{display:flex;align-items:center;gap:8px;margin-bottom:8px;min-height:32px}.tweet .name{font-weight:600;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:240px;flex-shrink:1;min-width:0}.tweet .uname{color:var(--muted);font-size:13px;flex-shrink:0}.tweet .verified{color:var(--teal);font-size:12px;font-weight:700;flex-shrink:0}.tweet .time{color:var(--muted);font-size:12px;margin-left:auto;flex-shrink:0;white-space:nowrap}.tweet .text{white-space:pre-wrap;word-wrap:break-word;font-size:15px}.tweet .text-zh{font-size:15.5px}.tweet .text-en{font-size:13.5px;color:var(--muted);background:#fafbfc;padding:10px 12px;border-radius:6px;border:1px dashed var(--line);margin-top:6px}.tweet .stats{display:flex;gap:14px;margin-top:10px;font-size:12px;color:var(--muted);flex-wrap:wrap}.tweet .stats span{display:inline-flex;align-items:center;gap:4px}.tweet .media{margin-top:8px}.badge{display:inline-flex;align-items:center;gap:3px;font-size:11px;font-weight:600;padding:2px 8px;border-radius:999px;border:1px solid var(--line);background:#fafbfc;color:var(--muted)}.badge.heat{background:var(--rose-soft);color:var(--rose);border-color:#fbd5db}.badge.age{background:var(--teal-soft);color:var(--teal);border-color:#c8e8e2}details.en-details{margin-top:6px}details.en-details summary{cursor:pointer;font-size:13px;color:var(--muted);user-select:none;padding:2px 0}details.en-details[open] summary{color:var(--ink);font-weight:600}.link-row{margin-top:8px}.orig-link{color:var(--teal);text-decoration:none;font-size:13px}footer{margin-top:34px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:14px}</style>'''
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(items)
    html_doc = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>X AI 热门动态 · 24h · {TODAY}</title>{css}</head><body><div class="page"><header><span class="eyebrow">🐦 X (Twitter) · AI 热门动态 · 24h</span><h1>X 上 24 小时内的 AI 热门动态</h1><p class="subtitle">大模型 / Agent / Vibe Coding / 世界模型 — {TODAY} · <strong>按 热度×新鲜度 综合排序</strong></p><div class="meta"><span class="pill"><strong>来源</strong> X / Twitter (via twitter-cli)</span><span class="pill"><strong>窗口</strong> 最近 24h</span><span class="pill"><strong>采集</strong> {generated}</span><span class="pill"><strong>总数</strong> {total} 条去重精选</span><span class="pill"><strong>Fallback</strong> {'是' if payload.get('usedFallback') else '否'}</span></div></header>{''.join(sections)}<footer><h2>📐 算法说明</h2><p><strong>热度分</strong> = likes + 2·retweets + 0.5·replies + 0.001·views</p><p><strong>新鲜度</strong> = 1 / (1 + ageHours/8)</p><p><strong>综合分</strong> = 热度 × 新鲜度。每个搜索词单独抓取，去重后按分类与综合分排序。</p></footer></div></body></html>'''
    HTML_OUT.write_text(html_doc, encoding="utf-8")
    print(json.dumps({"html": str(HTML_OUT), "counts": counts, "usedFallback": payload.get("usedFallback", False)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
