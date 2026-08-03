"""
Small wrapper around Telegram Bot API's sendMessage endpoint.
No external telegram library needed — plain requests call.
"""

import logging
import requests

logger = logging.getLogger("sarkari_monitor")


def send_telegram_message(bot_token: str, chat_id: str, text: str) -> bool:
    """Send a text message via Telegram Bot API. Returns True on success."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, data=payload, timeout=15)
        if resp.status_code == 200 and resp.json().get("ok"):
            return True
        logger.error("Telegram send failed [%s]: %s", resp.status_code, resp.text)
        return False
    except requests.RequestException as e:
        logger.error("Telegram request error: %s", e)
        return False


def format_notification(site_name: str, category: str, title: str, link: str) -> str:
    """Build a nicely formatted HTML message for Telegram."""
    return (
        f"🔔 <b>{category}</b>\n"
        f"🏛️ <b>Site:</b> {site_name}\n"
        f"📄 <b>Title:</b> {title}\n"
        f"🔗 <a href=\"{link}\">Open Link</a>"
    )
