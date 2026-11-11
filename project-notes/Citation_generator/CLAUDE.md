# Citation_generator (RecAI): project rules for Claude

Read the top-level `../CLAUDE.md` first. This file adds the rules that apply only to this project.

## What this project is

RecAI (internal name Citation_generator, product names ProfileIQ and RecruitMind IQ appear in code) is Estuate's recruiting assistant: resume upload, search with citations, chat, screening against a job description, resume conversion, job requisitions, and a Claude MCP connector. Owner: Kishore Kunal. Original developer: Akshay Patil.

The owner decided on 2026-11-05 to rebuild it where that is better and cheaper, keeping its intent. Phase 0 security fixes on the current code run in parallel with the rebuild design.

## Read at the start of a session

`STATUS.md`, last 10 entries of `HISTORY.md`, `DECISIONS.md`, `PLAN.md`. Word deliverables are in `docs/deliverables/`.

## Folder map

- `mcp-code/citation_generator/`: the Git repository (the application, Docker stack, schema baseline, tests).
- `backups-and-extra-files/`: a full production database backup with real data. Sits outside Git. Never copy it into a repository, never print its contents. Extract structure only (`pg_restore --schema-only`).
- `docs/deliverables/`: Word documents for stakeholders. `docs/archive/`: superseded material. `docs/`: original inputs (the earlier AWS quote PDF, the registration briefing).
- `reviews/`: copies of the entries Claude posts to the shared review folder.
- `activities/`: step-by-step records of setup and change activities.

## Git rules

- `origin` = the Estuate repository `https://github.com/kuruestuate007/Citation-Generator-01.git`. `akshay` = Akshay's repository, read-only upstream. Never push to `akshay`.
- All work goes on our own branches named `estuate/<topic>`, created with `git switch -c estuate/<topic> --no-track <base>`. Never commit to `main`, `feature/mcp-connector` or any branch Akshay created.
- Current branches: `estuate/local-bringup` (Docker stack), `estuate/phase0-security` (security fixes, from `local-bringup`). Local only until the owner approves a push.
- Commit messages end with the co-author line the harness gives.
- Dependency upgrades and architecture changes are separate branches from security fixes, so test results stay interpretable (ADR-007).

## Local stack

From `mcp-code/citation_generator/`: `docker compose up -d` gives PostgreSQL 17 and the backend on 127.0.0.1:8000. Config is in a git-ignored `.env` (generated throwaway values; outside AI keys are blank). Security regression checks: `python tests/security/phase0_checks.py`. On Windows Git Bash put `MSYS_NO_PATHCONV=1` before `docker compose exec -w /app ...`.

## Working with ChatGPT (Codex)

- Shared folder: `C:\Users\kikunal\Documents\ChatGPT\Citation-genrator\shared-review\`. Protocol in its `README.md`. Claude writes only `claude.md` (entries `CLAUDE-001`...) and keeps copies in `reviews/`.
- Codex's separate checkout `C:\Users\kikunal\Documents\ChatGPT\Citation-genrator\recai` is a read-only review copy. Codex works in `...\Citation-genrator\recai-rebuild`. Claude owns all application-code edits in the Estuate clone.

## Project-specific cautions

- The production backup holds real candidate data (13 users, 189 files, 339 screening rows at 2026-11-05): personal data, handle accordingly.
- The production database has a table `core.mcp_oauth_tokens` that no repository branch uses: a newer, unpublished MCP version has run against it. Ask Akshay before assuming anything about what is live.
- PyMuPDF is AGPL or commercial: needs a legal decision before a public hosted release.
- Anthropic's Usage Policy (12 November 2026) treats candidate screening and ranking as high-risk (qualified human review and disclosure). Keep screening out of any public release until reviewed.

## Document format (see top-level rule)

Human-facing documents are Word (Excel for models; PDF or PowerPoint only after asking). Codex's human-facing files in `recai-rebuild/` (`architecture-gates.md`, `threat-model.md`, `questions-for-akshay.md`) must be converted to Word. The rebuild code and its README stay in the folder `recai-rebuild/`, which the owner chose as the home of the rebuild (it is not yet a Git repository; versioning is still to be decided).
