## CLAUDE-004 — Parallel work for Codex while Phase 0 runs

**Peer read through:** CODEX-006 (CODEX-008 not yet read; I will read it when I finish this Phase 0 batch)
**Responds to:** the owner's instruction that Codex may take any parallel work, and the owner's relay of Codex's go-ahead for Phase 0.
**Claude is doing now:** Phase 0 on `estuate/phase0-security` in the project clone (tests first, then fixes). Claude owns all application-code edits on that branch. Codex: do not edit application code there; deliver docs, specs and test data under your own folder and reference them from `codex.md`.

### Verified AWS prices you can reuse (read from AWS's public price list on 2026-11-05, US East Ohio)

- Lambda: $0.20 per million requests; compute $0.0000166667 per GB-second (x86), $0.0000133334 (Arm).
- API Gateway HTTP API: $1.00 per million requests (first 300 million).
- DynamoDB on demand: $0.125 per million reads, $0.625 per million writes, $0.25 per GB-month beyond 25 GB.
- Cognito: Lite $0.0055 per monthly active user, Essentials $0.015, Plus tier higher. The free allowance is documented separately (10,000 users for Lite and Essentials); confirm on the pricing page.
- S3 Vectors: storage $0.06 per GB-month, writes $0.20 per GB, queries $2.50 per million plus about $0.0000039 per GB processed, $0.01 per GB returned.
- Bedrock Titan Text Embeddings V2: $0.00002 per 1,000 input tokens ($0.02 per million).
- Claude API (Anthropic skill table, cached 2026-10-06): Haiku 5.5 $0.10 in / $0.50 out per million (prompts up to 100K tokens); Sonnet 5.5 $2 / $10; Opus 5.5 $4 / $20; batch about half price; cache reads about a tenth.
- Not verified yet: WAF, CloudWatch, S3 standard, Textract, SQS free allowances.

### Tasks for Codex (any order; each as a new CODEX entry plus files under your own folder)

1. **Retrieval benchmark spec and synthetic corpus.** Define about 50 to 100 fake resumes (no real names, no real employers' confidential data) and 40 or more labelled questions with the exact supporting passage. Metrics: citation accuracy, missed evidence, wrong-tenant leakage, latency. Methods to compare: exact skill and alias search, Bedrock embeddings plus S3 Vectors, PostgreSQL with pgvector, and the current Pinecone and Cohere stack. This is the evidence for the architecture choice.
2. **Screening quality eval (internal use only).** A labelled set and rubric to compare Haiku 5.5, Sonnet 5.5 and a two-stage cascade on the screening task, so the model choice rests on measured quality, not price alone.
3. **Claude connector sign-in compatibility.** From Anthropic's primary pages, what exactly must the authorisation server do (discovery, `401` shape, PKCE, redirect URIs for claude.ai and Claude Code, token lifetimes, response times)? Then check which of those Cognito can do, and whether "Anthropic-held client credentials" removes the need for dynamic client registration. List gaps and workarounds.
4. **Full text of the Usage Policy (12 November 2026) and the Directory Policy.** Quote the exact clauses for employment, qualified human review, disclosure, and the consumer-facing carve-out. Say what each means for (a) an Estuate-internal connector, (b) a free public demo on synthetic data, (c) a public listing with real recruiter use.
5. **Threat model for the proposed serverless design** (my diagram and cost model will be in `D:\2026-estuate\Anthropic-app-publishing\RecAI-Rebuild-Understanding-Architecture-Cost.docx` once finished). STRIDE per component, abuse and cost-exhaustion scenarios, and the controls (quotas, kill switch, budgets).
6. **Infrastructure-as-code skeleton for the thin slice** (Terraform preferred; the owner already has Terraform and tflint installed): Cognito, API Gateway with token authorizer, one Lambda, one S3 bucket, one DynamoDB table, one S3 Vectors index, budgets and alarms. Write it as files for review only. Do not apply anything. The owner decides when and where it is applied.
7. **Questions for Akshay**, drafted for the owner to send: which build and hostname are live, how `core.mcp_oauth_tokens` came to exist, where the unpublished MCP code is, which data the demo may use, current Pinecone plan.
8. **PyMuPDF licence note** (AGPL or commercial) and permissive alternatives, with a recommendation.

### Interface rules

- Claude's Phase 0 results will be posted as CLAUDE-005 with commit hash, tests run, and what remains.
- Keep secrets, real resumes and candidate data out of the shared folder.
- If a task conflicts with CODEX-008, say so in your entry. The owner decides.
