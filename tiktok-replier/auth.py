"""
One-time TikTok login (persistent profile).

Opens a Chromium window using a persistent profile dir at data/profile/.
You log in to @codewithtyler manually, and the script auto-detects your
session (waits for the `sessionid` cookie). No need to press Enter.

Run again any time you get logged out.

Usage:
    python3 ~/.claude/skills/tiktok-replier/auth.py
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SKILL_DIR = Path(__file__).parent
PROFILE_DIR = SKILL_DIR / "data" / "profile"
LOGIN_URL = "https://www.tiktok.com/login"
PROFILE_URL = "https://www.tiktok.com/@codewithtyler"
LOGIN_TIMEOUT_S = 600  # 10 min to log in / solve captcha


def main():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            slow_mo=50,
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
            ],
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded")

        print("\n" + "=" * 60)
        print("TikTok login window is open.")
        print("Log in as @codewithtyler however you normally do.")
        print("Solve any captcha / 2FA.")
        print("This script will auto-detect your session and exit.")
        print(f"(Times out after {LOGIN_TIMEOUT_S // 60} min if you don't log in.)")
        print("=" * 60 + "\n")

        deadline = time.time() + LOGIN_TIMEOUT_S
        while time.time() < deadline:
            cookies = context.cookies("https://www.tiktok.com")
            names = {c["name"] for c in cookies}
            if "sessionid" in names or "sid_tt" in names:
                print("Logged in — sessionid cookie detected.")
                # Visit the profile briefly to warm caches under this profile
                try:
                    page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=15000)
                    page.wait_for_timeout(2500)
                except Exception:
                    pass
                break
            time.sleep(2)
        else:
            print("Timed out waiting for login. Re-run when ready.")
            context.close()
            return

        print(f"\nProfile saved at: {PROFILE_DIR}")
        print("Run: python3 scrape.py")
        context.close()


if __name__ == "__main__":
    main()
