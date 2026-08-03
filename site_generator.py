"""
Builds the site/ folder from notifications_log.json — called automatically
by monitor.py after every check cycle.

Produces TWO things:
  1. site/data.json — plain JSON array of notifications. This is what a
     static index.html can `fetch('data.json')` to load live data (works
     once hosted, e.g. GitHub Pages; fetch() of a local file does NOT work
     when just double-clicking index.html directly, due to browser CORS
     rules for file:// pages).
  2. site/index.html — only rebuilt from site/index_template.html if that
     template file exists AND still contains the __NOTIFICATIONS_JSON__
     placeholder. If you've hand-customized index.html (e.g. added your
     own widgets) and it now reads from data.json instead, this script
     will NOT touch/overwrite your index.html — only data.json refreshes.
"""

import json
import logging
import os

logger = logging.getLogger("sarkari_monitor")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "site", "index_template.html")
OUTPUT_PATH = os.path.join(BASE_DIR, "site", "index.html")
DATA_JSON_PATH = os.path.join(BASE_DIR, "site", "data.json")
NOTIFICATIONS_LOG = os.path.join(BASE_DIR, "notifications_log.json")

MAX_ITEMS_ON_SITE = 300  # keep the page light — most recent N notices


def load_notifications() -> list:
    if not os.path.exists(NOTIFICATIONS_LOG):
        return []
    try:
        with open(NOTIFICATIONS_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not read notifications log: %s", e)
        return []


def append_notification(site: str, category: str, title: str, link: str, timestamp: str) -> None:
    """Add one notification to the persistent log (used by monitor.py)."""
    items = load_notifications()
    items.append({
        "site": site,
        "category": category,
        "title": title,
        "link": link,
        "timestamp": timestamp,
    })
    # keep the log from growing forever
    items = items[-2000:]
    try:
        with open(NOTIFICATIONS_LOG, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error("Could not write notifications log: %s", e)


def _get_items_sorted() -> list:
    items = load_notifications()
    return sorted(items, key=lambda x: x.get("timestamp", ""), reverse=True)[:MAX_ITEMS_ON_SITE]


def generate_site() -> None:
    """Refresh site/data.json always; refresh site/index.html only if the
    template still uses the embedded-JSON placeholder pattern."""
    os.makedirs(os.path.join(BASE_DIR, "site"), exist_ok=True)
    items_sorted = _get_items_sorted()

    # 1. Always write data.json — this is what fetch('data.json') reads.
    try:
        with open(DATA_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(items_sorted, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error("Could not write data.json: %s", e)

    # 2. Only rebuild index.html from the template if that template exists
    #    and still expects embedded JSON (so we never clobber a hand-edited
    #    index.html that now fetches data.json instead).
    if os.path.exists(TEMPLATE_PATH):
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            template = f.read()
        if "__NOTIFICATIONS_JSON__" in template:
            json_blob = json.dumps(items_sorted, ensure_ascii=False)
            html = template.replace("__NOTIFICATIONS_JSON__", json_blob)
            with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
                f.write(html)

    logger.info("Site data updated: %s (%d notices)", DATA_JSON_PATH, len(items_sorted))
