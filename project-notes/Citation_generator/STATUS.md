# Status: Citation_generator (RecAI)

Last updated: 2026-11-05, evening. A new session starts here, then HISTORY.md (last 10 entries), DECISIONS.md, PLAN.md.

## Session handover, 2026-11-11 (read this first in a new session)

- **Repositories (all private, Estuate GitHub account `kuruestuate007`):**
  - `Citation-Generator-01` (the old app): branches `main` 7f8ffed, `feature/mcp-connector` 95ef749 (both Akshay's), `estuate/local-bringup` 2a22f0a, `estuate/phase0-security` b1f1033 (38 of 38 security checks). Local clone: `mcp-code/citation_generator`, remote `origin`; Akshay's repo is remote `akshay` (read-only).
  - `recai-rebuild` (the rebuild): `https://github.com/kuruestuate007/recai-rebuild`, branch `main`. Local folder: `Citation_generator/recai-rebuild`. Pushed 2026-11-11 (first commit 36255cc). A snapshot of these continuity notes is committed in it under `project-notes/` as a backup (the source of truth stays in `Citation_generator/`).
- **Working agreement with ChatGPT in `recai-rebuild`:** Codex works on branches named `codex/<topic>` and commits locally; Claude reviews, merges to `main` and pushes (the owner's GitHub sign-in is used by Claude's pushes). Only the owner enters credentials. Claude owns edits in the old app clone.
- **Decided by the owner:** Option A serverless on AWS; Haiku is the only generative model at launch (CODEX-020); feature-gated release one (PLAN.md); practice AWS account profile `glencore-erm` (Estuate-owned), Ohio `us-east-2`; testing rule in top-level CLAUDE.md (simulate first, cents, build and destroy per test, API keys only at the end); format rule (Word for anything a person reads); layout rule (everything about this project stays in `Citation_generator/`); cost check without infracost (our price-list estimator).
- **Waiting on the owner:** open Codex's Word drafts (`docs/deliverables/RecAI Rebuild Plan.docx` and four drafts in `recai-rebuild/`) and say if they look right; his AWS sign-in when L1 is ready; later: message to Akshay, legal items (PyMuPDF, privacy policy), Seema's commitment answer, archiving stale top-level research files.
- **Next for Claude, in order:** (1) fix the unencrypted alerts SNS topic (`infra/guardrails.tf` 94-96, use `alias/aws/sns`) and switch `infra/up.ps1` from infracost to `cost/estimate.py`; (2) run the offline L0 checks (validate, tflint, trivy, mock-plan estimate, policy checks for cost traps); (3) OAuth sign-in page fix in the old app (escape output, bind sign-in to the authorize request, use client id, require redirect match), then legacy upload-row scan; (4) review Codex's code (`slice/app.py`, `extract.py`, `aws_reads.py`, `acceptance.py`, `benchmark_http.py`) and its threat model, which Claude has not done; (5) update the rebuild Word document with the per-feature table and Codex's corrections; (6) L1 on AWS only after the owner approves the estimate for the exact plan.

## One-paragraph state

Kishore owns RecAI now. We are doing two things in parallel: (1) Phase 0 security fixes on the current code, on branch `estuate/phase0-security`, and (2) designing a cheaper, safer, serverless rebuild on AWS (ADR-008 direction). The local Docker stack works. Phase 0 is DONE and committed locally (`d72bc4b`): 38 of 38 security checks pass (13 of 26 failed before the first fixes; the converted-resume checks were also proven red without their fix). The rebuild design document v1 is written (`docs/deliverables/RecAI-Rebuild-Understanding-Architecture-Cost.docx`, with three diagrams; facts in `docs/rebuild-design-notes.md`, build scripts in `activities/2026-11-05-rebuild-design/`); it needs review against Codex's CODEX-008 and its threat model, and the numbers are estimates until a prototype measures them. ChatGPT (Codex) is working in parallel on tasks I assigned.

## Done (verified)

- **AWS cost package for Seema**: `docs/deliverables/AWS-Hosting-Plan-and-Cost-FINAL-RecAI-MCP.docx`, sent by Kishore 2026-11-04. t3.large in Ohio, Postgres on the VM, S3 for files and backups, about $73/month on-demand or about $50 with a 1-year commitment, plus about $84/month outside AI services (Akshay's low-end estimate). Commitment question pending with Seema (ADR-002).
- **Analysis and security review**: `docs/deliverables/RecAI-Analysis-Serverless-Security-Plan.docx` (static review of commit 95ef749).
- **Estuate repo**: `main` and `feature/mcp-connector` pushed to `https://github.com/kuruestuate007/Citation-Generator-01.git` (remote `origin`; Akshay's repo is remote `akshay`). Default branch `main`; anonymous request returns 404 (consistent with private; owner to confirm in GitHub).
- **Local stack**: `mcp-code/citation_generator`, `docker compose up -d` gives PostgreSQL 17 and the backend on 127.0.0.1:8000. Real schema baseline `db/schema/001_baseline.sql` extracted structure-only from the production backup (data never read). Fresh DB builds cleanly. ERM kind cluster was stopped (not deleted) to free resources: `docker start erm-local-control-plane erm-local-worker` to resume.
- **Findings reproduced by running them**: anonymous `POST /mcp` `tools/call` returns another user's data when `MCP_DEV_MODE` is unset (code default); report download, chat history read, same-name upload overwrite and `../` filename traversal confirmed with two users. Batch delete was wrongly reported earlier and is withdrawn (admin-only, 403). `.env` overrides real environment variables (`load_dotenv(override=True)`).
- **Production database facts (counts only)**: 13 users, 189 files, 339 screening rows, 47 batches, 93 chat threads. Table `core.mcp_oauth_tokens` exists with 1 row but no repository branch uses it: an unpublished newer MCP version has run against this data.
- **Pricing verified from AWS's own price list (Ohio)**: see `docs/rebuild-design-notes.md`.
- **Folder restructure (2026-11-05)**: everything about this project now lives inside `Citation_generator/`. Top level (`../`) keeps only shared files (CLAUDE.md, PROJECTS.md, POC-STANDARDS.md, activities/_TEMPLATE, general research).

## Phase 0: done (commit d72bc4b, local only)

- Branch `estuate/phase0-security` = `2a22f0a` (tests) + `3b8f111` (real schema baseline, PostgreSQL 17) + `d72bc4b` (fixes). Not pushed.
- `python tests/security/phase0_checks.py` (from `mcp-code/citation_generator`, stack up): 26 passed, 0 failed. Each area asserts the specific denial and the owner's success. Fixed: MCP authentication (Bearer tokens from `/oauth/token` only; no dev mode, dev key, loopback, cookie or web-token acceptance), report download ownership, chat read and write ownership (404; database layer refuses non-owner), both upload routes (per-user folders, sanitised names), converter lookup, `.env` no longer overrides the environment. Admin-only batch deletion unchanged and tested.
- Results and the open-issue list were posted as CLAUDE-006 (copy in `reviews/`); Codex was asked to review the commit independently.
- Added after the first commit: converted-resume download and preview now check ownership and output names are per user (commit 1b4204a). Still open after Phase 0 (follow-up, ranked by Claude and Codex): same report name shared across users; password in URL; no login throttling; CSRF and CORS; resume-text prompt injection; raw error text; in-memory tokens with 4 workers; `core.mcp_oauth_tokens` unexplained. Upload success paths return HTTP 500 locally only because outside keys are not configured.
- Resume steps if anything changes: `git switch estuate/phase0-security`, `docker compose up -d`, run the checks, see `activities/2026-11-05-phase0-security/STEPS.md`.

## Codex review of Phase 0 (CODEX-011, read 2026-11-05) and what I verified

Claude read CODEX-001 to 014 in full. Not done: reading or running Codex's code in `recai-rebuild/slice/` (connector, ingest, acceptance, benchmark runner), reading `architecture-gates.md` and `threat-model.md`, and rerunning its benchmark. Do these next.

CODEX-011 findings, each confirmed by a static read of `mcp-code/citation_generator` (not yet reproduced by running):
- **Bulk screening route, P0:** `routes/folderprocesser.py` line 344 takes `job_id` from the client as the batch id, loads the batch with no owner check (lines 346-365), and the cumulative read at 426-439 returns all rows of that batch (`WHERE batch_id = $1`, no user filter). A user who knows another batch id can read its rows and attach results to it.
- **Report name in the file path, P0:** the client-supplied `report_name` (lines 367-369) becomes the workbook path (writer around line 406 and `routes/endpoint/bulk_processing.py` 227-288), so `../` names can write an XLSX outside `screening_reports`, and equal names share one file. Related sinks in `db/jobendpoint.py`.
- **OAuth sign-in page, P0 before any exposure:** `mcp_server/oauth.py` lines 205-214 put `state` and `code_challenge` into HTML without escaping (reflected injection); the sign-in POST does not bind to the original authorize request; `client_id` is accepted but unused; redirect check is optional if omitted.
- **Legacy rows, P1:** existing `core.files` rows may share one flat path; the new per-user folders do not fix those. Needs a duplicate-path scan on production data and a migration.
- Codex also found nothing wrong with the MCP dispatch paths, the chat ownership check, or slash and backslash traversal on new upload paths. The converter finding was already fixed in 1b4204a.

Plan for next session on `estuate/phase0-security` (tests first, each asserting denial and success, then fix, then prove red without the fix): (1) bulk route batch-id ownership; (2) report names to generated owner-scoped file names, sanitise `db/jobendpoint.py` sinks; (3) OAuth: escape output, one-time server-side transaction bound to client, callback, state and S256; (4) legacy-row scan and migration plan. After each, post a CLAUDE entry and update this file.

## Fixes since the Codex review (2026-11-05, all local only until the GitHub sign-in is refreshed)

- Local commits on `estuate/phase0-security` not yet pushed: `1b4204a` (converted resumes ownership), `2fdb23c` (bulk route batch ownership and safe report name), and the converter regeneration fix (commit after it). `tests/security/phase0_checks.py` now has 38 checks, all passing. Each new check was shown red without its fix, except the report-name write check, which cannot fail locally without outside keys (so it is not proof by itself).
- Kishore pushed `estuate/phase0-security` on 2026-11-05 (confirm the remote head equals local `b1f1033` with `git ls-remote origin`).
- Fixed from CODEX-011 and 015: bulk route batch id ownership (P0), report name path (partly: traversal closed; two users with the same report name still share one file), converter regeneration overwrite (P0).
- Still open from the Codex reviews: OAuth sign-in page (escape output, bind the sign-in to the original authorize request, use client id, require redirect match); basename-based converter ownership and shared legacy file names (needs a data migration and opaque artifact ids); legacy upload rows that share one path; the chat query check accepts a 500 as a pass (needs a model stub); other write sinks in `db/jobendpoint.py`; same report name shared across users.
- My own review of Codex's slice is partial: read `recai-rebuild/slice/core.py` and CODEX-011 to 015 only. Observations on core.py: search results are not relevance-ranked (`results[:limit]` takes the first matches in insertion order), no document-level ACL inside a tenant (Codex lists this itself), locking is in-process only, retry and delete are not durable. Not yet reviewed or run: `app.py`, `extract.py`, `aws_reads.py`, `acceptance.py`, `benchmark_http.py`, `threat-model.md`, `architecture-gates.md`.

## Scope direction (CODEX-016, owner, 2026-11-05)

Release one is feature-gated, not capped at evidence search: include as much of Akshay's functionality and useful additions as can be proved accurate, secure, reliable and policy-compatible. Gates are listed in PLAN.md. Screening and ranking stay off the public tools until the policy gates are proved; video interviews excluded. More features mean more attack surface and more cost, so each gets its own tests and cost line in the rebuild document.

## AWS build plan (owner, 2026-11-05): cost first, one-click build and destroy

The owner pushed the Phase 0 branches and asked to begin the full build and AWS setup, with these rules:
1. **Know the cost before anything is created.** Terraform plan only (creates nothing), then `infracost` on that plan (already on this machine: `D:	ools-and-sw\infracost`), compared with `docs/rebuild-design-notes.md`; the owner approves the numbers; only then apply.
2. **One-click build and one-click destroy.** Terraform with two wrapper scripts (up and down). Everything tagged `project=recai-rebuild`; destroy must leave nothing behind (buckets force-destroyed, no customer-managed KMS keys because they cannot be deleted instantly, no retained log groups, secrets with zero recovery window). After destroy, verify with a tag-based resource search that nothing remains.
3. **Safety guards in the code:** `allowed_account_ids` pinned to the owner's account, region Ohio, an AWS Budget with alerts at 50, 80 and 100 percent of the cap plus an automatic stop, no NAT gateway, no database server, no public IP.
4. **Order:** plan, infracost, owner approval, apply, run the HTTP acceptance suite against the deployed endpoint, test with a real Claude client using synthetic data, destroy, verify empty. Repeat until the cycle is boring.
5. **AWS profile (found 2026-11-05):** the only profile on this machine is `glencore-erm` (default region eu-central-2, sign-in with `aws login --profile glencore-erm`, documented in `D:	ools-and-sw\_docsccountsws-cli-signin.md`). Owner confirmed 2026-11-05: it is an Estuate-owned account given to him for practice, so it is fine to use for RecAI. NOT BLOCKING (owner, 2026-11-05: he will sign in to AWS himself once the setup is ready; build everything offline with profile, region and account id as variables, default Ohio, apply refuses to run until the profile and pinned account id are set). Account question answered (Estuate practice account, fine to use). Still do: pin the account id in the Terraform and tag everything `project=recai-rebuild`, so a destroy can never touch other practice resources in that account (for example anything left from ERM). DECIDED by the owner 2026-11-05: region is Ohio (`us-east-2`), where prices and S3 Vectors and Bedrock Titan availability were verified. The Terraform sets the region explicitly, so the profile's Zurich default does not matter. (Earlier note, for the record:) prices and Bedrock and S3 Vectors availability were verified for Ohio only, not for eu-central-2. No AWS command has been run.
6. **Still needed from the owner before the first apply (not credentials):** the AWS profile name to use, the account id to pin, the monthly cap, and where the rebuild code lives (see open question).
7. **Decided by the owner:** the rebuild lives in `recai-rebuild/` (a plain folder inside the project, not yet a Git repository). Still to decide: versioning it (recommended: a new Estuate GitHub repository or branch) before the code grows.
- Codex was assigned the Terraform, wrapper scripts, budget guard and cost plan (CLAUDE-011); Claude reviews every plan and cost report before the owner sees it.

## Format rule (owner, 2026-11-05)

Anything a person reads is a Word document (Excel for models; PDF or PowerPoint only after asking). Markdown only for files the assistants alone use. Codex's human-facing .md files (`release-feature-gates.md`, `architecture-gates.md`, `threat-model.md`, `questions-for-akshay.md`) are to be converted to Word. Rule is in the top-level `CLAUDE.md`.

## Infracost key (owner, 2026-11-05)

The owner's free infracost allowance on the Estuate email ended. He will register again himself with another email by running `infracost auth login` in his own terminal (browser sign-in); Claude must never read or print the key or the credentials file, and must not run `infracost configure get api_key`. After he confirms, check with `infracost breakdown` on the Terraform plan. Backup plan if limits hit again: a small estimator that reads the Terraform plan and prices resources from AWS's public price list (scripts in `activities/2026-11-05-rebuild-design/awsprice*.py`), plus a usage file for usage-based items.

## Cost estimator (built 2026-11-05, no accounts or keys needed)

- `recai-rebuild/cost/estimate.py` prices a scenario in Ohio from a usage file (and, once it exists, a Terraform plan converted with `terraform show -json`). Flags cost traps (NAT gateway, interface endpoints, customer KMS keys, database servers, always-on instances, Elastic IPs) and unknown resource types. Each price is marked verified (AWS price list or Anthropic table, 2026-11-05) or unverified. Word report with `--out`.
- Results, estimates only: pilot (evidence search, 2,000 documents, 10,000 searches) about **$2.06 per month** (about $9 with a firewall); full internal product, lean (Haiku 5.5 first, batch, cached prompts) about **$23.63 per month including a $7 firewall** (about $16.6 without), of which about $9.7 is priced with still-unverified list prices (WAF, CloudWatch, S3 standard, SQS). Word report: `docs/deliverables/RecAI-Cost-Estimate-Pilot-Ohio.docx`.
- Not yet done: plan-file mode has not been run against a real Terraform plan; the unverified prices need checking against AWS's price list; Lambda and CloudFront free allowances are ignored (conservative) unless `apply_free_tier` is set.

## Infrastructure scaffold review (CODEX-019, Claude spot review 2026-11-05)

- Scaffold in `recai-rebuild/infra/` (Terraform, provider 6.72.0, `up.ps1`, `down.ps1`, offline tests). Offline only; nothing applied; no AWS call made. Meets the guards: pinned account, no NAT, no database server, no WAF, no customer KMS key, paused runtime, typed approval, budget alerts.
- Claude ran `tflint` (clean) and `trivy config` (one HIGH: alerts SNS topic unencrypted, `guardrails.tf:94-96`; fix with `alias/aws/sns`). `up.ps1` still uses infracost; to be switched to `cost/estimate.py` (CLAUDE-017).
- **Owner's testing rule (in top-level CLAUDE.md):** practice account, simulate first, spend cents (about $1 max), build and destroy per test, API keys only for the final end-to-end run. Test ladder L0 offline, L1 infra with paused runtime, L2 runtime with simulated models, L3 real Claude client with keys.
- Open for the owner: create a separate private Estuate repository for `recai-rebuild` (Codex proposal; Claude agrees); open the Word drafts Codex generated (not rendered, LibreOffice missing).

## Versioning of the rebuild and the Terraform files (2026-11-05)

- `recai-rebuild/` is now a local Git repository (branch `main`, first commit made by Claude; gitleaks clean; 33 files). `.gitignore` excludes Terraform state, plans, `.terraform/`, `*.tfvars`, env files, keys, virtual environments and generated Word reports; the provider lock file `.terraform.lock.hcl` IS committed. NOT pushed: the owner must create an empty private repository in the Estuate GitHub and give the URL; then `git remote add origin <url>` and `git push -u origin main` (needs his GitHub sign-in).
- Terraform state is never committed. Practice account: local state is acceptable because every test is destroyed before logging off; if the laptop dies mid-test, clean up by the `project=recai-rebuild` tag (the `down` script's tag search). Real PoC and publishing account: use a remote S3 backend (versioned, encrypted, lock file) created by a separate bootstrap stack that is not destroyed with the app stack.
- Outside any repository today (back these up): the project folder `Citation_generator/` (STATUS, HISTORY, DECISIONS, reviews, Word deliverables) and the production database backup with real candidate data (do NOT put the backup on GitHub; keep it only in approved, access-controlled storage).

## Next, in order

1. Read Codex's review of `d72bc4b` when it arrives and fix any bypass it finds (new commit on `estuate/phase0-security`).
2. Review the rebuild document v1 with the owner; reconcile with CODEX-008; update after Codex's threat model and cost workbook land.
3. Review Codex's deliverables as they land (benchmark CODEX-009 done; connector sign-in verdict, policy text, threat model, Terraform skeleton, acceptance tests, cost workbook assigned in CLAUDE-005).
4. Prototype the thin slice in Kishore's AWS account only after he approves (synthetic data only).

## Approvals and decisions (updated 2026-11-05, late)

- **Done:** pushed `estuate/local-bringup` (2a22f0a) and `estuate/phase0-security` (d72bc4b) to `origin` (Estuate repo). **Pending:** commit 1b4204a (converted-resume fix, 30 of 30 checks) is local only. GitHub access currently fails with a terminal/sign-in error (expired cached credential). Kishore must sign in again (for example run `git ls-remote origin` in his own terminal so the browser prompt opens), then run `git push origin estuate/phase0-security`. Remote now has `main`, `feature/mcp-connector` and those two.
- **Direction approved by Kishore:** private connector first and public listing later (ADR-003), modernise in waves after Phase 0 (ADR-007), serverless rebuild after a prototype (ADR-008). Treat these as accepted.
- **Live check:** Kishore is open to it. No AWS account is needed for a reachability check (it is a plain web request to the production host, presumed `recai.estuate.com`, not confirmed). Not done yet; limit it to reachability (`ping` or `initialize` on `/mcp`), never a data-returning call, and only after Kishore says go.
- **AWS prototype:** needs Kishore's AWS account and a budget cap, in Ohio, synthetic data only. Waiting for his go.
- **Deferred by Kishore (not blockers now):** message to Akshay, legal items (PyMuPDF, privacy policy), Seema's commitment answer, archiving the stale top-level research files.

## ChatGPT (Codex) state

- Review log: `C:\Users\kikunal\Documents\ChatGPT\Citation-genrator\shared-review\` (codex.md CODEX-001 to 009 read; my entries CLAUDE-001 to 005 posted, copies in `reviews/`).
- Codex delivered: CODEX-009 synthetic retrieval benchmark (60 profiles, 60 labelled queries) in `...\Citation-genrator\recai-rebuild\benchmark`. Baseline token-overlap search: 31.8% citation precision, 58.3% recall.
- Batch 1 (sign-in, policy, Akshay questions, PDF licence) is done; CODEX-011 (Phase 0 review), 012 (local MCP and ingest prototype), 013 (acceptance and retrieval results: phrase and alias search 66.7% citation precision / 100% recall against 31.8% / 58.3% for token overlap, false evidence still 6 of 12 empty cases) and 014 (threat model) have landed. Still assigned in CLAUDE-005, in order: threat model; Terraform skeleton (never applied); thin-slice acceptance tests; cost workbook; search comparison runs (after AWS approval).
- Codex does not edit application code; Claude owns all edits in the Estuate clone.

## Key facts for a new session

- Repo: `mcp-code/citation_generator`. Remotes: `origin` Estuate, `akshay` upstream. Work only on `estuate/<topic>` branches.
- Start stack: `docker compose up -d`. Reset DB: `docker compose down -v` then up. Admin login values are in the git-ignored `.env` (generated; never print).
- Windows Git Bash: prefix `MSYS_NO_PATHCONV=1` for `docker compose exec -w /app ...`.
- Scratch scripts live in the session scratchpad (temporary). Important ones are copied into `activities/` and `docs/` so they survive.
