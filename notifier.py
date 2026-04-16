# -*- coding: utf-8 -*-
import os
import sys
import json
import requests
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")
FREE_TIER_CHAT_IDS = os.environ.get("FREE_TIER_CHAT_IDS", "").split(",")
PAID_TIER_CHAT_IDS = os.environ.get("PAID_TIER_CHAT_IDS", "").split(",")


def send_telegram(text, chat_id):
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        print("[WARN] Telegram not configured", flush=True)
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for chunk in [text[i:i+4096] for i in range(0, len(text), 4096)]:
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        })
        if resp.status_code != 200:
            print(f"[ERROR] Telegram failed: {resp.text}", flush=True)
            return False
    return True


def send_discord(text):
    if not DISCORD_WEBHOOK:
        print("[WARN] Discord webhook not configured", flush=True)
        return False
    url = DISCORD_WEBHOOK
    chunks = [text[i:i+2000] for i in range(0, min(len(text), 6000), 2000)]
    for chunk in chunks:
        resp = requests.post(url, json={"content": chunk})
        if resp.status_code not in (200, 204):
            print(f"[ERROR] Discord failed: {resp.text}", flush=True)
            return False
    return True


def load_items():
    try:
        with open("items.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def load_digest(lang="zh"):
    path = f"digest_{lang}.txt"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""


def main():
    lang = sys.argv[1] if len(sys.argv) > 1 else "zh"
    is_paid = "--paid" in sys.argv

    digest = load_digest(lang)
    if not digest:
        print("[ERROR] No digest found", flush=True)
        return

    today = datetime.utcnow().strftime("%Y-%m-%d")
    header = f"🤖 AI Daily [{today}] - {付费版 if is_paid else 免费版}"

    target_ids = PAID_TIER_CHAT_IDS if is_paid else FREE_TIER_CHAT_IDS
    if not target_ids or target_ids == [""]:
        target_ids = [TELEGRAM_CHAT_ID] if TELEGRAM_CHAT_ID else []

    sent = 0
    for chat_id in target_ids:
        if chat_id:
            if send_telegram(digest, chat_id):
                sent += 1

    if DISCORD_WEBHOOK:
        send_discord(digest)

    print(f"Sent digest to {sent} recipients", flush=True)


if __name__ == "__main__":
    main()

