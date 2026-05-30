"""
Scrape unreplied comments from @codewithtyler's TikTok videos.

Reads the saved session from data/storage_state.json (run auth.py first),
visits the profile, collects video URLs, opens each video's comments panel,
scrolls to load all comments, and captures the ones the creator hasn't
replied to yet.

Output:
  - data/comments.json      structured list of unreplied comments
  - data/last_run.html      DOM snapshot of the last video opened (for debugging)
  - data/screenshot.png     screenshot of the last video page

Usage:
  python3 ~/.claude/skills/tiktok-replier/scrape.py             # default: 3 videos
  python3 ~/.claude/skills/tiktok-replier/scrape.py --videos 10
  python3 ~/.claude/skills/tiktok-replier/scrape.py --headed    # show the browser
"""

import argparse
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

SKILL_DIR = Path(__file__).parent
DATA_DIR = SKILL_DIR / "data"
PROFILE_DIR = DATA_DIR / "profile"
OUTPUT_FILE = DATA_DIR / "comments.json"
DEBUG_HTML = DATA_DIR / "last_run.html"
DEBUG_PNG = DATA_DIR / "screenshot.png"

USERNAME = "codewithtyler"
PROFILE_URL = f"https://www.tiktok.com/@{USERNAME}"


def collect_video_urls(page, limit):
    page.goto(PROFILE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # Scroll a bit so more videos load
    for _ in range(3):
        page.mouse.wheel(0, 1500)
        page.wait_for_timeout(800)

    urls = page.eval_on_selector_all(
        f'a[href*="/@{USERNAME}/video/"]',
        "els => Array.from(new Set(els.map(e => e.href)))",
    )
    print(f"Found {len(urls)} videos on profile, taking first {limit}")
    return urls[:limit]


def dismiss_overlays(page):
    """Dismiss TikTok's keyboard-shortcuts tutorial only (very surgical)."""
    page.evaluate(
        """() => {
            // Find the keyboard-shortcut tutorial — it has very specific text
            // like "Introducing keyboard shortcuts" and lists shortcut keys.
            const all = document.querySelectorAll('div, section, aside');
            for (const el of all) {
                const t = (el.innerText || '');
                if (/Introducing keyboard shortcuts/i.test(t) && t.length < 2000) {
                    // Walk up a couple parents to find the modal container, then remove it
                    let target = el;
                    for (let i = 0; i < 3 && target.parentElement; i++) {
                        if (target.parentElement.children.length > 1) break;
                        target = target.parentElement;
                    }
                    target.remove();
                }
            }
        }"""
    )


def scrape_comments_for_video(page, video_url):
    print(f"\n--- Scraping {video_url}")
    page.goto(video_url, wait_until="domcontentloaded")
    page.wait_for_timeout(3500)
    dismiss_overlays(page)
    page.wait_for_timeout(1500)

    # The right panel defaults to "You may like" — find the visible "Comments"
    # tab on that panel (NOT the inbox notification one) and click it.
    try:
        tab = page.get_by_role("tab", name="Comments").locator("visible=true").first
        tab.click(timeout=6000)
        print("  clicked Comments tab")
    except Exception:
        # Fallback: any visible button/element with text "Comments" not in the inbox
        try:
            page.evaluate(
                """() => {
                    const candidates = document.querySelectorAll('button, div[role="tab"], span');
                    for (const el of candidates) {
                        const t = (el.innerText || '').trim();
                        if (t !== 'Comments') continue;
                        // skip inbox notifications
                        if (el.closest('[id*="inbox"]')) continue;
                        const r = el.getBoundingClientRect();
                        if (r.width > 0 && r.height > 0) { el.click(); return; }
                    }
                }"""
            )
            print("  clicked Comments tab via JS fallback")
        except Exception as e:
            print(f"  could not click Comments tab: {e}")

    page.wait_for_timeout(2500)

    # Find the comments scroller and scroll it to load more
    for _ in range(10):
        try:
            page.evaluate(
                """() => {
                    const candidates = [
                        '[data-e2e="comment-list"]',
                        '[data-e2e="search-comment-container"]',
                        'div[class*="DivCommentListContainer"]',
                        'div[class*="CommentListContainer"]',
                    ];
                    for (const sel of candidates) {
                        const el = document.querySelector(sel);
                        if (el) { el.scrollBy(0, 1500); return; }
                    }
                    document.scrollingElement && document.scrollingElement.scrollBy(0, 1500);
                }"""
            )
        except Exception:
            pass
        page.wait_for_timeout(800)

    DEBUG_HTML.write_text(page.content(), encoding="utf-8")
    page.screenshot(path=str(DEBUG_PNG), full_page=False)

    # Find the actual right-side comments panel by position (right half of
    # viewport), then iterate user links inside it. Exclude inbox/sidebar
    # notifications by ignoring elements in the left half of the screen.
    raw = page.evaluate(
        """(creator) => {
            const VW = window.innerWidth;
            const NOISE = /^(started following you|liked your video|commented on your video|mentioned you|sent you|tagged you in)/i;
            const TIMESTAMP = /·\\s*\\d+[smhdw]\\s*ago$/i;

            const results = [];
            const seen = new Set();

            // Iterate every @-link on the page
            document.querySelectorAll('a[href^="/@"]').forEach(link => {
                // Position filter: skip anything in the left HALF of the viewport
                // (left nav, inbox notifications, profile sidebar, etc.)
                const r = link.getBoundingClientRect();
                if (r.x < VW * 0.45) return;  // must be right-of-center
                if (r.width === 0) return;     // must be visible

                const author = link.getAttribute('href').replace(/^\\/@/, '').split('?')[0].split('/')[0];
                if (!author || author.toLowerCase() === creator.toLowerCase()) return;

                // Walk up to the row containing this comment
                let row = link.parentElement;
                for (let i = 0; i < 5 && row; i++) {
                    const links = row.querySelectorAll('a[href^="/@"]');
                    if (links.length >= 1 && row.innerText.length > 10) break;
                    row = row.parentElement;
                }
                if (!row) return;

                // Pick longest text inside row that's NOT inside any link
                let text = '';
                row.querySelectorAll('p, span').forEach(el => {
                    if (el.closest('a')) return;
                    const t = (el.innerText || '').trim();
                    if (t && t !== author && t.length > text.length && t.length < 800) {
                        text = t;
                    }
                });

                if (!text) return;
                // Filter out notification-style entries
                if (NOISE.test(text)) return;
                if (TIMESTAMP.test(text)) return;
                // Filter out things that look like just a display name (no spaces or punctuation, very short)
                if (text.length < 3) return;

                const fp = author + '|' + text.slice(0, 80);
                if (seen.has(fp)) return;
                seen.add(fp);

                // creator-reply detection: did the creator post anywhere in this comment thread?
                let creatorReplied = false;
                const thread = row.parentElement;
                if (thread) {
                    thread.querySelectorAll('a[href^="/@"]').forEach(a => {
                        const u = a.getAttribute('href').replace(/^\\/@/, '').split('?')[0].split('/')[0];
                        if (u.toLowerCase() === creator.toLowerCase()) creatorReplied = true;
                    });
                }

                results.push({ author, text, creatorReplied });
            });

            return results;
        }""",
        "codewithtyler",
    )

    print(f"  raw comments parsed: {len(raw)}")
    unreplied = [c for c in raw if c.get("text") and not c.get("creatorReplied")]
    print(f"  unreplied (no creator reply): {len(unreplied)}")
    for c in unreplied[:5]:
        snippet = (c.get("text") or "")[:80].replace("\n", " ")
        print(f"    @{c.get('author')}: {snippet}")

    return [{**c, "video_url": video_url} for c in unreplied]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--videos", type=int, default=3, help="how many recent videos to scrape")
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    args = parser.parse_args()

    if not PROFILE_DIR.exists() or not any(PROFILE_DIR.iterdir()):
        print(f"ERROR: {PROFILE_DIR} not found or empty. Run auth.py first.", file=sys.stderr)
        sys.exit(1)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=not args.headed,
            slow_mo=100,
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

        try:
            video_urls = collect_video_urls(page, args.videos)
            if not video_urls:
                print("No video URLs found. Possible login/captcha issue.", file=sys.stderr)
                page.screenshot(path=str(DEBUG_PNG), full_page=True)
                DEBUG_HTML.write_text(page.content(), encoding="utf-8")
                sys.exit(2)

            all_unreplied = []
            for url in video_urls:
                try:
                    all_unreplied.extend(scrape_comments_for_video(page, url))
                except PWTimeout as e:
                    print(f"  timeout on {url}: {e}", file=sys.stderr)
                except Exception as e:
                    print(f"  error on {url}: {e}", file=sys.stderr)

            OUTPUT_FILE.write_text(json.dumps(all_unreplied, indent=2, ensure_ascii=False))
            print(f"\nSaved {len(all_unreplied)} unreplied comments to {OUTPUT_FILE}")
            print(f"Debug HTML: {DEBUG_HTML}")
            print(f"Debug PNG : {DEBUG_PNG}")
        finally:
            context.close()


if __name__ == "__main__":
    main()
