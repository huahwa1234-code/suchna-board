"""
Sarkari Result / Govt Job Website Monitor -> Telegram Bot
-----------------------------------------------------------
What it does:
  1. Visits every website listed in config.SITES
  2. Scans all links (<a> tags) on the homepage
  3. Auto-tags each link into a category (Admit Card / Result / Vacancy /
     Answer Key / Syllabus / Admission) based on keywords in its text
  4. Compares against previously-seen links (stored in seen_state.json)
  5. Sends only the NEW matching links to your Telegram chat
  6. Repeats every CHECK_INTERVAL_MINUTES (set in config.py)

Setup:
  pip install -r requirements.txt
  set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (env vars or edit config.py)
  python monitor.py            # runs forever, checking on a schedule
  python monitor.py --once     # run a single check and exit (good for cron)
"""

import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
import schedule
from bs4 import BeautifulSoup

import config
from telegram_notify import send_telegram_message, format_notification
from site_generator import append_notification, generate_site
from git_publish import publish_to_git

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sarkari_monitor")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT = 20  # seconds


# ---------------------------------------------------------------------------
# State handling (remembers what's already been notified)
# ---------------------------------------------------------------------------
def load_state() -> dict:
    if os.path.exists(config.STATE_FILE):
        try:
            with open(config.STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not read state file, starting fresh: %s", e)
    return {}


def save_state(state: dict) -> None:
    try:
        with open(config.STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error("Could not save state file: %s", e)


def link_hash(text: str, href: str) -> str:
    return hashlib.sha256(f"{text.strip()}|{href.strip()}".encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Categorization
# ---------------------------------------------------------------------------
def categorize(text: str):
    lowered = text.lower()
    for category, keywords in config.CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                return category
    return None if config.STRICT_MODE else config.DEFAULT_CATEGORY


# ---------------------------------------------------------------------------
# Core scraping logic for one site
# ---------------------------------------------------------------------------
def check_site(site: dict, state: dict) -> int:
    """Check a single site, notify about new items, return count of new items."""
    name, url = site["name"], site["url"]
    seen = set(state.get(name, []))
    new_count = 0

    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("[%s] fetch failed: %s", name, e)
        return 0

    soup = BeautifulSoup(resp.text, "html.parser")
    anchors = soup.find_all("a", href=True)

    for a in anchors:
        text = a.get_text(strip=True)
        href = a["href"]
        if not text or len(text) < 5:
            continue

        category = categorize(text)
        if category is None:
            continue  # doesn't match any tracked category, skip (strict mode)

        h = link_hash(text, href)
        if h in seen:
            continue  # already notified before

        # New item found
        seen.add(h)
        full_link = urljoin(url, href)
        message = format_notification(name, category, text, full_link)

        sent = send_telegram_message(
            config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, message
        )
        if sent:
            logger.info("[%s] Notified: [%s] %s", name, category, text[:70])
            new_count += 1
            append_notification(
                site=name,
                category=category,
                title=text,
                link=full_link,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        else:
            # If sending failed, don't mark as seen so we retry next cycle
            seen.discard(h)

        time.sleep(1)  # small delay to avoid Telegram rate limits

    state[name] = list(seen)
    return new_count


# ---------------------------------------------------------------------------
# Full check cycle across all configured sites
# ---------------------------------------------------------------------------
def run_check_cycle():
    logger.info("Starting check cycle across %d sites...", len(config.SITES))
    state = load_state()
    total_new = 0

    for site in config.SITES:
        try:
            found = check_site(site, state)
            total_new += found
            if found > 0:
                save_state(state)   # persist immediately so a crash doesn't re-send
                generate_site()     # website updates the instant new items are found
                publish_to_git()    # push to GitHub so the live site updates too
        except Exception as e:  # keep the loop alive even on unexpected errors
            logger.error("[%s] unexpected error: %s", site["name"], e)

    save_state(state)
    generate_site()
    publish_to_git()
    logger.info("Check cycle complete. %d new notifications sent.", total_new)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    if config.TELEGRAM_BOT_TOKEN.startswith("PUT_YOUR") or config.TELEGRAM_CHAT_ID.startswith("PUT_YOUR"):
        logger.error(
            "Telegram bot token / chat id not set. "
            "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars, or edit config.py."
        )
        sys.exit(1)

    run_once = "--once" in sys.argv

    if run_once:
        run_check_cycle()
        return

    # Run once immediately, then on a schedule
    run_check_cycle()
    schedule.every(config.CHECK_INTERVAL_MINUTES).minutes.do(run_check_cycle)

    logger.info(
        "Monitor running. Checking every %d minutes. Press Ctrl+C to stop.",
        config.CHECK_INTERVAL_MINUTES,
    )
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
