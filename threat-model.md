# RecAI design review and threat model

Scope is the proposed AWS evidence connector and intake portal. Keep the local prototype synthetic. The internal screening, chat, conversion, and export economics need a separate scenario with the same workload on both sides. The $25 target applies to the narrow pilot until measured. See the project design notes and architecture-gates.md.

| Boundary | Failure or abuse | Release control and evidence |
| --- | --- | --- |
| Claude and browser to API | Stolen token, spoofed issuer or tenant, stale access | Fail closed. Validate access token, resource, scope and signature. Derive tenant and membership server-side. Test discovery, refresh, revocation and two independent accounts. |
| API to index and documents | Forged IDs, wrong-tenant index hits, stale results after deletion | Filter within the authenticated namespace and recheck every result against the canonical ready document and passage before returning bytes. Include same-ID collisions and injected stale hits in tests. |
| Browser to quarantine | Oversized uploads, malicious files, parser exploitation | Use short-lived scoped uploads with size limits, immutable generated keys and quarantine. Constrain worker CPU, memory and time. Separate parser permissions and networking from identity, search and paid services. |
| Queue and worker | Duplicate delivery, partial writes, delete/reindex race | Use conditional state transitions, idempotency keys and a dead-letter queue. Make deleted documents immediately invisible via a tombstone before asynchronous cleanup. Test replay, crash between writes and retry after deletion. |
| Free demo | Scraping, repeated OCR or model calls, noisy neighbor spend | Use a fixed synthetic corpus and remove uploads from the anonymous demo. Enforce edge throttles, tenant quotas, a global paid-work quota and reserved concurrency. Budget alerts inform operators and do not enforce a hard cap. Test the kill switch and document residual gateway/log charges. |
| Logs and operators | Candidate text or tokens in logs, insufficient audit trail | Log request ID, coarse outcomes and tenant pseudonyms. Keep retention bounded and access scoped. Test that payloads, bearer tokens and signed links are absent. Audit admin, access and delete events. |
| Release and recovery | Overbroad IAM, leaked credentials, restore resurrects deleted documents | Separate read, parse and index permissions. Use an explicit deployment role, versioned infrastructure, restore drills, and a deletion ledger checked after restore. |

## Architecture details to reconcile

- Separate the security gate for a deployed legacy app from the rebuild. The earlier review in CODEX-011 still covers bulk-screening ownership, report write paths, OAuth and older file rows. Protect or disable those paths before exposing the legacy build.
- The MCP authorization challenge must survive the gateway. Prototype the real Claude hosted-client flow before choosing a gateway authorizer or claiming Claude Code support.
- The isolated parser with only S3 and DynamoDB gateway access cannot also be assumed to reach Bedrock or an external OCR endpoint. Separate parsing from indexing and explicitly choose network access for the paid worker. SQS can invoke Lambda through its event source mapping.
- The internal-analysis policy exclusion is workflow-specific. The public tool should fetch source evidence without producing scores or shortlists.
- Record recurring costs for storage, auth, edge, queue, logging and paid processing. Include backfill, retries and OCR. Calibrate screening quality and model price separately. Validate numbers against AWS and the billed workload before using them in the CEO comparison.
