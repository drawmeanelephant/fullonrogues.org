#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
BORIS_BIN=${BORIS_BIN:-./bin/boris}
CONTENT_DIR=${CONTENT_DIR:-content}
THEME=${THEME:-themes/cantilever}
DIST_DIR=${DIST_DIR:-dist/cantilever}
SITE_URL=${SITE_URL:-https://fullonrogues.org}
BORIS_JOBS=${BORIS_JOBS:-1}

cd "$ROOT"

python3 scripts/rogue_ids.py --root "$CONTENT_DIR" --map metadata/id-map.jsonl
python3 scripts/audit_markdown_links.py "$CONTENT_DIR"

"$BORIS_BIN" \
  --input "$CONTENT_DIR" \
  --theme "$THEME" \
  --html-dir "$DIST_DIR" \
  --sitemap \
  --site-url "$SITE_URL" \
  --static-dir static \
  --layout-rule default id:index "$THEME/layouts/home.html" \
  --layout-rule default glob:changelog/* "$THEME/layouts/compact.html" \
  --layout-rule default glob:posts/* "$THEME/layouts/compact.html" \
  --jobs "$BORIS_JOBS"

# RSS and llms.txt are standalone export modes and cannot share an HTML-mode
# invocation; each writes directly into the HTML target after the main build.
"$BORIS_BIN" --input "$CONTENT_DIR" --llms-path "$DIST_DIR/llms.txt" --quiet
"$BORIS_BIN" --input "$CONTENT_DIR" --rss --rss-path "$DIST_DIR/rss.xml" \
  --site-url "$SITE_URL" \
  --rss-title "Full On Rogues" \
  --rss-description "Guild archive updates from Full On Rogues" \
  --rss-limit 50 --quiet

python3 scripts/enrich_html_head.py --dist "$DIST_DIR" --content "$CONTENT_DIR" --site-url "$SITE_URL"

python3 scripts/audit_html_ids.py "$DIST_DIR"

if [[ -f "$DIST_DIR/_boris/proof/checks.json" ]]; then
  bad_checks=$(jq -r '[.checks[] | select(.status != "passed" and .status != "not-applicable")] | length' "$DIST_DIR/_boris/proof/checks.json")
  if [[ "$bad_checks" -ne 0 ]]; then
    echo "Full On Rogues publication checks failed: $bad_checks check(s) are not green." >&2
    exit 1
  fi
fi

echo "Full On Rogues build passed: $DIST_DIR"
