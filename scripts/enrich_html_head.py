#!/usr/bin/env python3
"""Inject per-page SEO head tags into the built HTML target.

Boris layouts accept a fixed marker whitelist only, so frontmatter values
like `summary` and `published_at` cannot be templated directly. This script
runs after the Boris HTML build and enriches each page's <head> from the
content frontmatter: meta description, canonical URL, Open Graph and Twitter
tags, and RSS autodiscovery. It also de-duplicates the homepage <title> and
strips the 404 page from sitemap.xml.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

SITE_NAME = "Full On Rogues"
DEFAULT_DESCRIPTION = "The archive of Full on Rogues, Feathermoon's premier end-page reading guild, 2007-2012."
OG_IMAGE_PATH = "assets/images/WoWScrnShot_042411_233824.jpeg"

FIELD_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")
TITLE_ELEMENT = re.compile(r"<title>(.*?)</title>", re.DOTALL)


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = FIELD_LINE.match(line)
        if not match:
            continue
        key, value = match.groups()
        value = value.strip()
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            value = value[1:-1]
        fields[key] = value
    return fields


def collect_records(content_root: Path) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for source in sorted(content_root.rglob("*.md")):
        rel = source.relative_to(content_root).with_suffix(".html").as_posix()
        records[rel] = parse_frontmatter(source)
    return records


def canonical_url(site_url: str, rel: str) -> str:
    if rel == "index.html":
        return f"{site_url}/"
    return f"{site_url}/{rel}"


def head_block(site_url: str, rel: str, fields: dict[str, str], has_rss: bool, has_og_image: bool) -> str:
    title = fields.get("title", SITE_NAME)
    description = fields.get("summary") or DEFAULT_DESCRIPTION
    published_at = fields.get("published_at")
    is_error_page = rel == "404.html"
    og_type = "article" if published_at else "website"

    tags = [
        f'<meta name="description" content="{html.escape(description, quote=True)}">',
    ]
    if not is_error_page:
        url = canonical_url(site_url, rel)
        tags.append(f'<link rel="canonical" href="{html.escape(url, quote=True)}">')
        tags.append('<meta property="og:site_name" content="Full On Rogues">')
        tags.append(f'<meta property="og:type" content="{og_type}">')
        tags.append(f'<meta property="og:title" content="{html.escape(title, quote=True)}">')
        tags.append(f'<meta property="og:url" content="{html.escape(url, quote=True)}">')
        tags.append(
            f'<meta property="og:description" content="{html.escape(description, quote=True)}">'
        )
        tags.append('<meta name="twitter:card" content="summary_large_image">')
    if published_at:
        tags.append(
            f'<meta property="article:published_time" content="{html.escape(published_at, quote=True)}">'
        )
    if has_og_image and not is_error_page:
        image_url = f"{site_url}/{OG_IMAGE_PATH}"
        tags.append(f'<meta property="og:image" content="{html.escape(image_url, quote=True)}">')
        tags.append(f'<meta name="twitter:image" content="{html.escape(image_url, quote=True)}">')
    if has_rss and not is_error_page:
        rss_url = f"{site_url}/rss.xml"
        tags.append(
            '<link rel="alternate" type="application/rss+xml" '
            f'title="{SITE_NAME}" href="{html.escape(rss_url, quote=True)}">'
        )
    return "\n".join(tags)


def enrich_page(path: Path, site_url: str, rel: str, fields: dict[str, str], has_rss: bool, has_og_image: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    if 'rel="canonical"' in text:
        return False
    if "</head>" not in text:
        raise ValueError(f"{rel}: no </head> element found")
    title_match = TITLE_ELEMENT.search(text)
    if title_match and title_match.group(1).strip() == f"{SITE_NAME} · {SITE_NAME}":
        text = TITLE_ELEMENT.sub(f"<title>{SITE_NAME}</title>", text, count=1)
    text = text.replace("</head>", head_block(site_url, rel, fields, has_rss, has_og_image) + "\n</head>", 1)
    path.write_text(text, encoding="utf-8")
    return True


def strip_sitemap(path: Path, excluded: set[str]) -> int:
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"<url>.*?</url>", text, re.DOTALL)
    removed = 0
    for block in blocks:
        loc = re.search(r"<loc>(.*?)</loc>", block)
        if loc and any(loc.group(1).endswith(suffix) for suffix in excluded):
            text = text.replace(block + "\n", "", 1)
            removed += 1
    if removed:
        path.write_text(text, encoding="utf-8")
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True, help="Built HTML target directory")
    parser.add_argument("--content", type=Path, default=Path("content"))
    parser.add_argument("--site-url", default="https://fullonrogues.org")
    args = parser.parse_args()

    dist = args.dist.resolve()
    if not dist.is_dir():
        print(f"Enrich HTML head: error: {dist} is not a directory", file=sys.stderr)
        return 2

    records = collect_records(args.content.resolve())
    has_rss = (dist / "rss.xml").exists()
    has_og_image = (dist / OG_IMAGE_PATH).exists()
    enriched = 0
    failures: list[str] = []
    for path in sorted(dist.rglob("*.html")):
        rel = path.relative_to(dist).as_posix()
        if rel.startswith("_boris/"):
            continue
        try:
            if enrich_page(path, args.site_url.rstrip("/"), rel, records.get(rel, {}), has_rss, has_og_image):
                enriched += 1
        except ValueError as error:
            failures.append(str(error))

    sitemap = dist / "sitemap.xml"
    removed = strip_sitemap(sitemap, {"/404.html"}) if sitemap.exists() else 0

    if failures:
        print("Enrich HTML head: error:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print(f"HTML head enrichment: {enriched} page(s) enriched; sitemap entries removed: {removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
