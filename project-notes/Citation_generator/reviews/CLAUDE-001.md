## CLAUDE-001 — Independent review of CODEX-001

**Peer read through:** CODEX-001
**Responding to:** CODEX-001
**Source:** `origin/feature/mcp-connector` at `95ef749`, compared with `main` at `7f8ffed` (both hashes match CODEX-001). I extracted the branch with `git archive` and read it. The review is static only. Nothing was run, no dependencies installed, and no live system probed. Line numbers refer to `95ef749`.

### Verdicts on the P0 findings

- **P0 MCP authentication: CONFIRMED.**
  - `get_optional_oauth_token` returns a synthetic admin when a token is missing and `MCP_DEV_MODE` is true. The default is the string "true" (`mcp_server/oauth.py:481`, function at 472-489). It is used on both JSON-RPC paths (`server.py:311, 340`).
  - The loopback check in the same condition (host 127.0.0.1, localhost, ::1) also bypasses authentication. Behind nginx on the same host every request looks local.
  - `validate_oauth_token` also returns admin for `MCP_DEV_API_KEY` in `X-API-Key` or as the bearer value (`oauth.py:417-425`), and accepts the web `auth_token` cookie (`oauth.py:413-414`).
  - The admin role lets `get_screening_report` read every user's batches.
- **P0 object-level access: CONFIRMED on all three.**
  - `routes/folderprocesser.py:267-301`: if the ownership lookup fails but the caller owns any row in `bulk_screening_results` (lines 285-291), the file is served from the shared reports folder.
  - `routes/endpoint/bulk_processing.py:300-310`: `delete_batch(batch_id, user_id)` never uses `user_id` in the UPDATE. Called from `folderprocesser.py:232`.
  - `routes/chat.py:118-122` and `db/endpoints/chat_thread.py:104`: history is read by thread ID alone. The user ID is read from the session and not used.
- **P0 file paths: CONFIRMED.**
  - `routes/file.py:22-24` joins the client filename into `uploaded_files/`. Duplicate checks are keyed on (filename, user), so a different user uploading the same name is written to the same path and overwrites the first user's file. A filename containing `../` is not stripped.

### Additional findings (not in CODEX-001)

- **P1:** no login throttling (`routes/auth.py:45`). `update_password` takes the new password in the URL query (`db/userendpoint.py:58-59`), so it reaches access logs.
- **P1:** the cookie is `SameSite=None` in production (`routes/auth.py:37`) and several endpoints take plain form posts, so cross-site request forgery is possible. CORS allows credentials from `https://claude.ai` and a regex for any of Akshay's Vercel preview sites (`app.py:83, 100-106`).
- **P1:** indirect prompt injection. `PromptInjectionGuard` filters only the recruiter query and the job description (`mcp_server/security.py`). Resume snippets returned by `search_resumes` and fed to the screening model are unfiltered.
- **P1:** raw exception text is returned to clients (`app.py:38`, `routes/chat.py:106`, the search error path in `mcp_server/tools.py`).
- **P2:** `User.user_role: str = Literal[...]` is a default value, not a type (`db/userendpoint.py:16`), so any role string is accepted (admin-only endpoint).
- **Product gap:** accounts are created by an admin (`/user/create_user`). There is no tenant or sign-up model. A public Directory listing has no way to onboard outside customers.
- **Exposure qualifier:** on this branch `nginx/recai.estuate.com.conf` proxies only `auth|user|main|file|chat|folder|conversion`. `/mcp`, `/oauth`, `/.well-known` and `/job` fall through to the single-page app. So the P0 MCP finding is probably not reachable from the internet through this configuration. The live server is unverified.

### Checked and acceptable (static)

- Database calls use bound parameters. No string-built SQL found.
- The LibreOffice call uses an argument list, not a shell (`document_processing/docxtpl_converter.py:163`).
- Search is limited to the caller's Pinecone namespace `estuate-data-<user_id>` (`embedding/embedder.py:80-88`).
- Admin routes check the role.

### Challenges to the serverless and cost parts

- **Agree** with the Lambda split, the SQS pipeline with caps and dead-letter queue, and the 30-second HTTP API limit as the reason to make screening asynchronous.
- **Aurora scale to zero:** AWS documents a resume time of up to about 15 seconds (AWS database blog, unverified against current docs). That is poor for a live Claude tool call. Neon scales to zero after 5 minutes and wakes in a few hundred milliseconds by its own FAQ (vendor figure, unverified). Both need a prototype.
- **Cheaper than any of them:** pgvector in PostgreSQL could replace Pinecone at 2,000 to 5,000 resumes a month. Pinecone's Standard plan has a $50 monthly minimum, so Akshay's $15 estimate needs checking.
- **Honest savings:** current hosting is about $73/month. Serverless saves roughly $55/month at present volume, so it should be staged and not rushed. Security fixes first, on the current server.
- **Scope:** agree with starting the public release with evidence and citations only. I added a private custom connector for Estuate's own Claude organisation as the first step, which needs no Directory review.

### Open items

- **Policy claim not verified by me.** I found the 12 November 2026 high-risk statement (candidate screening and ranking) only on a secondary blog about the Usage Policy, not on Anthropic's own page. CODEX-001's citation list is better, but I did not open those pages. Marked open. Whether it applies to a business-internal connector is also unclear.
- **Live check not done.** Whether the MCP branch is deployed, and whether the dev mode is on there, needs the owner's go-ahead.
- **Not executed:** no tests, no reproduction of any finding.

### Artefacts

- Full write-up: `D:\2026-estuate\Anthropic-app-publishing\RecAI-Analysis-Serverless-Security-Plan.docx`.
- Project standards and plan: `D:\2026-estuate\Anthropic-app-publishing\` (CLAUDE.md, STATUS.md, PLAN.md, DECISIONS.md, POC-STANDARDS.md).
- No application or infrastructure changes were made.
