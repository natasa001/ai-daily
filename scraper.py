# -*- coding: utf-8 -*-
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

SOURCES = {
    "hackernews": {
        "url": "https://hnrss.org/frontpage",
        "type": "rss"
    },
    "techcrunch_ai": {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "type": "rss"
    },
    "mit_ai": {
        "url": "https://www.technologyreview.com/feed/",
        "type": "rss"
    },
}

CUSTOM_SOURCES = [
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/ai/feed/",
        "type": "rss"
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "type": "rss"
    },
]


def fetch_rss(source_name, url):
    items = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:8]:
            item = {
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "source": source_name,
                "published": entry.get("published", ""),
                "summary": strip_html(entry.get("summary", entry.get("description", "")))[:200],
                "id": hashlib.md5(entry.get("link", "").encode()).hexdigest()[:12],
            }
            items.append(item)
    except Exception as e:
        print(f"[ERROR] Failed to fetch {source_name}: {e}", flush=True)
    return items


def fetch_html(source):
    items = []
    try:
        resp = requests.get(source["url"], timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AI-Daily/1.0)"
        })
        soup = BeautifulSoup(resp.text, "html.parser")
        articles = soup.select("article h2 a, .post-title a, h3 a")[:6]
        for a in articles:
            href = a.get("href", "")
            if not href.startswith("http"):
                continue
            title = a.get_text(strip=True)
            items.append({
                "title": title,
                "url": href,
                "source": source["name"],
                "published": "",
                "summary": "",
                "id": hashlib.md5(href.encode()).hexdigest()[:12],
            })
    except Exception as e:
        print(f"[ERROR] Failed to fetch {source['name']}: {e}", flush=True)
    return items


def strip_html(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def scrape_all():
    all_items = []
    for name, source in SOURCES.items():
        if source["type"] == "rss":
            all_items.extend(fetch_rss(name, source["url"]))

    for source in CUSTOM_SOURCES:
        if source["type"] == "rss":
            all_items.extend(fetch_rss(source["name"], source["url"]))
        elif source["type"] == "html":
            all_items.extend(fetch_html(source))

    seen = set()
    unique = []
    for item in all_items:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique.append(item)

    unique.sort(key=lambda x: x["published"], reverse=True)
    return unique


def format_digest(items, lang="zh"):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    lines = []

    if lang == "zh":
        lines.append(f"🤖 AI Daily | {today}\n")
        lines.append(f"📰 今日共抓取 {len(items)} 条资讯\n")
        lines.append("─" * 24)
        lines.append("")
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item['title']}")
            lines.append(f"   🔗 {item['url']}")
            if item["summary"]:
                lines.append(f"   📝 {item['summary'][:80]}...")
            lines.append("")
        lines.append("─" * 24)
        lines.append("付费订阅 ¥10/月：英文版 / 关键词监控 / 历史搜索")
        lines.append("微信转账后联系 @your_telegram 开通")
    else:
        lines.append(f"🤖 AI Daily | {today}\n")
        lines.append(f"📰 {len(items)} items today\n")
        lines.append("─" * 24)
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item['title']}")
            lines.append(f"   🔗 {item['url']}")
            lines.append("")

    return "\n".join(lines)


def generate_html(items):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    source_colors = {
        "hackernews": "#ff6600",
        "techcrunch_ai": "#0a9e01",
        "mit_ai": "#8b0000",
        "VentureBeat AI": "#ff4a00",
        "The Verge AI": "#1b9ce2",
    }
    source_labels = {
        "hackernews": "Hacker News",
        "techcrunch_ai": "TechCrunch AI",
        "mit_ai": "MIT Tech Review",
        "VentureBeat AI": "VentureBeat AI",
        "The Verge AI": "The Verge AI",
    }

    from collections import OrderedDict
    grouped = OrderedDict()
    for item in items:
        s = item["source"]
        if s not in grouped:
            grouped[s] = []
        grouped[s].append(item)

    cards = ""
    for source_name, source_items in grouped.items():
        color = source_colors.get(source_name, "#555")
        label = source_labels.get(source_name, source_name)
        cards += f'<div class="source-group"><h2 class="source-title" style="border-left:4px solid {color};padding-left:12px">{label} <span class="count">{len(source_items)}</span></h2>'
        for item in source_items:
            pub = item["published"][:16] if item["published"] else ""
            summary = item["summary"][:150] if item["summary"] else ""
            cards += f'''<article class="item">
                <h3><a href="{item['url']}" target="_blank" rel="noopener">{item['title']}</a></h3>
                <div class="meta">{pub}</div>
                {f'<p class="summary">{summary}</p>' if summary else ''}
            </article>'''
        cards += "</div>"

    html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Daily - {today}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f7;color:#1d1d1f;line-height:1.6}}
.container{{max-width:720px;margin:0 auto;padding:20px}}
header{{text-align:center;padding:32px 0 24px}}
header h1{{font-size:28px;font-weight:700}}
header .date{{color:#86868b;font-size:14px;margin-top:4px}}
header .total{{color:#6e6e73;font-size:13px;margin-top:2px}}
.source-group{{margin-bottom:24px}}
.source-title{{font-size:16px;font-weight:600;margin-bottom:10px;display:flex;align-items:center;gap:8px}}
.count{{font-size:12px;background:#e8e8ed;color:#6e6e73;border-radius:10px;padding:0 8px;line-height:20px}}
.item{{background:#fff;border-radius:10px;padding:14px 16px;margin-bottom:8px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.item h3{{font-size:15px;font-weight:500;line-height:1.4}}
.item h3 a{{color:#1d1d1f;text-decoration:none}}
.item h3 a:hover{{color:#06c;text-decoration:underline}}
.meta{{font-size:12px;color:#86868b;margin-top:4px}}
.summary{{font-size:13px;color:#6e6e73;margin-top:6px;line-height:1.5}}
footer{{text-align:center;color:#86868b;font-size:12px;padding:32px 0 48px}}
@media(prefers-color-scheme:dark){{
body{{background:#1c1c1e;color:#f5f5f7}}
.item{{background:#2c2c2e;box-shadow:0 1px 3px rgba(0,0,0,.2)}}
.item h3 a{{color:#f5f5f7}}
.item h3 a:hover{{color:#64a8ff}}
.meta,.source-title,.total,.date{{color:#98989d}}
.count{{background:#3a3a3c;color:#98989d}}
.summary{{color:#8e8e93}}
}}
</style>
</head>
<body>
<div class="container">
<header>
<h1>🤖 AI Daily</h1>
<div class="date">{today}</div>
<div class="total">共 {len(items)} 条资讯</div>
</header>
{cards}
<footer>自动抓取 · 每日更新</footer>
</div>
</body>
</html>'''
    return html


if __name__ == "__main__":
    items = scrape_all()
    digest_zh = format_digest(items, "zh")
    digest_en = format_digest(items, "en")

    os.makedirs("site", exist_ok=True)

    with open("site/index.html", "w", encoding="utf-8") as f:
        f.write(generate_html(items))
    with open("site/items.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    with open("digest_zh.txt", "w", encoding="utf-8") as f:
        f.write(digest_zh)
    with open("digest_en.txt", "w", encoding="utf-8") as f:
        f.write(digest_en)

    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"Scraped {len(items)} items, site/ generated", flush=True)

