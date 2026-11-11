# History

Append-only. Newest entries at the bottom. One entry per completed task.

## 2026-11-03

- Read the email context and the app code (branch `feature/mcp-connector`). Reviewed the AWS estimate from Sumit (c6g.xlarge, $107.28/month) and judged it oversized.
- Researched Anthropic's Connectors Directory: submission portal, OAuth rules, tool annotations, privacy policy, test account, Community vs Verified labels.
- Compared Ohio on-demand prices for about 19 instance types and verified the ARM compatibility of all 46 pinned Python packages.
- Produced several versions of the cost document in Word. Decisions along the way: t3.large chosen over t4g.large for safety, PostgreSQL on the VM, S3 for files and backups.

## 2026-11-04

- Corrected the RDS estimate (db.t4g.small about $26/month, not the micro size).
- Added Akshay's AI service estimate (about $84/month). Pinecone Standard has a $50 minimum, queried with Akshay.
- Verified the 1-year commitment rules against AWS documentation: not tied to one VM, fixed hourly amount, 7-day return window in the same calendar month, applied to the buying account first. Rewrote the commitment wording for Seema.
- Kishore sent the final email and document to Seema.

## 2026-11-05

- Kishore took ownership of the project.
- Independent static review of commit 95ef749. Confirmed ChatGPT's P0 findings (unauthenticated admin fallback, report download, batch delete, chat history, upload path) and added login throttling, CSRF and CORS, resume-text injection, error leakage and the missing tenant model.
- Noted that the branch's nginx config does not route /mcp, /oauth or /.well-known (live state unverified).
- Researched serverless options (S3 + CloudFront, Lambda, queue workers, Neon, Aurora scale-to-zero, pgvector). Concluded the saving is about $55/month, so move in stages and fix security first.
- Wrote `docs/deliverables/RecAI-Analysis-Serverless-Security-Plan.docx`.
- Created the root standards: CLAUDE.md, STATUS.md, HISTORY.md, DECISIONS.md, PLAN.md, POC-STANDARDS.md, activities template.
- Posted CLAUDE-001 to the ChatGPT shared review folder. Saved memory notes.
- Located ChatGPT's local branch `claude-mcp-publish-01` (clone under Documents\ChatGPT\Citation-genrator\recai). It sits at 95ef749 with no new commits, nothing to push.
- Ran Gitleaks 8.30.1 on both branches (redacted output): 4 hits, all the same dummy dev key in `documentation/mcp_server_guide.md`. Word and PDF files are not scanned by the tool.
- Renamed remotes in the project clone: Estuate repo is now `origin`, Akshay's is `akshay`. Created branch `estuate/local-bringup` off `feature/mcp-connector`. Rule recorded: work only on our own `estuate/<topic>` branches.
- Found schema drift: the code uses `core.bulk_screening_results`, `core.document_chunks` and `core.users.is_active`, none of which the repo SQL creates. Docker engine not running and only Python 3.14 on the laptop, so local bring-up goes through containers. Wrote Dockerfile, docker-compose.yml, .env.example, initdb scripts (untested) and committed locally.
- Docker started. Built the image (Python 3.12, all packages installed). First database start failed on the repo SQL; generated a draft schema (`docker/initdb/01-schema-draft.sql`) and patched missing columns. Backend and database now run locally; login, session, chat threads and file list work. Reproduced finding 1 by executing the code in the container. Committed on `estuate/local-bringup` (not pushed).
- Stopped the ERM kind cluster (two containers) to free CPU and memory; not deleted (19 days of platform setup inside).
- Read ChatGPT's CODEX-001 to 006 and its clone (no code changes there). Ran two-user checks locally: confirmed report download, chat history read, same-name upload overwrite and `../` path traversal; found my batch-delete finding wrong (admin-only route, 403) and corrected it publicly. Verified ChatGPT's Usage Policy claim against Anthropic's pages. Posted CLAUDE-002 and CLAUDE-003.
- Reproduced finding 1 over HTTP with the variable truly unset (anonymous `tools/call` returned another user's batch). Found `load_dotenv(override=True)` overrides real environment variables. Committed `tests/security/two_user_checks.py` on `estuate/local-bringup`.
- Created branch `estuate/phase0-security`. Found the supplied "db-schema" file is a full custom-format production backup with data; extracted structure only with `pg_restore --schema-only` in a PostgreSQL 17 container (data never read; row counts only). Built `db/schema/001_baseline.sql` (scratch tables and the default password removed), moved local Postgres to 17, committed (3b8f111). Fresh database builds cleanly; reproductions unchanged on the real schema. Found `core.mcp_oauth_tokens` in production with no matching code in any branch.
- Checked package versions: 15 of 46 pinned packages unused; `unstructured` blocks Python 3.14. Drafted ADR-007 (modernise in waves after Phase 0).
- Added remote `estuate` and pushed `main` (7f8ffed) and `feature/mcp-connector` (95ef749) to the Estuate-owned repo `kuruestuate007/Citation-Generator-01`. No force push. Akshay's remote and the server deployment were not changed.
- **Restructure (2026-11-05, evening):** at the owner's request everything about this project moved inside `Citation_generator/` (continuity files, reviews, activities, Word documents in `docs/deliverables/`); the top level keeps only shared files (CLAUDE.md, PROJECTS.md, POC-STANDARDS.md, activities/_TEMPLATE). Added a project-level CLAUDE.md.
- **Phase 0 (2026-11-05):** wrote `tests/security/phase0_checks.py` (red run 13 failed, 13 passed), applied the fixes with a scripted patch, caught and fixed one bug the tests exposed (missing `HTTPException` import turned a 404 into a 500), then 26 of 26 passed. Committed `d72bc4b` on `estuate/phase0-security` (local only). Posted CLAUDE-005 (assignments) and CLAUDE-006 (results, request for independent review). Read CODEX-007 to 010.
- Saved rebuild design facts (verified AWS prices, cost scenarios, options, outline) in `docs/rebuild-design-notes.md`; the rebuild Word document is still to be written.
- Wrote `docs/deliverables/RecAI-Rebuild-Understanding-Architecture-Cost.docx` v1 (three diagrams, old-against-new cost in three model scenarios, three options, what to prove, decisions needed) and ADR-008. Saved the build scripts in `activities/2026-11-05-rebuild-design/` so it can be regenerated.
- Pushed `estuate/local-bringup` and `estuate/phase0-security` to the Estuate repo (owner approved). Owner approved the direction (ADR-003, ADR-007, ADR-008 treated as accepted) and deferred the remaining open questions as non-blockers.
- Fixed converted-resume download and preview ownership and per-user output names; 30 of 30 checks pass; proved the new checks fail without the fix; committed as 1b4204a. The push failed (expired GitHub sign-in); pending Kishore's re-login. Posted CLAUDE-007 giving Codex a large build chunk (connector service, ingest worker, authorization layer, HTTP acceptance suite, benchmark run, commit review, cost workbook) in `recai-rebuild/`.
- Read CODEX-011 to 014. Verified by reading the code that the three headline findings of CODEX-011 are real (bulk route batch id, report name in path, unescaped OAuth page). Queued the fixes in STATUS.md. Codex's code in `recai-rebuild/slice/` not yet reviewed or run.
- Read CODEX-015. Fixed and tested (red then green): bulk route batch ownership and report-name traversal (2fdb23c), converter regeneration overwrite (next commit). 38 of 38 checks pass. Partial review of Codex's slice (core.py). Pushes pending the GitHub sign-in.
- Read CODEX-016: owner direction to include as much functionality as can be proved. Recorded as an amendment to ADR-003 and a feature-gate list in PLAN.md.
- Owner pushed the Phase 0 branches and asked to begin the full build and AWS setup, cost first, one-click build and destroy. Read CODEX-017 (slice now ranks exact matches above aliases, second subject in a tenant refused, tests pass). Recorded the AWS build plan in STATUS.md and assigned the Terraform and cost work to Codex (CLAUDE-011). No AWS call made yet.
- Owner chose `recai-rebuild/` as the home of the rebuild and set a format rule: human-facing documents are Word (Excel, PDF or PowerPoint only on request), Markdown only for assistant-only files. Added to the top-level and project CLAUDE.md and memory. Read CODEX-018 (executable release gates, delivered as .md, to be converted).
- Found the AWS profile name (`glencore-erm`, Zurich) from the owner's setup docs without any AWS call. Flagged that it appears to be a client account and that prices were verified for Ohio only; asked the owner which account and region to use. Pushed `estuate/phase0-security` verified on the remote (b1f1033).
- Owner said he will sign in to AWS once the setup is ready. Account and region questions stay open but do not block the offline build.
- Owner confirmed the `glencore-erm` AWS account is an Estuate practice account, fine for RecAI. Kept the safeguards (pinned account id, project tag). Region choice (Ohio verified vs Zurich unverified) still open.
- Owner chose Ohio (us-east-2) as the region. Cost numbers in `docs/rebuild-design-notes.md` stand.
- Owner's infracost free allowance ended; he will re-register himself and sign in with `infracost auth login`. Offered a price-list-based estimator as a backup.
- Built the price-list cost estimator (`recai-rebuild/cost/`) at the owner's request, because infracost's free allowance ends. Pilot about $2.06 per month, full lean product about $23.63 including a firewall. Estimates; plan mode untested.
- Added the practice-account testing rule to the top-level CLAUDE.md and memory. Read CODEX-019, spot-reviewed the infra scaffold (tflint clean, trivy one finding, up.ps1 still uses infracost), posted CLAUDE-017 with fixes and a staged test ladder.
- Initialised `recai-rebuild/` as a Git repository with a safe .gitignore (no Terraform state or secrets; lock file committed), gitleaks clean, first local commit. Push waits for the owner to create the private repository.
- **2026-11-11:** new session. Rebuilt state from STATUS.md and the repositories. Confirmed `Citation-Generator-01` remote and its four branches. Owner created `recai-rebuild` on GitHub; pushed `main` (36255cc). Wrote a session handover block at the top of STATUS.md, committed a snapshot of the continuity notes into the rebuild repo (`project-notes/`), and posted a complete handoff to ChatGPT (CLAUDE-018). Read CODEX-020 (Haiku-only launch plan, one-page Word plan).

