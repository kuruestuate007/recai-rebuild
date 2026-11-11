# RecAI end-to-end analysis, serverless options and security review

Date: 2026-11-05. Owner: Kishore Kunal. Related ADRs: ADR-003, ADR-004, ADR-005.

## Purpose

Understand the RecAI app after taking ownership, judge how it would be built better, explore serverless to avoid idle cost, and find what must be fixed before a public Claude listing. Nothing was installed or changed on any system.

## Prerequisites

- Read access to `mcp-code/citation_generator` (branch `feature/mcp-connector`, commit 95ef749).
- Read access to the ChatGPT shared review folder (`C:\Users\kikunal\Documents\ChatGPT\Citation-genrator\shared-review\`).

## Steps

1. Extracted the branch to a scratch folder with `git archive origin/feature/mcp-connector` (no change to the repository).
2. Read the entry point, auth, MCP server, upload, chat, report and database code. Searched for string-built SQL, subprocess calls, archive extraction and role checks.
3. Verified each of ChatGPT's findings (CODEX-001) against the code and added new ones.
4. Researched current Anthropic and AWS documentation and vendor pricing for the serverless options.
5. Wrote `docs/deliverables/RecAI-Analysis-Serverless-Security-Plan.docx` and the root standards.
6. Posted CLAUDE-001 to the shared folder.

## Verification

- Finding evidence is given as `file:line` for commit 95ef749. All findings are static (read), not executed.
- The `git rev-parse` commits matched ChatGPT's (95ef749 and 7f8ffed).

## Rollback

- Delete the root standards files and the new Word document. No other change was made. The scratch extraction is in the session scratchpad.

## Gotchas

- The live server was not checked. Whether `/mcp` is reachable, and whether the development mode is on there, is unverified.
- The statement that Anthropic's 2026-11-12 policy names candidate screening as high-risk comes from a secondary source and is unverified.

## Follow-up

- STATUS.md, HISTORY.md and DECISIONS.md updated. Phase 0 fixes are next (PLAN.md).
