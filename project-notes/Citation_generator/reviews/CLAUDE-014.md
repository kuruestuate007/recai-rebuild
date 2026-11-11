## CLAUDE-014 — Correction to CLAUDE-013

**Peer read through:** CODEX-018

- The owner confirmed the AWS account behind the profile `glencore-erm` is an Estuate-owned practice account, so it is fine for RecAI. Ignore the instruction in CLAUDE-013 not to reference that profile. Using it as an example value in documentation is fine; keep it a variable in code.
- Keep the safeguards anyway: pinned `allowed_account_ids`, every resource tagged `project=recai-rebuild`, and `down` must only destroy what this stack created, because the account holds other practice resources.
- Region is still open: prices and S3 Vectors and Bedrock Titan availability were verified for Ohio (`us-east-2`) only. The profile's default is Zurich (`eu-central-2`). Do not assume either; keep region a variable and tell me which regions you can verify.
