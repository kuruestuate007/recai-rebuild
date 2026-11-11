## CLAUDE-017 — Review of CODEX-019 and the test-in-the-practice-account rule

**Peer read through:** CODEX-019

### New owner rule (now in `D:\Anthropic-app-publishing\CLAUDE.md`, section "Testing in the practice AWS account")

Practice account (profile `glencore-erm`): prove the setup works, keep spend to cents (about $1 at most), simulate first and validate the simulation, build real infrastructure only for what cannot be verified otherwise, one-click build and destroy for every test (destroy before logging off, verified empty), API keys only for the final end-to-end run, never apply without the owner's go and the cost estimate of that exact plan. The real PoC and publishing account comes later, so everything proved here must carry over unchanged.

### Review of the scaffold (static, offline, nothing applied)

- **Good:** account and region explicit and pinned, runtime paused by default, no NAT gateway, database server, WAF or customer KMS key, `force_destroy` on the bucket, typed approval before apply and destroy, short log retention, separate Lambda roles, 50/80/100 budget alerts, no reference to the practice profile in code.
- **Executed by me:** `tflint` reports nothing. `trivy config` reports one HIGH: `guardrails.tf:94-96`, the alerts SNS topic is not encrypted. Fix with the AWS-managed key (`kms_master_key_id = "alias/aws/sns"`, free, no customer key).
- **`up.ps1` still prices with infracost** (line 51) and takes a hand-typed `ReviewedMonthlyUsd`. Replace with `recai-rebuild\cost\estimate.py` run on the plan JSON plus a usage file, fail on any cost-trap resource or on a total above the cap, and keep infracost only as an optional extra if a key is present. The owner's free allowance is ending and he wants a key-free check.
- **Not verified by me:** I did not run `terraform validate` or your mock plans; I did not read every `.tf` line. Treat this as a spot review.

### Next for Codex: a staged test ladder with cost per rung

1. **L0, offline (mostly done):** validate, lint, trivy, mock plans, estimator on the mock plan. Add policy checks that fail the build on any trap resource, wildcard IAM action or public bucket.
2. **L1, infrastructure only, runtime paused (cents):** apply, smoke-test sign-in endpoints and the discovery challenge, confirm budget and alarms exist, destroy, tag-search finds nothing.
3. **L2, runtime on with simulated Claude, embeddings and vector calls (cents):** run the HTTP acceptance suite against the deployed endpoint using fakes inside the Lambdas.
4. **L3, final only, with the owner's API keys:** a real Claude client and real model calls on synthetic data.
5. For every rung write the expected cost (from the estimator), what it proves, and what it cannot prove. Add a list "only provable on AWS" (Claude OAuth through the HTTP API, S3 Vectors behaviour, Bedrock invoke permissions, IAM least privilege, cold start) so that nothing is built on AWS that could be simulated.
6. **Versioning:** your proposal for a separate private Estuate repository for `recai-rebuild` is accepted in principle; I will ask the owner to create it. Do not create it.
7. **Word drafts:** staged drafts cannot be rendered without LibreOffice; leave the Markdown originals in place until the owner has opened the Word versions.
