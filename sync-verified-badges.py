#!/usr/bin/env python3
"""
Sync the "Verified & Trusted" badge on category-page listing rows
(food.html, shopping.html, services.html, health.html) with the
verification status shown on each business's individual featured
listing page.

Source of truth: each business's own page has
    <span class="status-pill is-verified">...Verified and Trusted</span>
or
    <span class="status-pill">...Unverified</span>
near the top, under the hero photo.

This script re-reads that status from every business page and
rewrites the category-page rows to match — add the green pill for
verified businesses, remove it (or leave it absent) for unverified
ones. Safe to re-run any time a business's status changes on its own
page; it will not duplicate or drift out of sync.

Usage:
    python3 sync-verified-badges.py
"""
import re
import glob

CATEGORY_PAGES = ["food.html", "shopping.html", "services.html", "health.html"]
EXCLUDE = set(CATEGORY_PAGES) | {"index.html", "spotlight.html"}

BADGE_HTML = (
    '<span class="status-pill is-verified">'
    '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'
    '</svg>Verified &amp; Trusted</span>'
)

CSS_BLOCK = """
    .status-pill {
      display: inline-flex;
      align-items: center;
      font-family: var(--font-sans);
      gap: 5px;
      font-size: 0.625rem;
      font-weight: 800;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      padding: 3px 9px;
      border-radius: 100px;
      vertical-align: middle;
      margin-left: 8px;
    }
    .status-pill.is-verified {
      color: #1E9E5A;
      background: rgba(0,0,0,0.06);
    }
    .status-pill svg { flex-shrink: 0; }
"""


def get_verified_status():
    """Read every individual business page and return {filename: is_verified}."""
    status = {}
    for f in glob.glob("*.html"):
        if f in EXCLUDE or f == "sync-verified-badges.py":
            continue
        content = open(f, encoding="utf-8").read()
        status[f] = 'class="status-pill is-verified"' in content
    return status


def ensure_css(content):
    if ".status-pill {" in content:
        return content
    marker = "    .biz-name {"
    idx = content.index(marker)
    return content[:idx] + CSS_BLOCK.strip("\n") + "\n\n" + content[idx:]


def sync_page(fname, status):
    content = open(fname, encoding="utf-8").read()
    content = ensure_css(content)

    changed = 0

    def replace_row(match):
        nonlocal changed
        href = match.group(1)
        biz_file = href.lstrip("/")
        name_text = match.group(2)
        # whatever currently sits between </a> and </h3> — empty, or a
        # badge span left over from a previous run
        existing_tail = match.group(3)

        is_verified = status.get(biz_file, False)
        new_tail = (" " + BADGE_HTML) if is_verified else ""

        if new_tail != existing_tail:
            changed += 1

        return f'<h3 class="biz-name"><a href="{href}">{name_text}</a>{new_tail}</h3>'

    # Match: <h3 class="biz-name"><a href="...">NAME</a>[optional existing badge]</h3>
    # The name itself never contains a link (only a badge might sit after it),
    # so match the name up to the first </a> non-greedily.
    pattern = re.compile(
        r'<h3 class="biz-name"><a href="([^"]+)">(.*?)</a>(.*?)</h3>',
        re.S,
    )
    content = pattern.sub(replace_row, content)

    open(fname, "w", encoding="utf-8").write(content)
    return changed


def main():
    status = get_verified_status()
    print(f"Read verified status from {len(status)} business pages.")
    total = 0
    for page in CATEGORY_PAGES:
        n = sync_page(page, status)
        print(f"  {page}: {n} row(s) updated")
        total += n
    print(f"Done. {total} total row(s) changed.")


if __name__ == "__main__":
    main()
