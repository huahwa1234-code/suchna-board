"""
Configuration for Sarkari Result / Govt Job Monitor Bot
---------------------------------------------------------
- SITES: list of websites to monitor (name + URL)
- CATEGORY_KEYWORDS: keyword -> category mapping used to auto-tag
  every new link found on a page (Admit Card / Result / Vacancy / etc.)
- Edit / add / remove sites freely. Each site just needs a "name" and a "url".
"""

import os

# ---------------------------------------------------------------------------
# 1. Telegram settings (better to set these as environment variables / .env)
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "PUT_YOUR_CHAT_ID_HERE")

# ---------------------------------------------------------------------------
# 2. How often to check all sites (in minutes)
#    Lower = faster updates, but more requests to each site (risk of getting
#    rate-limited/blocked) and more Telegram/API calls. 2 min is a reasonable
#    fast-but-safe default for 25 sites.
# ---------------------------------------------------------------------------
CHECK_INTERVAL_MINUTES = 2

# ---------------------------------------------------------------------------
# 2b. Auto-publish the site to GitHub after every update (for GitHub Pages).
#     Requires: git installed, repo already initialized with 'origin' set,
#     and git identity configured (see README). Set to False to disable.
# ---------------------------------------------------------------------------
GIT_AUTO_PUSH = True
GIT_COMMIT_MESSAGE = "Auto-update: new notifications"

# ---------------------------------------------------------------------------
# 3. File used to remember which links have already been notified
# ---------------------------------------------------------------------------
STATE_FILE = "seen_state.json"

# ---------------------------------------------------------------------------
# 4. Websites to monitor (25 sites — central govt, state PSCs, banking,
#    defence, and aggregator sites). Add more the same way any time.
# ---------------------------------------------------------------------------
SITES = [
    {"name": "SSC",                 "url": "https://ssc.nic.in"},
    {"name": "UPSC",                "url": "https://upsc.gov.in"},
    {"name": "IBPS",                "url": "https://www.ibps.in"},
    {"name": "RRB (Railway)",       "url": "https://indianrailways.gov.in"},
    {"name": "UPSSSC",              "url": "https://upsssc.gov.in"},
    {"name": "UPPSC",               "url": "https://uppsc.up.nic.in"},
    {"name": "RPSC (Rajasthan)",    "url": "https://rpsc.rajasthan.gov.in"},
    {"name": "MPPSC",               "url": "https://mppsc.mp.gov.in"},
    {"name": "WBPSC",               "url": "https://wbpsc.gov.in"},
    {"name": "TNPSC",               "url": "https://www.tnpsc.gov.in"},
    {"name": "APPSC",               "url": "https://psc.ap.gov.in"},
    {"name": "TSPSC",               "url": "https://tspsc.gov.in"},
    {"name": "BPSC (Bihar)",        "url": "https://bpsc.bih.nic.in"},
    {"name": "HPSC (Haryana)",      "url": "https://hpsc.gov.in"},
    {"name": "JPSC (Jharkhand)",    "url": "https://jpsc.gov.in"},
    {"name": "UPSSSC",    "url": "https://upsssc.gov.in/AllNotifications.aspx"},
    {"name": "GPSC (Gujarat)",      "url": "https://gpsc.gujarat.gov.in"},
    {"name": "Employment News",     "url": "https://www.employmentnews.gov.in"},
    {"name": "SBI Careers",         "url": "https://bank.sbi/careers"},
    {"name": "RBI Opportunities",   "url": "https://opportunities.rbi.org.in"},
    {"name": "Indian Army",         "url": "https://joinindianarmy.nic.in"},
    {"name": "UPSSSC",         "url": "https://upsssc.gov.in/News.aspx?id=1"},
    {"name": "Sarkari Result",      "url": "https://www.sarkariresult.com"},
    {"name": "FreeJobAlert",        "url": "https://www.freejobalert.com"},
    {"name": "NIACL/Insurance Jobs", "url": "https://www.nicl.co.in"},
    {"name": "MJPRU Bareilly",       "url": "https://mjpru.ac.in/NoticeBoard.aspx"},
    {"name": "MJPRU Exam Result",    "url": "https://mjpruiums.in/(S(zmyf3vfxo1tbxcl5bfiotrmo))/Results/ExamResult.aspx"},
]

# ---------------------------------------------------------------------------
# 5. Keyword -> Category mapping (case-insensitive substring match)
#    Order matters a little: first matching category wins.
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    "Admit Card":  ["admit card", "hall ticket", "call letter", "e-admit"],
    "Answer Key":  ["answer key", "response sheet", "objection"],
    "Result":      ["result", "merit list", "cut off", "cutoff", "selection list", "scorecard", "score card"],
    "Syllabus":    ["syllabus", "exam pattern", "exam scheme"],
    "Admission":   ["admission", "counselling", "counseling"],
    "Vacancy":     ["recruitment", "vacancy", "notification", "apply online",
                     "bharti", "job", "engagement", "walk-in", "walk in"],
}

# Generic fallback category if a link matches none of the keywords above
# but still looks like a notice (used only if you enable STRICT_MODE = False)
DEFAULT_CATEGORY = "General Update"

# If True, only links matching a known keyword are sent (recommended).
# If False, every new link on the page is sent tagged as "General Update".
STRICT_MODE = True
