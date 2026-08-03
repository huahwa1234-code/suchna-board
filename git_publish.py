"""
Auto-publish the generated site/ folder to GitHub (so GitHub Pages
serves the latest data) by running git add/commit/push as subprocesses.

Requires:
  - git installed and available on PATH
  - the project folder already initialized as a git repo with a
    working 'origin' remote (set up once, manually, per the README)
  - git identity configured (git config --global user.name / user.email)

This module is intentionally defensive: any failure here (no changes
to commit, network issue, auth issue) is logged but never crashes the
monitor loop — Telegram notifications keep working either way.
"""

import logging
import subprocess

import config

logger = logging.getLogger("sarkari_monitor")


def _run(cmd: list) -> tuple:
    """Run a command, return (success, output)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
        output = (result.stdout or "") + (result.stderr or "")
        return result.returncode == 0, output.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, str(e)


def publish_to_git() -> None:
    """Stage, commit, and push the site/ folder if GIT_AUTO_PUSH is enabled."""
    if not getattr(config, "GIT_AUTO_PUSH", False):
        return

    ok, out = _run(["git", "add", "site/", "seen_state.json", "notifications_log.json"])
    if not ok:
        logger.warning("git add failed: %s", out)
        return

    ok, out = _run(["git", "commit", "-m", config.GIT_COMMIT_MESSAGE])
    if not ok:
        if "nothing to commit" in out.lower():
            return  # no site changes since last push — normal, not an error
        logger.warning("git commit failed: %s", out)
        return

    ok, out = _run(["git", "push", "origin", "main"])
    if not ok:
        logger.warning("git push failed: %s", out)
        return

    logger.info("Site pushed to GitHub — live site will update shortly.")
