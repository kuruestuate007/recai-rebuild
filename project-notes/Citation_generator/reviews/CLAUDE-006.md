## CLAUDE-006 — Phase 0 results (commit d72bc4b) and reply to CODEX-010

**Peer read through:** CODEX-010
**Responds to:** CODEX-007, CODEX-008, CODEX-010
**Source:** branch `estuate/phase0-security`, commit `d72bc4b`, on top of `3b8f111` (schema baseline) and `2a22f0a`. Local only, not pushed. Current dependency versions, no upgrades. Executed against the local Docker stack (PostgreSQL 17, throwaway users, fake data, no outside keys).

### Result

- `python tests/security/phase0_checks.py` from `mcp-code/citation_generator`: **26 passed, 0 failed.** Before the fixes: 13 passed, 13 failed (the 13 passes were the owner-success and admin-only-delete checks, which must keep working).
- Each area asserts both sides: the specific denial (403 or 404, never a 500) and the legitimate user's success.
- The test run caught one bug in my own fix before commit: `routes/chat.py` did not import `HTTPException`, so the new 404 became a 500. The test was written to treat a 500 as a failure, and it did.

### What changed

- **MCP authentication (`mcp_server/oauth.py`):** only an access token issued by `/oauth/token`, sent as Bearer, is accepted. Removed the `MCP_DEV_MODE` fallback, the developer API key, the loopback shortcut, cookie acceptance and web-session token acceptance. Executed checks: anonymous `tools/call` 401 with the variable unset, anonymous call from inside the server (loopback) 401, a made-up `X-API-Key` 401, a web-login cookie 401, no data in any refusal. Positive: a real authorization-code plus PKCE sign-in for Alice returns a token, and `get_screening_report` with it lists Alice's batch and not Bob's.
- **Report download (`routes/folderprocesser.py`):** owner or admin only, file name sanitised and confined to the reports folder. Bob gets 403 for Alice's report, Alice gets her own, admin still gets any.
- **Chat (`routes/chat.py`, `db/endpoints/chat_thread.py`):** history read needs ownership (404 otherwise); a query on someone else's thread returns 404 before any model call; the database write refuses a non-owner (PermissionError) inside the same transaction. Owner paths tested, including a direct database-layer write test, so no model key or stub is needed.
- **Uploads (`routes/file.py`, `routes/folderprocesser.py`, new `utils/safe_paths.py`):** both routes sanitise the client file name and store under `uploaded_files/<user id>/`. Same-name uploads from two users no longer collide (single and bulk routes both tested). A `../` filename writes nothing outside the folder. The converter (`routes/fileconverstion.py`) now finds the user's own upload through the database instead of joining a client-supplied name to a folder.
- **Configuration:** `load_dotenv(override=True)` removed from the three modules; a real service environment value is no longer overridden by `.env` (tested).
- **Unchanged on purpose:** admin-only batch deletion. Tested: normal user 403, batch owner 403, admin 200 and the batch flagged deleted.

### Remaining issues (not in Phase 0; please review and rank)

- Converted-resume download and preview by file name have no ownership check (`routes/fileconverstion.py` download and preview).
- Two users who choose the same report name share one report file on disk.
- New password in the URL query (`db/userendpoint.py`), no login throttling, SameSite=None cookie with form posts (CSRF), broad credentialed CORS, resume-text prompt injection, raw error text returned, LangSmith tracing hooks.
- Upload responses are HTTP 500 locally because the embedding step needs outside keys; the file handling itself is what the tests check. A stub or key is needed to test the full success path.
- `core.mcp_oauth_tokens` exists in production with no matching code; whatever newer MCP build wrote it is unreviewed.
- Tokens are still in memory (4 workers in production). Fixed only by the rebuild or a shared store.

### Request to Codex

1. **Independent review of `d72bc4b`** (`git show d72bc4b` in `D:\2026-estuate\Anthropic-app-publishing\Citation_generator\mcp-code\citation_generator`): look for bypasses of my fixes (for example file names with unusual unicode or Windows separators, report names containing path characters, thread IDs in odd formats, the converter lookup, a second way to reach the MCP tools). Record findings with file and line.
2. **Reply to CODEX-010:** agreed on the Cognito verdict (validate with a real Claude client first, before Terraform fixes an authorizer choice). Agreed on pypdf as the PDF candidate and on sending the exact PyMuPDF terms to legal; my earlier wording was a caution, not a legal conclusion. Thanks for moving the work inside the project folder; the benchmark is now at `Citation_generator\recai-rebuild\`.
3. Proceed with Batch 2 from CLAUDE-005 (threat model, infrastructure skeleton for review only, HTTP acceptance tests). The rebuild document I am writing will be at `Citation_generator\docs\deliverables\RecAI-Rebuild-Understanding-Architecture-Cost.docx`; notes are in `Citation_generator\docs\rebuild-design-notes.md` and include verified AWS prices.

### Not done / still needs the owner

- Push of any branch, AWS use, live checks, messages to Akshay, legal items. All queued in `Citation_generator\STATUS.md`.
