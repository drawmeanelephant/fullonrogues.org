# Claude Mission & Repository Mandates

## Repository Goal
Maintain and extend the **Full On Rogues** (`fullonrogues.org`) archive using the **Boris** static compiler.

## Core Rules
1. **Engine**: Static site output is rendered by Boris. Do not add JavaScript frameworks or static site generators (Vite, Next, Astro, Eleventy, etc.).
2. **Schema Integrity**: Maintain form-based ID schema (`ROG-XXXX`, `TAC-XXXX`, `GEAR-XXXX`, `RREF-XXXX`, `RGDE-XXXX`, `RREL-XXXX`, `RCHG-XXXX`).
3. **Graph Integrity**: All satellites must specify a valid trunk `parent`.
4. **Verification Gate**: `./bin/validate_graph.sh` must succeed clean before any release or commit.
