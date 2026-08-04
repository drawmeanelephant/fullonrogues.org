# Operational Guide for Coding Agents

This repository is **Full On Rogues** (`fullonrogues.org`), a static archive compiled using **Boris** and deployed to Cloudflare Pages at `https://fullonrogues.org`.

This document is the canonical operational guide for all AI coding agents working in this repository.

---

## 1. Core Operating Context

* **Architecture**: Full On Rogues is a production Boris site—**not** an Astro, Node, or JavaScript project.
* **Public URL**: `https://fullonrogues.org`
* **Compiler**: Boris is an external Zig static site compiler, provided locally or in execution environments via `BORIS_BIN`.
* **Helper Scripts**: Python scripts in `scripts/` perform bounded validation, auditing, metadata processing, and publishing tasks.
* **Authoring Tree**: `content/` is the canonical source of record for all rogue profiles, tactics, and equipment records.
* **Production Theme**: `themes/cantilever/` houses the production design and layout templates.
* **Generated Outputs**: `dist/`, `publish/`, `site/`, and local compiler binaries (`bin/boris*`) are build artifacts and must never be committed to git.

---

## 2. Mandatory Pre-Task Workflow

Before executing any substantive changes:

1. Inspect current workspace state: `git status`
2. Read project governance files:
   * `README.md`
   * `rules.md`
   * `metadata/id-policy.json`
3. When editing or creating content, inspect nearby records to maintain voice and layout consistency.
4. Preserve unrelated work in progress.

---

## 3. Primary Execution Commands

Use these scripts for local workflow, validation, and publishing:

* `./preview.sh`: Builds the site with Boris and launches a local preview server on port 8000.
* `./bin/validate_graph.sh`: Validates graph relationships, trunk/satellite structures, and metadata constraints.
* `./scripts/rogue-build.sh`: Runs the production build pipeline using Boris and theme templates.
* `./scripts/rogue-publish.sh`: Prepares and verifies deployment artifacts for production release.

---

## 4. Frontmatter & Schema Rules

Boris enforces a **closed and constrained** frontmatter schema.

* **Forbidden**: Do **not** introduce arbitrary YAML keys, legacy framework metadata, `updatedAt` fields, JSX/MDX components, executable expressions, or generic HTML components into record files.
* **Strict Schema**: Only key-value attributes recognized by the Boris compiler frontmatter schema are permitted (`id`, `title`, `parent`, `status`, `tags`, `relations`). Unknown keys will trigger build or validation failures.

---

## 5. Identity, Graph Structure & Hierarchy

* **Canonical Identifiers**: Preserve existing canonical IDs and the identity map (`metadata/id-policy.json`). Never silently rename, renumber, or reuse IDs.
* **Structural Hierarchy**: Hierarchy is declared strictly using `parent`.
* **Semantic Connections**: Non-hierarchical relationships use Boris `relations`.
* **Trunk & Satellite Model**:
  * Collection root pages function as **Trunks** (`rogues`, `tactics`, `gear`, `reference`, `guides`, `releases`, `changelog`).
  * Individual records function as **Satellites** (e.g. `rogues/ROG-0001`).

---

## 6. Completion & Verification Protocol

* Always run `./bin/validate_graph.sh` before declaring any task complete.
* When reporting completion to maintainers, output exact commands executed and their specific validation results.
