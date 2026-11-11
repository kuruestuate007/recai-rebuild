# Rebuild design notes (input for the architecture document)

Written 2026-11-05 so a new session can build `docs/deliverables/RecAI-Rebuild-Understanding-Architecture-Cost.docx` without redoing the research. Diagram generator: `activities/2026-11-05-rebuild-design/diagrams.py` (Pillow; draws today, proposed, one-search-flow diagrams).

## Goal and constraint (from the owner)

- Rebuild completely if it is better and cheaper, keeping the app's intent. Permission was about $125/month; stretch goal about $25/month. Deploy on AWS, own AWS account as sandbox, synthetic data only until Estuate owns production and approves privacy and security.
- Present to the CEO: where we picked it up, what we built, the pros in simple terms, same workload and feature scope compared old against new, deferred features disclosed.

## Intent of the app (what to keep)

- Recruiters upload resumes; search and chat over them with exact citations; screening against a job description with a report; convert resumes to the Estuate template; job requisitions; admin; a Claude MCP connector (search, screening, reports). A video interview module exists only as a design document (not built).
- Public release one (agreed by Claude and Codex): free, for visibility; read-only evidence lookup with citations and a clear "no evidence" answer; no scoring, ranking, bulk screening, uploads or admin over MCP. Screening and ranking are high-risk under Anthropic's Usage Policy (12 Nov 2026): qualified human review plus disclosure; carve-out stated for non-consumer-facing output. Keep screening internal and separately reviewed.

## Verified prices (AWS public price list, Ohio, read 2026-11-05)

- Lambda: $0.20 per million requests; $0.0000166667 per GB-second (x86); $0.0000133334 per GB-second (Arm).
- API Gateway HTTP API: $1.00 per million requests.
- DynamoDB on demand: $0.125 per million reads, $0.625 per million writes, $0.25 per GB-month beyond 25 GB.
- Cognito: Lite $0.0055 per monthly active user; Essentials $0.015. Free allowance 10,000 users (from AWS documentation snippet; confirm on the pricing page).
- S3 Vectors: storage $0.06 per GB-month; writes $0.20 per GB; queries $0.0000025 per request plus about $0.0000039 per GB processed; $0.01 per GB returned. (AWS cut large-index query charges in June 2026; re-check.)
- Bedrock Titan Text Embeddings V2: $0.00002 per 1,000 tokens ($0.02 per million).
- RDS PostgreSQL db.t4g.micro $0.016 per hour (about $11.68/month) plus gp3 storage $0.115 per GB-month. EC2 (Linux): t4g.micro $6.13/month, t4g.small $12.26, t4g.medium $24.53, t4g.large $49.06, t3.large $60.74, c6g.xlarge $99.28 (730 hours).
- Aurora Serverless v2 about $0.12 per ACU-hour, storage $0.10 per GB-month (third-party blogs, unverified); scale-to-zero resume up to about 15 seconds.
- Claude API (Anthropic skill table, cached 2026-10-06): Haiku 5.5 $0.10 in / $0.50 out per million tokens (prompts up to 100K); Sonnet 5.5 $2 / $10; Opus 5.5 $4 / $20. Batch about half price; cache reads about a tenth.
- Not verified: WAF (about $5 per web ACL plus $1 per rule per month), CloudWatch, S3 standard ($0.023/GB-month), SQS and CloudFront free allowances, Textract.

## Proposed architecture (Option A, serverless)

- Web app: S3 + CloudFront. Sign-in: Cognito (portal and Claude connector; test Anthropic-held client credentials because Cognito has no dynamic client registration). API: API Gateway HTTP API with token authorizer, then Lambda (separate roles for web API and MCP tools).
- Data: DynamoDB (users, jobs, results, chats), private S3 (resumes, reports), S3 Vectors (search index with forced tenant filter), Bedrock Titan embeddings.
- Background: SQS then parser Lambda in a private subnet with only S3 and DynamoDB gateway endpoints (no internet, no NAT, free); screening worker Lambda calling the Claude API (Haiku 5.5 first, Sonnet 5.5 for borderline, batch and cached prompts). No VPC or NAT for other Lambdas; no public IP.
- Idle infrastructure estimate: about $3-4 per month (S3 storage, CloudWatch, tiny DynamoDB). Optional WAF about $6-8.
- The MCP search tool makes no Claude call: the user's own Claude writes the answer, so Estuate's LLM cost for it is zero.

## Cost scenarios (monthly, using Akshay's low-end volumes: 2,000 to 5,000 resumes and screenings, 1,000 to 3,000 chat queries; token assumptions: 3,000-token resume, 1,000-token job description, 700-token structured output)

- Per screening evaluation: Sonnet 5.5 on demand about $0.016; with cached prompt and batch about $0.007; Haiku 5.5 about $0.0008 ($0.0004 batch). Two-stage (Haiku all, Sonnet top 20 percent, batch): 2,000 evals about $3.5; 5,000 evals about $8.7.
- Portal chat per query: Haiku 5.5 about $0.00075; Sonnet 5.5 about $0.015. Resume conversion per file (not in Akshay's estimate): Haiku about $0.002; Sonnet about $0.037.
- Embeddings: 2,000 to 5,000 resumes is about $0.12 to $0.30. S3 Vectors storage and queries under $1.
- Lean (Haiku-first, batch, cached): about $9 to $16 per month all-in. Balanced (Sonnet for screening with batch and cache, Haiku for chat and conversion): about $19 to $40. Premium (Sonnet everywhere, on demand): about $69 to $147. Today: about $157 ($73 hosting + $84 AI). The LLM model choice, not infrastructure, is the largest cost lever. All quality claims for Haiku need an eval.

## Options compared (infrastructure only)

- A: serverless with DynamoDB and S3 Vectors: about $3-4 idle. Cheapest, strongest isolation; most rewrite; new services to prove.
- C: serverless compute with RDS PostgreSQL db.t4g.micro and pgvector: about $17-18. Keeps SQL and team skills.
- B: one small VM (t4g.small to t4g.medium) with Postgres and pgvector: about $21-33 (instance plus disk, public IP $3.65, snapshots, monitoring). Fastest port; always on; single failure point.
- Today: about $73.

## What to prove in a prototype before committing

1. Claude connector sign-in works with Cognito (Anthropic-held client credentials).
2. S3 Vectors search quality and latency against exact and alias search, pgvector and the current Pinecone and Cohere stack, on the Codex benchmark (`...\recai-rebuild\benchmark`).
3. Haiku 5.5 screening quality against Sonnet 5.5 on a labelled sample.
4. Lambda cold start and end-to-end latency inside Claude's tool timeout.
5. The parsing pipeline (LibreOffice, OCR) in an isolated worker.
6. PyMuPDF licence decision or a replacement.

## Features: keep, change, defer

- Keep: resume ingestion, search with citations, internal screening with human review, Excel export, resume conversion (internal), job requisitions, admin (via Cognito groups).
- Defer or drop: video interview (unbuilt, high-risk, biometrics), Tavily web search in chat (SSRF and injection surface).
- Add: audit log, per-tenant quotas, kill switch, budgets, retrieval and screening eval suites, tests that assert denial and success.

## Document outline for the CEO and owner

1. Where we picked it up (today's diagram, cost, risks closed). 2. What the app is for. 3. Proposed design in plain words (proposed diagram) and one search step by step. 4. Cost old against new at the same workload, three model scenarios. 5. Options compared. 6. Security by design (each flaw found becomes impossible by construction). 7. What we must prove first and how long it takes (rough: prototype 1 to 2 weeks, build several weeks; refine after prototype). 8. Decisions needed.
