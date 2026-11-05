# RecAI AWS infrastructure

Status: offline-tested scaffold. Real deployable connector and ingest archives are required. The current in-memory prototype is not a production Lambda package. No live plan, Infracost run, or AWS verification has been performed.

## Checks without an AWS login

Run from this directory:

```powershell
terraform init -backend=false -input=false
terraform fmt -check -recursive
terraform validate
terraform test
```

Tests use a mocked AWS provider and plan-only runs. Keep the provider lock file in version control.

## Owner-run scripts

- `up.ps1` checks the AWS profile's account, pins Terraform to that account, creates a saved plan, and passes it with an explicit usage file to Infracost. It prints the account and requires the typed stack-specific approval before applying that same plan. ReviewedMonthlyUsd is a manual all-in estimate, not a value derived from Infracost. Compare the printed plan and unsupported usage to that estimate before proceeding.
- `down.ps1` uses the exact account, region and stack state. Supply a Terraform var file with the same deployment inputs, keep the Lambda ZIPs, then approve the destroy plan. The stack deletes its own bucket contents. Never reuse a stack ID for someone else's deployment or import unrelated resources into this state. Preserve the private state while the stack exists. A failed initial deployment might lack target outputs and need a deliberate recovery plan. After destroy it checks Terraform state and the regional tag inventory. Global, unsupported, or untaggable resources still require service-specific verification, and tag inventory can lag.
- Keep .local, plan JSON, and state private. Cognito can store the app-client secret in Terraform state. The scripts do not display that secret. Do not use hosted Infracost uploads for sensitive plans. Use an approved local estimator workflow before planning with real state.

## Release gates and limits

- Pass region explicitly. S3 Vectors is listed in both Ohio and Zurich. AWS's Titan Text Embeddings V2 knowledge-base support table lists both, while the direct model card does not list Zurich. Confirm direct InvokeModel availability and regional pricing before picking Zurich. Ohio is the working cost baseline and direct invocation is listed there.
- Lambdas start paused and ingestion starts disabled. Switch EnableRuntime only after the build packages fail closed, the AWS persistence layer is tested, and cloud OAuth is proven. The portal routes require scoped JWTs at the gateway. MCP routes leave the OAuth 401 and resource metadata to the handler. Do not deploy the local fixture verifier.
- EnableBudgetAction opts into an automatic IAM deny for model invocation and vector queries/writes on only this stack's runtime roles at 100 percent. This is delayed, partial protection. API, logs, identity, storage and queued activity may still cost money. Activate the stack cost-allocation tag and verify the budget's tracking and action permissions before relying on it. The independent runtime pause sets reserved concurrency to zero and disables the ingestion event mapping.
- Infracost must be reconciled with actual planned monthly requests, Lambda memory and duration, log volume, S3 and queue operations, vector storage, writes, query scans and returned data, Bedrock input tokens, Cognito users and data transfer. OCR and Claude model use are outside this infrastructure. No live estimate has been approved.
