# -*- coding: utf-8 -*-
import os
import sys
import json
import requests
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ADMIN_ID = os.environ.get("ADMIN_ID", "")

SUB_PRICE_CNY = 10
SUB_DURATION_DAYS = 30

DB_FILE = "subscribers.json"
PAYMENT_QRS = {
    "wechat": os.environ.get("WECHAT_QR_URL", "https://i.imgur.com/placeholder.png"),
}


def get_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"free": [], "paid": []}


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def get_updates(offset=0):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 30}
    resp = requests.get(url, params=params, timeout=35)
    return resp.json()


def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "reply_markup": reply_markup}
    requests.post(url, json=data)


def is_paid(chat_id):
    db = get_db()
    for sub in db.get("paid", []):
        if sub["chat_id"] == str(chat_id):
            exp = datetime.fromisoformat(sub["expires"])
            return datetime.now() < exp
    return False


def subscribe(chat_id, months=1):
    db = get_db()
    expires = datetime.now() + timedelta(days=SUB_DURATION_DAYS * months)
    existing = [s for s in db["paid"] if s["chat_id"] == str(chat_id)]
    if existing:
        old_exp = datetime.fromisoformat(existing[0]["expires"])
        new_exp = max(old_exp, datetime.now()) + timedelta(days=SUB_DURATION_DAYS * months)
        existing[0]["expires"] = new_exp.isoformat()
    else:
        db["paid"].append({
            "chat_id": str(chat_id),
            "joined": datetime.now().isoformat(),
            "expires": expires.isoformat(),
        })
    save_db(db)
    return expires


def run_bot():
    offset = 0
    paid_users = set(s["chat_id"] for s in get_db().get("paid", []))
    free_users = set(s["chat_id"] for s in get_db().get("free", []))

    print("Bot started...", flush=True)
    while True:
        try:
            updates = get_updates(offset)
            if updates.get("ok"):
                for u in updates.get("result", []):
                    offset = u["update_id"] + 1
                    msg = u.get("message", {})
                    chat = msg.get("chat", {})
                    text = msg.get("text", "")
                    chat_id = chat.get("id")

                    if text == "/start":
                        send_message(chat_id,
                            "🤖 欢迎使用 AI Daily Bot\n\n"
                            "/subscribe - 订阅付费版 ¥10/月\n"
                            "/status - 查看订阅状态\n"
                            "/free - 加入免费频道\n"
                            "/help - 帮助"
                        )
                    elif text == "/subscribe":
                        kb = {
                            "inline_keyboard": [[
                                {"text": "💚 微信支付 ¥10", "callback_data": "pay_wechat"}
                            ]]
                        }
                        send_message(chat_id,
                            f"💳 订阅付费版\n"
                            f"价格：¥{SUB_PRICE_CNY}/月\n"
                            f"包含：英文版 + 关键词监控 + 历史搜索\n"
                            f"\n点击下方按钮支付：",
                            reply_markup=kb
                        )
                    elif text == "/status":
                        if is_paid(chat_id):
                            db = get_db()
                            sub = next((s for s in db["paid"] if s["chat_id"] == str(chat_id)), None)
                            exp = datetime.fromisoformat(sub["expires"]).strftime("%Y-%m-%d")
                            send_message(chat_id, f"✅ 付费版会员，到期：{exp}")
                        else:
                            send_message(chat_id, "❌ 当前为免费用户，订阅：/subscribe")
                    elif text == "/help":
                        send_message(chat_id,
                            "📖 AI Daily Bot 使用帮助\n\n"
                            "/subscribe - 订阅付费版\n"
                            "/status - 订阅状态\n"
                            "/free - 免费版介绍\n\n"
                            "付费问题联系 @your_admin"
                        )
                    elif str(chat_id) == ADMIN_ID and text.startswith("/addpaid"):
                        target = text.split()[1] if len(text.split()) > 1 else str(chat_id)
                        exp = subscribe(target)
                        send_message(chat_id, f"✅ 已为 {target} 开通，到期：{exp.strftime(%Y-%m-%d)}")
                    else:
                        if not is_paid(chat_id):
                            send_message(chat_id, "发送 /help 查看命令")
        except Exception as e:
            print(f"[ERROR] {e}", flush=True)


if __name__ == "__main__":
    run_bot()

