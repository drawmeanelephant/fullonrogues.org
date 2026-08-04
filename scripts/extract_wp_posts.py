#!/usr/bin/env python3
"""Extract WordPress posts from local MariaDB container into Boris Markdown files."""

import json
import re
import subprocess
from pathlib import Path

# SQL query to get published posts
SQL = """
SELECT ID, post_date, post_title, post_name, post_content, post_type
FROM for_posts
WHERE post_type IN ('post', 'topic', 'page', 'testimonial')
  AND post_status = 'publish'
ORDER BY post_date ASC;
"""

def run_query(sql):
    cmd = [
        "docker", "exec", "-i", "wp-local-db-1",
        "mariadb", "-u", "root", "-proot_password", "wordpress",
        "-N", "-e", sql
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    rows = []
    for line in res.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 6:
            rows.append({
                "id": parts[0],
                "date": parts[1],
                "title": parts[2],
                "slug": parts[3],
                "content": parts[4],
                "type": parts[5],
            })
    return rows

def html_to_markdown(html):
    if not html:
        return ""
    text = html.replace("\\n", "\n").replace("\\r", "")
    # Remove wp paragraph tags
    text = re.sub(r'</p>\s*<p>', '\n\n', text)
    text = re.sub(r'<p>', '', text)
    text = re.sub(r'</p>', '\n\n', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    # Headings
    text = re.sub(r'<h[1-6]>(.*?)</h[1-6]>', r'## \1\n', text)
    # Strong & em
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)
    text = re.sub(r'<i>(.*?)</i>', r'*\1*', text)
    # Links
    text = re.sub(r'<a\s+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text)
    # Strip remaining HTML tags except markdown clean text
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def main():
    root = Path(__file__).parent.parent / "content" / "posts"
    root.mkdir(parents=True, exist_ok=True)
    
    rows = run_query(SQL)
    print(f"Discovered {len(rows)} published posts from database.")
    
    count = 0
    for idx, row in enumerate(rows, 1):
        title = row["title"].strip() or f"Post {row['id']}"
        # Clean title quotes
        clean_title = title.replace('"', '\\"')
        form_id = f"POST-{idx:04d}"
        entity_id = f"posts/{form_id}"
        
        content_md = html_to_markdown(row["content"])
        date_str = row["date"].split()[0] if " " in row["date"] else row["date"]
        
        md_text = f"""---
title: "{clean_title}"
id: {entity_id}
parent: posts
status: published
tags: ["archive", "legacy", "{row['type']}"]
---

# {title}

*Published: {date_str}*

{content_md}
"""
        out_path = root / f"{form_id}.md"
        out_path.write_text(md_text, encoding="utf-8")
        count += 1
        print(f"  Wrote {out_path.name}: {title[:40]}")
        
    print(f"Successfully extracted {count} posts to {root}")

if __name__ == "__main__":
    main()
