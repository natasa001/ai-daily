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
        print(f"[ERROR] Failed to fetch {source[name]}: {e}", flush=True)
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
            lines.append(f"{i}. {item[title]}")
            lines.append(f"   🔗 {item[url]}")
            if item["summary"]:
                lines.append(f"   📝 {item[summary][:80]}...")
            lines.append("")
        lines.append("─" * 24)
        lines.append("付费订阅 ¥10/月：英文版 / 关键词监控 / 历史搜索")
        lines.append("微信转账后联系 @your_telegram 开通")
    else:
        lines.append(f"🤖 AI Daily | {today}\n")
        lines.append(f"📰 {len(items)} items today\n")
        lines.append("─" * 24)
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item[title]}")
            lines.append(f"   🔗 {item[url]}")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    items = scrape_all()
    digest_zh = format_digest(items, "zh")
    digest_en = format_digest(items, "en")

    with open("digest_zh.txt", "w", encoding="utf-8") as f:
        f.write(digest_zh)
    with open("digest_en.txt", "w", encoding="utf-8") as f:
        f.write(digest_en)

    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"Scraped {len(items)} items", flush=True)

