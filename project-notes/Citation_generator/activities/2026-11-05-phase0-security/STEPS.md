# Phase 0 security fixes on the current RecAI code

Date: 2026-11-05. Owner: Kishore Kunal. Branch: `estuate/phase0-security` in `mcp-code/citation_generator` (local only, not pushed). Related ADR: ADR-005, ADR-007.

## Purpose

Close the flaws that were reproduced by running the app, on the current dependency versions, so each test result shows exactly what a fix did. Dependency upgrades and the rebuild are separate work.

## Prerequisites

- Docker Desktop running; `docker compose up -d` in `mcp-code/citation_generator` (database and backend healthy).
- Git-ignored `.env` present (generated throwaway values). `MCP_DEV_MODE` is no longer a setting; it must not appear in `.env`.

## Steps

1. Run the tests first and confirm they fail where the flaws are: `python tests/security/phase0_checks.py`. Recorded result before fixes: 13 passed, 13 failed.
2. Apply the fixes: `python activities/2026-11-05-phase0-security/patch_phase0.py` from the project folder (it patches the repository files in place and asserts each change; run it once only, on a clean branch). What it does:
  - `mcp_server/oauth.py`: the only accepted MCP credential is an OAuth access token issued by `/oauth/token`, sent as a Bearer header. Removed: cookie acceptance, web-session token acceptance, the developer API key, the `MCP_DEV_MODE` fallback and the localhost shortcut. The optional lookup returns nothing instead of inventing an admin.
  - `routes/folderprocesser.py`: report download allowed only for the batch owner or an admin, with a safe file name and a folder-containment check; bulk upload stores files per user and sanitises names; `.env` no longer overrides the environment.
  - `routes/file.py`: single upload sanitises the file name and stores under `uploaded_files/<user id>/`.
  - `utils/safe_paths.py` (new): `safe_filename`, `user_upload_path`.
  - `routes/chat.py` and `db/endpoints/chat_thread.py`: thread reads need ownership (404 otherwise), a query on someone else's thread returns 404 before any model call, and the database write itself refuses a non-owner.
  - `routes/fileconverstion.py`: the converter finds the user's own upload through the database instead of joining a client-supplied name to a folder.
  - `agents/agents_main.py`, `document_processing/docxtpl_converter.py`: `load_dotenv()` without `override=True`.
3. Re-run `python tests/security/phase0_checks.py` until every check passes (26 checks). Fix what it shows; do not weaken a test to make it pass.
4. Delete the older reproducer `tests/security/two_user_checks.py`, commit, post the result in the shared review log, update STATUS.md and HISTORY.md.

## Verification

- Exit code 0 from `tests/security/phase0_checks.py`, with both the denial (403 or 404, never a 500) and the owner's success asserted for each area: MCP authentication, report download, chat read and write, single and bulk upload, admin-only deletion (kept), configuration precedence.

## Rollback

- `git switch estuate/local-bringup` (the branch before these edits), or `git checkout -- .` on this branch before committing. No data outside the throwaway local database is touched.

## Gotchas

- The uvicorn `--reload` picks up code changes automatically; if an import error appears, check `docker compose logs app`.
- A thread owned by a user but marked deleted counts as not found.
- Existing production files live flat in `uploaded_files/`; the database stores each file's real path, so old files keep working. Only new uploads go to per-user folders.
- Not in Phase 0 (follow-up): converted-resume download and preview by file name, shared report file names across users, password in the URL, login throttling, CSRF and CORS, resume-text prompt injection, error text leakage, `core.mcp_oauth_tokens`.
