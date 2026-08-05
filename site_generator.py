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

Retention: notifications stay in the log (and on the site) for
RETENTION_DAYS (default 365) from when they were first seen — old items
are only dropped once they age past that, not because of a count cap.
Duplicates (same site+title+link seen more than once) are collapsed to a
single entry automatically.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("sarkari_monitor")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "site", "index_template.html")
OUTPUT_PATH = os.path.join(BASE_DIR, "site", "index.html")
DATA_JSON_PATH = os.path.join(BASE_DIR, "site", "data.json")
NOTIFICATIONS_LOG = os.path.join(BASE_DIR, "notifications_log.json")

RETENTION_DAYS = 365     # keep notifications on site for this long
MAX_ITEMS_ON_SITE = 5000 # hard safety cap only — retention/dedup keep this from being hit normally


def load_notifications() -> list:
    if not os.path.exists(NOTIFICATIONS_LOG):
        return []
    try:
        with open(NOTIFICATIONS_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not read notifications log: %s", e)
        return []


def _dedupe_and_trim(items: list) -> list:
    """Collapse duplicate (site, title, link) entries to one, and drop
    anything older than RETENTION_DAYS. Order is not guaranteed on input."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    best_by_key = {}
    for item in items:
        ts = item.get("timestamp", "")
        try:
            ts_dt = datetime.fromisoformat(ts)
            if ts_dt.tzinfo is None:
                ts_dt = ts_dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue  # skip entries with an unparseable/missing date
        if ts_dt < cutoff:
            continue  # older than retention window — drop

        key = (item.get("site", ""), item.get("title", ""), item.get("link", ""))
        existing = best_by_key.get(key)
        if existing is None or ts > existing.get("timestamp", ""):
            best_by_key[key] = item

    deduped = list(best_by_key.values())
    deduped.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return deduped[:MAX_ITEMS_ON_SITE]


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
    items = _dedupe_and_trim(items)
    try:
        with open(NOTIFICATIONS_LOG, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error("Could not write notifications log: %s", e)


def _get_items_sorted() -> list:
    items = load_notifications()
    return _dedupe_and_trim(items)


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
