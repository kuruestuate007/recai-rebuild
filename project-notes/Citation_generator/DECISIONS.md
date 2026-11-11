# Decisions (ADRs)

Each decision has a status: Accepted, Pending (waiting on a person), or Proposed (Claude's recommendation, not yet confirmed). Every one has a "Revisit when" trigger.

## ADR-001: Hosting for the first release

- **Status:** Accepted by Kishore, 2026-11-04.
- **Decision:** one AWS t3.large (2 CPU, 8 GB) in US East (Ohio). PostgreSQL installed on the VM and managed by Akshay. S3 holds the live files and the database backups. Outside AI services (Pinecone, Cohere, OpenAI, Claude) are billed separately by usage.
- **Why:** all heavy AI work is external, so 2 CPUs are enough, while 8 GB is needed because the database, 4 app workers and LibreOffice share memory. This costs less than the earlier 4-CPU quote.
- **Cost:** about $73/month on-demand (server $60.74, disk $3.20, IP $3.65, snapshots $1.50, S3 $3.00, monitoring $1.00).
- **Known limit:** one server means no automatic failover. Recovery is by restoring from backup.
- **Revisit when:** a failover requirement appears, real usage differs a lot from the estimate, the ARM trial passes (t4g.large saves about $12/month), or the serverless prototype (ADR-004) shows lower cost.

## ADR-002: One-year AWS commitment

- **Status:** Pending. Question sent to Seema on 2026-11-04.
- **Facts verified against AWS documentation:**
  - It is not tied to a VM. It is a fixed hourly dollar amount (about $0.0522/hour) applied to matching t3 usage in the Ohio region of the AWS account that bought it. Other accounts in the same Organization can use it only if discount sharing is on, after the buying account.
  - The saving is fixed at about $23/month. Extra t3 servers do not add to it. The amount is paid for the full year even if the server is stopped or deleted, and unused amounts do not carry over.
  - It can be returned only within 7 days of purchase and in the same calendar month (and the hourly amount must be $100 or less). Buy near the start of a month.
  - Existing Reserved Instances or Savings Plans are applied first, so a new commitment can be partly wasted.
- **Options if the server may change family or region:** a Compute Savings Plan (about 28% off instead of 37%).
- **Revisit when:** the AWS administrator answers (other t3 servers in the account, existing commitments, which account buys), or the ARM trial changes the instance family.

## ADR-003: Publishing route and first-release scope

- **Status:** Accepted by Kishore, 2026-11-05 (direction only; details to be proved by the prototype).
- **Proposal:** first run RecAI as a private custom connector inside Estuate's own Claude organisation (no Anthropic review, uses the same technology). Submit to the public Connectors Directory later, with a reduced scope: search with citations, read-only. Keep candidate screening and ranking out of the public release until Anthropic's policy is verified on a primary page.
- **Why:** accounts are admin-created and there is no tenant model, so a public listing has no way for outsiders to sign up. A secondary source says Anthropic's usage policy from 2026-11-12 treats candidate screening and ranking as high-risk.
- **Amendment 2026-11-05 (owner direction, CODEX-016):** release one is not capped at evidence search. Include as much of Akshay's functionality and as many useful additions as can be proved accurate, secure, reliable and policy-compatible. Each feature ships only when it passes its own gate (see PLAN.md, "Release-one feature gates"). Scoring, ranking and `start_screening` stay off the public tool list until policy, meaningful human review, disclosure, authorisation and quality are proved; free distribution and internal use are not exemptions. Video interviews are excluded (no registered API, no verified end-to-end path). Assumed case-study outcomes and quotes in the branch must not be used in listing copy.
- **Revisit when:** the customer model is decided, the policy is verified, or Estuate wants to sell to other companies.

## ADR-004: Serverless migration

- **Status:** Proposed.
- **Proposal:** move in stages: front end and files to S3 and CloudFront, then a job queue for parsing and screening, then the connector, then the database last (after a Neon or Aurora prototype). Fix security first on the current server.
- **Why:** at 2,000 to 5,000 resumes a month the saving is only about $55/month, so the case rests on no idle servers, isolation and patching. Aurora's wake-up time (up to about 15 seconds) hurts live calls.
- **Revisit when:** a prototype measures real numbers, usage grows, or a customer requires stronger isolation.

## ADR-005: Security baseline

- **Status:** Proposed. See POC-STANDARDS.md.
- **Proposal:** no development fallbacks in deployed code, every query scoped to the caller's tenant and checked by two-user tests, opaque file IDs with private storage, managed or shared token storage, untrusted resume text treated as data, per-tenant quotas.
- **Revisit when:** the identity provider is chosen or Anthropic changes its connector requirements.

## ADR-007: Modernise dependencies as part of the rebuild

- **Status:** Accepted by Kishore, 2026-11-05 (direction only; details to be proved by the prototype).
- **Facts (checked 2026-11-05 against PyPI):** 15 of the 46 pinned packages are never imported (alembic, bcrypt, crawl4ai, google libraries, openai, passlib, pdfplumber, psycopg, redis, reportlab, scikit-learn, SQLAlchemy, python-jose, unstructured directly, gunicorn is runtime only). Nearly all others publish Python 3.14 wheels. `unstructured` (latest 0.27.36) requires Python below 3.14, so 3.13 is the newest version everything supports.
- **Proposal:** fix Phase 0 on the current pins first, with tests as the safety net. Then modernise in waves, each gated by the test suite: (0) prune unused packages, (1) runtime: Python 3.13 (3.14 once `unstructured` is gone), PostgreSQL 17 now and 18 later, Node 24 LTS, pinned base images, lockfile, automated dependency updates, (2) breaking jumps needing code changes: LangChain 0.3 to 1.x (prefer dropping it for the Anthropic SDK), Pinecone 7 to 10, Cohere 5 to 7, pandas 2 to 3, PyMuPDF 1.x to 2.x, (3) architecture: official MCP SDK, managed identity, pgvector evaluation.
- **Licence flag:** PyMuPDF is AGPL or commercial. Needs a legal decision before a public hosted release; permissive alternatives exist.
- **Revisit when:** Phase 0 tests are green, or a pinned package has a security advisory.

## ADR-008: Rebuild as pay-per-use serverless on AWS (after a prototype)

- **Status:** Accepted by Kishore, 2026-11-05 (direction only; details to be proved by the prototype).
- **Proposal:** Option A: Cognito, API Gateway with token check, separate Lambda roles, DynamoDB, private S3, S3 Vectors and Bedrock Titan embeddings, queue-driven parser (no internet) and screening worker, Claude API with Haiku 5.5 first, batch and cached prompts. Release one is free, read-only evidence search with citations; screening and ranking stay internal (Anthropic Usage Policy, 12 Nov 2026). Estimated idle infrastructure about $3 to 4 per month against $73 today; all-in about $10 to 40 per month in lean and balanced cases against about $157 today. All estimates; nothing measured on AWS yet.
- **Alternatives kept:** Option C (serverless plus RDS PostgreSQL with pgvector, about $17) if SQL skills matter; Option B (one small server, about $21 to 33) for the fastest port.
- **Must be proved first (1 to 2 week prototype, synthetic data, owner's AWS account):** Claude sign-in through Cognito with Anthropic-held credentials; search quality on the Codex benchmark; Haiku 5.5 screening quality; latency inside Claude's tool timeout; isolated parser; PDF library licence; thin-slice test (upload, find, other user blocked, delete, gone).
- **Revisit when:** the prototype numbers are in, Anthropic changes connector or policy rules, or usage differs a lot from Akshay's low-end volumes.

## ADR-006: Documentation and handoff standard

- **Status:** Accepted, 2026-11-05.
- **Decision:** continuity files at the root (STATUS, HISTORY, DECISIONS, PLAN), updated after every task. No tables in markdown. Stakeholder deliverables in Word. Review entries exchanged with ChatGPT through the shared folder with sequential IDs.
- **Revisit when:** the folder becomes a git repository or a team joins.
