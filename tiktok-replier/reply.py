"""
Post replies to specific TikTok comments using the persistent profile from auth.py.

Reads data/replies_queue.json (a list of {cid, author, comment_text, video_url, reply_text}),
walks each item, finds the original comment, clicks its Reply button, types the reply,
posts it, then waits before the next.

Tracks posted comment ids in data/posted.json so re-runs skip what's done.

Usage:
  python3 reply.py --dry-run          # navigate + compose, but DO NOT click Post (default)
  python3 reply.py --post             # actually post replies
  python3 reply.py --post --limit 1   # only do the first one (smoke test)
  python3 reply.py --post --limit 1 --headed  # show the browser

Safety:
  - --dry-run is the default. You must explicitly pass --post to actually publish.
  - Defaults to headed mode so you can watch.
  - 30s pause between posts to stay under TikTok's spam thresholds.
"""

# --- skills venv bootstrap -------------------------------------------------
# `python3` is a moving target: a Homebrew upgrade silently re-points it and
# every third-party import here vanishes with no warning. Re-exec under the
# shared skills venv so the interpreter is decided by this file, not by PATH.
# Compares sys.prefix, not the executable path: a venv's bin/python3 is a
# symlink to the base interpreter, so realpath() matches and would never fire.
# If the venv is missing, fall through and run as before.
import os as _os, sys as _sys
_vdir = _os.path.expanduser("~/.claude/skills/.venv")
_vpy = _os.path.join(_vdir, "bin", "python3")
if _os.path.exists(_vpy) and _os.path.abspath(_sys.prefix) != _os.path.abspath(_vdir):
    _os.execv(_vpy, [_vpy, *_sys.argv])
# --- end skills venv bootstrap ---------------------------------------------

import argparse
import json
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

SKILL_DIR = Path(__file__).parent
DATA_DIR = SKILL_DIR / "data"
PROFILE_DIR = DATA_DIR / "profile"
DEFAULT_QUEUE = DATA_DIR / "replies_queue.json"
POSTED_FILE = DATA_DIR / "posted.json"
DEBUG_DIR = DATA_DIR / "reply_debug"

USERNAME = "codewithtyler"
DELAY_BETWEEN_POSTS_S = 30


def load_posted():
    if POSTED_FILE.exists():
        return set(json.loads(POSTED_FILE.read_text()))
    return set()


def save_posted(posted):
    POSTED_FILE.write_text(json.dumps(sorted(posted), indent=2))


def dismiss_overlays(page):
    """Remove TikTok's first-time keyboard-shortcut tutorial without nuking other UI."""
    page.evaluate(
        """() => {
            const all = document.querySelectorAll('div, section, aside');
            for (const el of all) {
                const t = (el.innerText || '');
                if (/Introducing keyboard shortcuts/i.test(t) && t.length < 2000) {
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


def click_comments_tab(page):
    """Click the comment-icon button next to the video player. This opens
    TikTok's real comments view (the right-side 'Comments' tab is a different,
    sidebar-only preview that doesn't expose the proper Reply controls)."""
    # Try the data-e2e comment icon first
    try:
        clicked = page.evaluate(
            """() => {
                const icon = document.querySelector('[data-e2e="comment-icon"]');
                if (icon) {
                    // walk up to find the clickable parent (button or div with click handler)
                    let target = icon;
                    for (let i = 0; i < 4 && target; i++) {
                        if (target.tagName === 'BUTTON' || target.getAttribute('role') === 'button') break;
                        target = target.parentElement;
                    }
                    (target || icon).click();
                    return true;
                }
                return false;
            }"""
        )
        if clicked:
            return
    except Exception:
        pass


def find_and_open_reply(page, target_author, target_text):
    """
    Find the target comment in TikTok's comment row containers, click its
    per-comment Reply button, verify the main composer got prefilled with
    @author. Returns True only if the verification passes.
    """
    snippet = (target_text or "")[:50].replace('"', '\\"')

    # Step 1a: locate the wrapper, find ALL "Reply" candidates, log them
    candidates_info = page.evaluate(
        """({ author, snippet }) => {
            const wrappers = document.querySelectorAll(
                'div[class*="DivCommentItemWrapper"], div[class*="DivCommentObjectWrapper"]'
            );
            const out = { wrappers_total: wrappers.length, matched: false, candidates: [] };
            for (const wrap of wrappers) {
                const link = wrap.querySelector(`a[href^="/@${author}"]`);
                if (!link) continue;
                if (!wrap.innerText.includes(snippet)) continue;
                out.matched = true;
                wrap.scrollIntoView({ block: 'center' });
                wrap.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
                wrap.dispatchEvent(new MouseEvent('mousemove', { bubbles: true }));

                // Find every element whose direct text is "Reply"
                const all = wrap.querySelectorAll('*');
                for (const el of all) {
                    const t = (el.innerText || '').trim();
                    if (t !== 'Reply') continue;
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;

                    const parents = [];
                    let p = el.parentElement;
                    for (let i = 0; i < 4 && p; i++) {
                        parents.push({
                            tag: p.tagName,
                            cls: (p.className || '').toString().slice(0, 80),
                            role: p.getAttribute('role'),
                            tabindex: p.getAttribute('tabindex'),
                        });
                        p = p.parentElement;
                    }
                    out.candidates.push({
                        tag: el.tagName,
                        cls: (el.className || '').toString().slice(0, 80),
                        x: Math.round(r.x + r.width / 2),
                        y: Math.round(r.y + r.height / 2),
                        w: Math.round(r.width),
                        h: Math.round(r.height),
                        parents,
                    });
                }
                break;
            }
            return out;
        }""",
        {"author": target_author, "snippet": snippet},
    )
    print(f"    matched wrapper: {candidates_info['matched']} (of {candidates_info['wrappers_total']} wrappers)")
    print(f"    Reply candidates inside wrapper: {len(candidates_info['candidates'])}")
    for i, c in enumerate(candidates_info["candidates"]):
        print(f"      [{i}] <{c['tag']}> at ({c['x']},{c['y']}) {c['w']}x{c['h']} cls={c['cls']!r}")
        for j, par in enumerate(c["parents"]):
            print(f"           parent[{j}] <{par['tag']}> role={par['role']} tabindex={par['tabindex']} cls={par['cls']!r}")

    if not candidates_info["matched"] or not candidates_info["candidates"]:
        return False

    # Step 1b: try MULTIPLE click strategies on the first candidate
    target = candidates_info["candidates"][0]
    print(f"    using candidate [0] at ({target['x']},{target['y']})")

    # Strategy 1: real Playwright mouse click at the candidate's center
    print("    strategy 1: page.mouse.click()")
    page.mouse.move(target["x"], target["y"])
    page.wait_for_timeout(200)
    page.mouse.click(target["x"], target["y"])
    page.wait_for_timeout(1500)

    # Did it work?
    placeholder_now = page.evaluate(
        """() => {
            const editors = document.querySelectorAll('div[contenteditable="true"]');
            for (const e of editors) {
                const desc = e.getAttribute('aria-describedby');
                const ph = desc ? document.getElementById(desc) : null;
                const phText = (ph?.innerText || '').toLowerCase();
                if (phText.includes('reply')) return ph.innerText;
            }
            return null;
        }"""
    )
    print(f"    after strategy 1: placeholder = {placeholder_now!r}")

    if not placeholder_now:
        # Strategy 2: walk up parents and click each of them via JS dispatch
        print("    strategy 2: click parent[0], parent[1], parent[2]")
        page.evaluate(
            """({ author, snippet }) => {
                const wrappers = document.querySelectorAll(
                    'div[class*="DivCommentItemWrapper"], div[class*="DivCommentObjectWrapper"]'
                );
                for (const wrap of wrappers) {
                    const link = wrap.querySelector(`a[href^="/@${author}"]`);
                    if (!link) continue;
                    if (!wrap.innerText.includes(snippet)) continue;
                    const all = wrap.querySelectorAll('*');
                    for (const el of all) {
                        const t = (el.innerText || '').trim();
                        if (t !== 'Reply') continue;
                        const r = el.getBoundingClientRect();
                        if (r.width === 0) continue;
                        // Try clicking element + 3 levels of parents
                        let p = el;
                        for (let i = 0; i < 4 && p; i++) {
                            try {
                                p.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                                p.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                                p.click();
                            } catch(e) {}
                            p = p.parentElement;
                        }
                        return;
                    }
                }
            }""",
            {"author": target_author, "snippet": snippet},
        )
        page.wait_for_timeout(1500)

    # Snapshot for debugging
    try:
        page.screenshot(path=str(DEBUG_DIR / "reply-clicked.png"))
        print(f"    screenshot: {DEBUG_DIR / 'reply-clicked.png'}")
    except Exception:
        pass

    page.wait_for_timeout(500)

    # Snapshot composer state right after the Reply click for debugging
    debug = page.evaluate(
        """(author) => {
            const editors = document.querySelectorAll('div[contenteditable="true"]');
            const out = [];
            editors.forEach((e, i) => {
                const desc = e.getAttribute('aria-describedby');
                const ph = desc ? document.getElementById(desc) : null;
                out.push({
                    i,
                    text: (e.innerText || '').slice(0, 200),
                    html: (e.innerHTML || '').slice(0, 400),
                    placeholder: ph ? (ph.innerText || '').slice(0, 100) : null,
                    focused: e === document.activeElement,
                });
            });
            return out;
        }""",
        target_author,
    )
    print(f"    composers ({len(debug)}):")
    for d in debug:
        print(f"      [{d['i']}] focused={d['focused']} placeholder={d['placeholder']!r}")
        print(f"            text={d['text']!r}")
        if "@" in d["html"] or "mention" in d["html"].lower():
            print(f"            html-snippet={d['html']!r}")

    # Permissive verification: any of these means we're in reply context
    matched = page.evaluate(
        """(author) => {
            const a = author.toLowerCase();
            const editors = document.querySelectorAll('div[contenteditable="true"]');
            for (const e of editors) {
                const text = (e.innerText || '').toLowerCase();
                const html = (e.innerHTML || '').toLowerCase();
                if (text.includes('@' + a)) return 'text-has-mention';
                if (html.includes(a)) return 'html-has-author';
                const desc = e.getAttribute('aria-describedby');
                const ph = desc && document.getElementById(desc);
                const phText = (ph?.innerText || '').toLowerCase();
                if (phText.includes('reply')) return 'placeholder-says-reply';
            }
            return null;
        }""",
        target_author,
    )
    if not matched:
        print(f"    SKIP: clicked Reply but composer did not enter reply context")
        return False
    print(f"    composer ready (signal: {matched})")
    return True


def type_and_post(page, reply_text, do_post):
    """Find the comment input, type the reply, optionally click Post.

    TikTok uses Draft.js where the placeholder div overlays the contenteditable
    and intercepts pointer events. We focus via JS and type via keyboard.
    """
    # Focus the reply composer in JS (the one currently visible after clicking Reply)
    focused = page.evaluate(
        """() => {
            // Prefer the editor that has the 'Add a reply' placeholder
            const editors = document.querySelectorAll('div[contenteditable="true"]');
            let target = null;
            for (const e of editors) {
                const desc = e.getAttribute('aria-describedby');
                const placeholder = desc && document.getElementById(desc);
                const phText = (placeholder?.innerText || '').toLowerCase();
                if (phText.includes('reply')) { target = e; break; }
            }
            if (!target && editors.length > 0) target = editors[editors.length - 1];
            if (!target) return false;
            target.focus();
            target.scrollIntoView({ block: 'center' });
            return true;
        }"""
    )
    if not focused:
        raise RuntimeError("could not find / focus the reply composer")
    page.wait_for_timeout(500)

    # Type via keyboard (works around the placeholder click interception)
    page.keyboard.type(reply_text, delay=20)
    page.wait_for_timeout(800)

    if not do_post:
        print("    [DRY-RUN] composed reply but NOT posting")
        return False

    # The submit button is an arrow icon. TikTok's selector is data-e2e="comment-post".
    # We need a real mouse click (same trick as the Reply button).
    submit_info = page.evaluate(
        """() => {
            // Prefer the post button that's currently enabled (not disabled-opacity)
            const candidates = Array.from(document.querySelectorAll(
                '[data-e2e="comment-post"], button[aria-label*="Post" i], svg[class*="Post"]'
            ));
            const visible = candidates.filter(el => {
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            });
            return visible.map(el => {
                // Walk up to find the actual clickable button/div
                let target = el;
                for (let i = 0; i < 4 && target.parentElement; i++) {
                    const cls = (target.className || '').toString();
                    if (target.tagName === 'BUTTON' || cls.includes('Button')) break;
                    target = target.parentElement;
                }
                const r = target.getBoundingClientRect();
                return {
                    tag: target.tagName,
                    cls: (target.className || '').toString().slice(0, 80),
                    x: Math.round(r.x + r.width / 2),
                    y: Math.round(r.y + r.height / 2),
                    w: Math.round(r.width),
                    h: Math.round(r.height),
                    'aria-label': target.getAttribute('aria-label'),
                    'data-e2e': target.getAttribute('data-e2e'),
                };
            });
        }"""
    )
    print(f"    submit candidates ({len(submit_info)}):")
    for i, s in enumerate(submit_info):
        print(f"      [{i}] <{s['tag']}> at ({s['x']},{s['y']}) {s['w']}x{s['h']} "
              f"data-e2e={s['data-e2e']!r} aria={s['aria-label']!r}")

    if not submit_info:
        print("    ERROR: no submit button found")
        return False

    # The reply submit is the one closer to the focused composer (right side, lower).
    # Pick the one with the smallest distance to the focused composer's center.
    composer_pos = page.evaluate(
        """() => {
            const editors = document.querySelectorAll('div[contenteditable="true"]');
            for (const e of editors) {
                if (e === document.activeElement) {
                    const r = e.getBoundingClientRect();
                    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
                }
            }
            return null;
        }"""
    )
    target = submit_info[0]
    if composer_pos:
        target = min(
            submit_info,
            key=lambda s: abs(s["x"] - composer_pos["x"]) + abs(s["y"] - composer_pos["y"]),
        )
    print(f"    >>> CLICKING SUBMIT at ({target['x']},{target['y']})")
    try:
        page.screenshot(path=str(DEBUG_DIR / "submit-before.png"))
    except Exception:
        pass
    page.mouse.move(target["x"], target["y"])
    page.wait_for_timeout(300)
    page.mouse.click(target["x"], target["y"])
    page.wait_for_timeout(3000)
    try:
        page.screenshot(path=str(DEBUG_DIR / "submit-after.png"))
    except Exception:
        pass

    # Verification (lenient): composer cleared OR reply composer gone OR comment count rose
    state = page.evaluate(
        """(replyText) => {
            const editors = document.querySelectorAll('div[contenteditable="true"]');
            let replyComposerStillThere = false;
            let replyComposerText = null;
            for (const e of editors) {
                const desc = e.getAttribute('aria-describedby');
                const ph = desc ? document.getElementById(desc) : null;
                const phText = (ph?.innerText || '').toLowerCase();
                if (phText.includes('reply')) {
                    replyComposerStillThere = true;
                    replyComposerText = (e.innerText || '').trim();
                }
            }
            // Did our reply text land in the visible comments?
            const newCommentVisible = !!Array.from(document.querySelectorAll('p, span'))
                .find(el => (el.innerText || '').includes(replyText.slice(0, 40)));
            return {
                replyComposerStillThere,
                replyComposerText,
                newCommentVisible,
            };
        }""",
        reply_text,
    )
    print(f"    after submit: {state}")

    # Decide success:
    # - composer disappeared = posted
    # - composer cleared = posted
    # - new comment matching reply text visible = posted
    if not state["replyComposerStillThere"]:
        print("    POSTED ✓ (reply composer gone)")
        return True
    if state["replyComposerText"] == "":
        print("    POSTED ✓ (composer cleared)")
        return True
    if state["newCommentVisible"]:
        print("    POSTED ✓ (reply visible in DOM)")
        return True
    print("    UNCERTAIN: clicked submit but couldn't confirm — check TikTok manually")
    print(f"    screenshots saved: submit-before.png, submit-after.png")
    return False


def is_logged_in(context, page):
    """Verify the persistent profile still has a live TikTok session.
    Primary signal: sessionid cookie is set. Fallback: DOM check on tiktok.com
    for the top-right 'Log in' button (present only when logged out)."""
    try:
        cookies = context.cookies("https://www.tiktok.com")
    except Exception:
        cookies = []
    if any(c.get("name") == "sessionid" and c.get("value") for c in cookies):
        return True

    try:
        page.goto("https://www.tiktok.com/foryou", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        login_btn = page.query_selector('[data-e2e="top-login-button"]')
        return login_btn is None
    except Exception:
        return False


def process_one(page, item, do_post, debug_idx):
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n[{debug_idx}] @{item['author']}: {item['comment_text'][:60]!r}")
    print(f"    video: {item['video_url']}")

    page.goto(item["video_url"], wait_until="domcontentloaded")
    page.wait_for_timeout(3500)
    dismiss_overlays(page)
    page.wait_for_timeout(800)
    click_comments_tab(page)
    page.wait_for_timeout(2500)

    # Scroll inside the comments panel a few times to load enough
    for _ in range(6):
        page.evaluate(
            """() => {
                const VW = window.innerWidth;
                const all = document.querySelectorAll('div');
                for (const d of all) {
                    const r = d.getBoundingClientRect();
                    if (r.x < VW * 0.45) continue;
                    if (d.scrollHeight > d.clientHeight) {
                        d.scrollBy(0, 800);
                        return;
                    }
                }
            }"""
        )
        page.wait_for_timeout(700)

    if not find_and_open_reply(page, item["author"], item["comment_text"]):
        print(f"    SKIP: could not find that comment in the panel")
        page.screenshot(path=str(DEBUG_DIR / f"{debug_idx}-not-found.png"))
        return False

    page.wait_for_timeout(1000)
    page.screenshot(path=str(DEBUG_DIR / f"{debug_idx}-before-type.png"))

    try:
        posted = type_and_post(page, item["reply_text"], do_post)
    except Exception as e:
        print(f"    ERROR composing: {e}")
        try:
            page.screenshot(path=str(DEBUG_DIR / f"{debug_idx}-compose-error.png"))
        except Exception:
            pass
        return False

    page.wait_for_timeout(1500)
    try:
        page.screenshot(path=str(DEBUG_DIR / f"{debug_idx}-after.png"))
    except Exception:
        pass

    if not do_post:
        return False  # dry-run: do not mark as posted
    if not posted:
        print(f"    WARN: type completed but Post click did not fire")
        return False
    print(f"    POSTED ✓")
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--post", action="store_true", help="actually publish (default: dry-run)")
    p.add_argument("--dry-run", action="store_true", help="explicit dry-run (default)")
    p.add_argument("--limit", type=int, default=0, help="only process first N items")
    p.add_argument("--headed", action="store_true", default=True, help="show the browser (default)")
    p.add_argument("--headless", action="store_true", help="hide the browser")
    p.add_argument("--queue", type=str, default=None,
                   help="path to a queue JSON (default: data/replies_queue.json). "
                        "Use data/drafts_queue.json to post auto-drafts from monitor.py.")
    args = p.parse_args()
    queue_file = Path(args.queue) if args.queue else DEFAULT_QUEUE

    do_post = args.post and not args.dry_run

    if not PROFILE_DIR.exists() or not any(PROFILE_DIR.iterdir()):
        print(f"ERROR: {PROFILE_DIR} not found. Run auth.py first.", file=sys.stderr)
        sys.exit(1)
    if not queue_file.exists():
        print(f"ERROR: {queue_file} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"queue file: {queue_file}")
    queue = json.loads(queue_file.read_text())
    posted_already = load_posted()
    queue = [q for q in queue if q["cid"] not in posted_already]
    if args.limit > 0:
        queue = queue[: args.limit]

    print(f"queue: {len(queue)} replies to process")
    print(f"mode : {'POST (live)' if do_post else 'DRY-RUN (no posting)'}")
    if not queue:
        print("nothing to do.")
        return

    headless = args.headless
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            slow_mo=50,
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            args=["--disable-blink-features=AutomationControlled", "--no-first-run"],
        )
        page = context.pages[0] if context.pages else context.new_page()

        if not is_logged_in(context, page):
            print("\nERROR: TikTok session expired (no valid sessionid cookie).", file=sys.stderr)
            print("       Re-auth with: python3 ~/.claude/skills/tiktok-replier/auth.py", file=sys.stderr)
            context.close()
            sys.exit(2)
        print("session: logged in ✓\n")

        try:
            for idx, item in enumerate(queue, start=1):
                ok = process_one(page, item, do_post, idx)
                if ok:
                    posted_already.add(item["cid"])
                    save_posted(posted_already)
                if idx < len(queue):
                    print(f"    waiting {DELAY_BETWEEN_POSTS_S}s before next...")
                    time.sleep(DELAY_BETWEEN_POSTS_S)
        finally:
            context.close()

    print(f"\ndone. {len(posted_already)} posted total (cumulative).")


if __name__ == "__main__":
    main()
