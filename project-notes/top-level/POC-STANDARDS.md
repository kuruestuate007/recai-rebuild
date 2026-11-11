# POC standards

Every proof of concept in this folder meets these checks before it is exposed to anyone outside the team. Tick them off in the POC's own STATUS entry.

## 1. Security gate

- **Authentication fails closed.**
  - No token means no access. No development fallback, test key or localhost bypass in deployed builds.
  - Tokens are checked for issuer, audience, expiry and scope. Session or cookie credentials are not accepted on the public API.
- **Tenant isolation on every data path.**
  - Every read, write, delete and download is scoped to the caller's tenant and the specific object.
  - Files are stored under generated IDs in private, encrypted storage. Client filenames are labels only. Downloads use short-lived signed links.
  - Tests: two users, one tenant each, try to read, change, delete and download each other's data through the normal endpoints.
- **State is shared, not in memory.** Tokens, sessions and rate limits survive restarts and work across several workers.
- **Abuse limits.** File size, page count, upload count, calls per minute and spend per tenant per day. Budget alarms on the cloud account.
- **Hostile input.**
  - Uploaded documents are parsed in a sandboxed worker with no network, no secrets and a time limit.
  - Text from documents is treated as data when passed to a language model: delimited, labelled, structured output, no authority over tools.
- **Least privilege.** The public service has its own cloud role with access only to its own storage prefix, queue and database role. No path to admin functions or infrastructure APIs.
- **Errors and logs.** Generic errors outward. Redacted structured logs. No secrets, queries, resume text or personal data in logs. Tracing off unless reviewed.
- **Secrets.** In a secrets manager. Never in the repository, chat or documents. Scan with Gitleaks. Scan dependencies and images with Trivy.
- **Browser safety.** Cookies HttpOnly, Secure and SameSite Lax or stricter. CSRF protection on state-changing calls. CORS allow-list with no wildcard patterns for credentialed requests.

## 2. Cost gate

- **Verify prices** against current published prices on the day. Record the source.
- **List every component:** compute, disk, IP, storage, snapshots, monitoring, data transfer, and any outside vendors on a separate line with their minimums.
- **State assumptions** (hours, GB, call volumes) and what would change them.
- **Idle cost:** state what the POC costs when nobody uses it.
- **Commitments** (Savings Plans, reserved capacity): state exactly what they cover, the obligation, the return window and who must confirm.
- **Document for stakeholders** in Word, short, written for the named audience, with the decision requested.

## 3. Anthropic marketplace gate (connectors)

Verify each point against the primary page at claude.com/docs/connectors/building before every submission.

- Remote server on HTTPS. OAuth 2.0 for user data, with Claude's callback `https://claude.ai/api/mcp/auth_callback` and a loopback redirect on any port for Claude Code.
- Sign-in method Claude supports: dynamic client registration, Client ID Metadata Document, or Anthropic-held credentials. S256 PKCE. Discovery returns 401 with a resource_metadata pointer. Discovery, registration and token endpoints answer within 10 seconds, refresh within 30.
- Every tool has a title and a read-only or destructive annotation. Names 64 characters or fewer. Read and write in separate tools. Accurate, narrow descriptions with no instructions to Claude.
- Specific error messages. Reasonably sized responses. No collection of conversation data beyond the tool's need.
- Public documentation and privacy policy URL. Support contact. Icon. Reviewer test account with a fully populated account.
- Allow Anthropic's address range 160.79.104.0/21.
- Policy check: the Anthropic Software Directory Policy and Usage Policy. High-risk uses (for example candidate screening and ranking) need separate review. Do not rely on secondary sources.
- Tested with MCP Inspector and as a custom connector in Claude.

## 4. Documentation and continuity gate

- CLAUDE.md, STATUS.md, HISTORY.md, DECISIONS.md and PLAN.md are current.
- Each setup or change has `activities/<date>-<activity>/STEPS.md` with rollback.
- Findings state the commit, `file:line`, and whether they are static or executed.
- No tables in markdown files.

## 5. Release gate

All four gates above are ticked, a rollback is written down, and the owner has said go.
