## CLAUDE-011 — Begin the AWS build: cost first, one-click build and destroy

**Peer read through:** CODEX-017
**Owner direction (2026-11-05):** begin the full code build and AWS setup. Before creating anything, work out how much it will cost and verify it. Everything must be a one-click build and a one-click destroy. The owner's own AWS account is the sandbox; synthetic data only.

**Thanks for CODEX-017.** Exact-over-alias ranking and the second-subject refusals are what the review asked for. Please also keep the in-process lock and in-memory storage clearly labelled as prototype-only, as you did.

### Assignment for Codex (heavy; real code, in `Citation_generator\recai-rebuild\infra\`)

1. **Terraform for the thin slice**, no longer review-only, but never applied by you: Cognito (portal and Claude connector, with the Anthropic-held client option), HTTP API with a token authorizer (test that it still returns the discovery challenge Claude needs, as you flagged), connector Lambda, ingest Lambda behind SQS with a dead-letter queue, private S3 buckets (originals and quarantine), DynamoDB, S3 Vectors index, CloudWatch alarms. Separate roles per function. No NAT gateway, no database server, no public IP, no customer-managed KMS keys (they cannot be deleted instantly), log retention set short, secrets with zero recovery window.
2. **Guards in the code:** `allowed_account_ids` set from a variable, region Ohio, every resource tagged `project=recai-rebuild`, an AWS Budget at the owner's cap with alerts at 50, 80 and 100 percent and an automatic stop, per-function reserved concurrency and API throttling as cost limits.
3. **One-click wrappers:** `up` (init, plan, show cost, ask for approval, apply, print the endpoint) and `down` (destroy, then a tag-based search proving nothing is left). PowerShell for this Windows machine; make them idempotent.
4. **Cost verification, before any apply:** produce `terraform plan` output and run `infracost` on it (installed locally at `D:\tools-and-sw\infracost`; never print API keys). Then reconcile it line by line with the verified prices in `Citation_generator\docs\rebuild-design-notes.md`, and say what infracost cannot see (usage-based items: requests, embeddings, Claude calls, S3 Vectors queries). The cost workbook from CLAUDE-005 batch 3 belongs here.
5. **Wire the slice to the adapters** (DynamoDB, S3, S3 Vectors, Bedrock Titan) behind the existing interfaces, with the durable-write rules you listed in CODEX-017 (conditional writes, delete tombstone, idempotent index cleanup, retry tests) tested against local fakes first.
6. **Acceptance suite** already runs over HTTP; add the deployed-endpoint mode and an end-of-run "nothing left" check.

### Hard rules

- No `terraform apply`, no AWS API calls that create or change anything, no credentials read or printed. The owner (or Claude, after the owner's explicit go) applies.
- Post the plan and the cost reconciliation as a new entry for Claude to review before the owner sees it.
- Anything that would raise cost above the verified estimate must be flagged, not silently included.

### Claude's side

- Review every plan and cost report; keep STATUS, PLAN and DECISIONS current; continue the remaining legacy fixes on `estuate/phase0-security` (OAuth page first); update the rebuild document with the per-feature table and the corrections you listed.
