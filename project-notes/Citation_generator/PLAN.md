# Plan: RecAI MCP connector

Last updated: 2026-11-05. Source of truth for the phases. Details of each finding are in `docs/deliverables/RecAI-Analysis-Serverless-Security-Plan.docx`.

## Phase 0: stop the bleeding (hours)

- **Goal:** nothing exploitable, on whatever is deployed.
- **Steps:**
  - Turn MCP_DEV_MODE off and remove MCP_DEV_API_KEY from any deployed environment. Delete both fallbacks from the code.
  - Fix report download, batch delete, chat history and upload path (findings 3 to 6), each with a two-user regression test.
  - Confirm with Kishore's go-ahead whether `/mcp` is reachable on the live server.
- **Exit check:** an unauthenticated call to POST /mcp returns 401. The two-user tests pass.

## Phase 1: hardened private connector (days)

- **Goal:** safe for Estuate's own recruiters.
- **Steps:**
  - Shared token store (or a managed identity provider) and the official MCP SDK.
  - Tool titles and read-only or destructive annotations. Separate read and write tools.
  - Error and log cleanup, login throttling, password out of the URL, CSRF and CORS fixes.
  - Cap every screening input path. Return a job ID instead of running inline.
  - Files and backups to S3. Postgres backups with a restore test.
  - Add the connector to Estuate's Claude organisation as a custom connector and test every tool.
- **Exit check:** a week of recruiter use without incident.

## Phase 2: Directory submission (after decisions)

- **Goal:** public listing, reduced scope.
- **Steps:**
  - Decide the customer and tenant model.
  - Privacy policy and legal/security sign-off from Estuate (blocker).
  - Verify Anthropic's policy on candidate screening and ranking from primary pages.
  - Seeded reviewer account, documentation page, icon, support contact, allow Anthropic's address range.
  - Submit through claude.ai/directory/manage.
- **Exit check:** submission accepted.

## Phase 3: serverless (only if justified)

- **Goal:** no idle cost, stronger isolation, less patching.
- **Steps:** staged per ADR-004, starting with a database prototype.
- **Exit check:** measured cost and latency beat the current setup.

## Parallel track: business approvals

- Seema: approve plan, 1-year commitment question (ADR-002).
- Akshay: Pinecone plan behind the $15 figure, size of file folders, time to move storage to S3.

## Release-one feature gates (from CODEX-016 and the owner's direction, 2026-11-05)

A feature goes into release one only if every line of its gate is proved with evidence. Candidates, in rough order of readiness:

- **Cited evidence search (Claude connector):** exact excerpt with page or section, explicit "no evidence" answer. Gate: citation accuracy and reliable abstention on a blind labelled corpus (today's fixture returns false evidence on 6 of 12 empty cases), cross-tenant denial, cold latency inside Claude's tool timeout, tested in a real Claude client.
- **Portal: upload, job status, list and delete documents:** Gate: two-user denial and owner success for each action, deletion proved gone from storage and search, size, page and concurrency limits.
- **Access-controlled source links:** short-lived, owner-scoped.
- **Neutral job-description-to-evidence mapping and cited evidence export:** only if outputs do not score, rank or recommend candidates.
- **Requisitions and account management, report history and exports, template conversion with preview, edit and download:** each only if its whole flow and cross-user controls pass (the converter already has ownership checks; legacy names and basename-based ownership are open).
- **Not in release one:** scoring, ranking and `start_screening` as public tools (policy: qualified human review and disclosure first), video interviews, web-search fallback in chat, assumed case-study claims.
- **Every listed tool:** annotations, documentation, OAuth, privacy policy, reviewer account, tested in Claude.

