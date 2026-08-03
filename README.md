# Sarkari Job / Result Website Monitor → Telegram Bot

25 government / job-portal websites ko monitor karta hai aur naye **Admit Card**,
**Result**, **Vacancy/Recruitment**, **Answer Key**, **Syllabus**, **Admission**
notifications ko automatically Telegram par bhejta hai.

## Files
- `config.py` — website list (25 sites), category keywords, settings
- `monitor.py` — main script (scrape → detect new → notify)
- `telegram_notify.py` — Telegram messaging helper
- `seen_state.json` — auto-created; remembers already-notified links
- `requirements.txt` — Python dependencies

## Setup

### 1. Telegram Bot banao
1. Telegram par **@BotFather** ko message karo → `/newbot` → naam/username do
2. Aapko ek **Bot Token** milega (jaise `123456:ABC-xyz...`)
3. Apne bot ko ek message bhejo (ya group me add karo), phir yeh URL kholo
   browser me apna token daal ke:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Response me `"chat":{"id": ...}` — yahi aapka **Chat ID** hai

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Token/Chat ID set karo
Environment variables se (recommended):
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```
Ya seedha `config.py` file me `PUT_YOUR_BOT_TOKEN_HERE` / `PUT_YOUR_CHAT_ID_HERE`
ki jagah apni values likh do.

### 4. Run karo
```bash
python monitor.py            # continuously chalega, har 30 min me check karega
python monitor.py --once     # sirf ek baar check karke exit ho jayega (cron ke liye)
```

Check interval `config.py` me `CHECK_INTERVAL_MINUTES` se change kar sakte ho.

## Website (Suchna Board)
Har check cycle ke baad `site/index.html` automatically update hota hai —
isme saare notifications **category-wise** (Admit Card, Result, Vacancy,
Answer Key, Syllabus, Admission) dikhte hain, filter buttons ke saath, aur
top par ek scrolling ticker latest notices ka.

**Dekhne ke 3 tareeke:**
1. **Seedha kholo** — `site/index.html` ko phone/PC ke browser me directly open karo (double-tap / "Open with browser")
2. **Local server** (agar direct-open me dikkat ho):
   ```bash
   cd site
   python -m http.server 8000
   ```
   Phir browser me `http://localhost:8000` kholo (Termux me `http://127.0.0.1:8000`)
3. **Internet par host karo** (dusron ko bhi dikhana ho to):
   - `site/index.html` ko **Netlify Drop** (app.netlify.com/drop) par drag-drop karo — turant free live URL milega
   - Ya GitHub Pages / Vercel par bhi same file upload kar sakte ho

Data seedha HTML file ke andar hi embed hota hai (`notifications_log.json` se),
to hosting simple hai — koi backend/database chalane ki zaroorat nahi.
`notifications_log.json` khud delete karke reset kar sakte ho (fresh start).

## Live website (GitHub Pages) — automatic updates
Agar aapne repo already GitHub par set up kar liya hai (`git remote add origin ...`
wagera), to `config.py` me `GIT_AUTO_PUSH = True` rakhne se bot **har naya
notification milne par khud** `git add` → `git commit` → `git push` karega.
Kuch minute me GitHub Pages apna deployment update kar deta hai, aur live
site (`https://<username>.github.io/<repo>/site/`) automatically naya data
dikhane lagti hai — bina kisi manual step ke.

**One-time setup zaroori hai** (agar abhi tak nahi kiya):
```bash
pkg install git -y
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
cd /path/to/project-folder
git config --global --add safe.directory "$(pwd)"
git init
git add site/
git commit -m "Initial site"
git branch -M main
git remote add origin https://YOUR_TOKEN@github.com/USERNAME/REPO.git
git push -u origin main
```
Phir GitHub repo → **Settings → Pages** → Branch `main`, folder `/site` (ya root,
us case me URL ke end me `/site/` add karna hoga) → Save.

**Auto-push band karna ho** (sirf local site chahiye, GitHub push nahi) to
`config.py` me:
```python
GIT_AUTO_PUSH = False
```

⚠️ Apna GitHub token kabhi chat/message me paste mat karo — sirf seedha
terminal me use karo. Agar galti se kahin share ho gaya ho, GitHub par turant
us token ko **revoke** karke naya banao.

## Websites/categories add-remove karna
`config.py` me `SITES` list me naya dictionary add karo:
```python
{"name": "My New Site", "url": "https://example.gov.in"},
```
Categories (`CATEGORY_KEYWORDS`) me bhi naye keywords add kar sakte ho — jaise
kisi site par "recruitment" ki jagah "bharti" likha ho.

## Important notes
- Har website ka HTML structure alag hota hai — yeh script generic keyword-based
  approach use karta hai (page ke saare links check karke jisme "admit card",
  "result", "recruitment" jaisa text ho unhe pakadta hai). Zyadatar sarkari
  sites ke liye yeh kaam karega, lekin agar koi site JavaScript-heavy hai
  (content JS se load hota hai) to woh site properly scan nahi hogi — us case
  me Selenium/Playwright jaisi tool chahiye hogi, jo maang par add ki ja sakti hai.
- Kuch sites scraping block kar sakti hain (rate-limit / captcha) — agar koi
  site baar-baar fail ho rahi hai, script use skip karke aage badh jayega aur
  baaki sites continue karega.
- 24x7 chalane ke liye is script ko server/VPS par `systemd` service ya
  `nohup python monitor.py &` se background me chalao, ya `--once` flag ke
  saath cron job set karo (e.g. har 30 min).
- Telegram rate limits se bachne ke liye messages ke beech 1 second ka delay
  already diya gaya hai.

## Example cron entry (har 30 minute me check)
```
*/30 * * * * cd /path/to/sarkari-monitor && /usr/bin/python3 monitor.py --once >> monitor.log 2>&1
```
