## CLAUDE-013 — AWS sign-in note for the build

**Peer read through:** CODEX-018

- The owner will sign in to AWS himself when the setup is ready. Do not wait for it and do not ask for credentials.
- Build the Terraform with the profile, region and pinned account id as required variables (default region Ohio, no default account id). The `up` script must refuse to run until the account id is set and must print the account it is about to use before asking for approval.
- The only AWS profile on the owner's machine is named `glencore-erm` (a client engagement account, default region Zurich). Do not reference it in code, defaults, examples or documents. Whether RecAI uses a separate Estuate account is the owner's decision.
