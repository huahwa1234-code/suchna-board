"""
Builds site/index.html (a self-contained static webpage) from
notifications_log.json — called automatically by monitor.py after
every check cycle, so the site always reflects the latest notices,
grouped by category (Admit Card / Result / Vacancy / Answer Key /
Syllabus / Admission).

No server required: index.html has the data embedded directly in it,
so it works by just opening the file, or by hosting it anywhere
(GitHub Pages, Netlify drag-and-drop, python -m http.server, etc.)
"""

import json
import logging
import os

logger = logging.getLogger("sarkari_monitor")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "site", "index_template.html")
OUTPUT_PATH = os.path.join(BASE_DIR, "site", "index.html")
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


def generate_site() -> None:
    """Rebuild site/index.html from the current notifications log."""
    if not os.path.exists(TEMPLATE_PATH):
        logger.warning("Site template not found at %s — skipping site build.", TEMPLATE_PATH)
        return

    items = load_notifications()
    # newest first, capped
    items_sorted = sorted(items, key=lambda x: x.get("timestamp", ""), reverse=True)[:MAX_ITEMS_ON_SITE]

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    json_blob = json.dumps(items_sorted, ensure_ascii=False)
    html = template.replace("__NOTIFICATIONS_JSON__", json_blob)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("Site updated: %s (%d notices shown)", OUTPUT_PATH, len(items_sorted))
