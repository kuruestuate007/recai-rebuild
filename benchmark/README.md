# RecAI retrieval benchmark

This benchmark is the first local slice of the rebuild. It contains 60 synthetic profiles, 120 page passages, and 60 labelled queries. The generator uses fictional profiles and template wording. The data is a smoke test for search and citation behavior. Add independently authored layouts, paraphrases, dates, tables, scans, extraction errors and misleading passages before using it to select an architecture.

## Run locally

From this directory, run:

```sh
node generate.mjs
node run.mjs
```

The run uses Node built-ins and local fixtures. It needs no cloud account, credentials, dependencies or model calls. The generated JSON files can also be loaded into future test adapters.

## Labels and scoring

- The corpus uses two synthetic tenants. The query records include the authenticated tenant and a requested document set. Document IDs are intentionally supplied across the tenant boundary in the adversarial cases. A production adapter must derive identity from verified authentication and resolve document access server-side.
- Five cases per skill cover direct matches, aliases, distractors, missing evidence and unauthorized documents. Expected passages include an exact ID, page number and excerpt.
- Development and holdout are split by skill family. Use development for thresholds and configuration. The published fixture holdout shares templates and is inspectable. Use an independently authored blind set for a production-quality comparison.
- Citation precision is the proportion of returned passages that match the labelled passage, page and text. Evidence recall is the fraction of all expected passages returned. False evidence counts empty-label questions that receive any result. A single wrong-scope response fails the run. Measure user-visible end-to-end latency separately.

## First result

| Split | Citation precision | Evidence recall | False evidence | Wrong scope |
| --- | ---: | ---: | ---: | ---: |
| Development | 34.8% | 66.7% | 6 of 12 | 0 |
| Holdout | 31.8% | 58.3% | 6 of 12 | 0 |

This baseline ranks by token overlap and returns up to three passages. It finds generic word matches and cannot tell a mention from hands-on use. The figures are a starting point and the scope checks apply only to the local adapter. The included in-process timing excludes upload, extraction, identity, network and storage.

## Architecture comparison

1. Add exact phrase and alias retrieval with a calibrated abstention threshold. Keep the token-overlap baseline for comparison.
2. Compare Bedrock embeddings with S3 Vectors and the same embeddings with PostgreSQL and pgvector. Use the same passage boundaries, authorized set and top-k. Record vector-index and embedding settings.
3. Run the existing Pinecone/Cohere path against the same extracted evidence in an isolated test setup. Compare with and without reranking. Measure added latency and cost.
4. Run each candidate against the independently labelled evaluation set. Reject any authorization failure or incorrect source attribution. Compare evidence precision, recall and abstention by query category. Check cold and warm p95 and cost per thousand searches separately from ingestion and OCR. Measure the chosen path through the actual Claude connector before launch.
