# RecAI first release verification plan

This supplements PLAN.md with proposed tests and test data. A feature enters the listing or companion portal when its own checks pass. Record the commit, fixtures, test run and outcome for every feature we advertise.

| Feature and surface | How to prove it |
| --- | --- |
| Cited search and chat in Claude | Use an independently authored, blind synthetic set with direct evidence, aliases, negation, conflicting statements, exposure-only mentions, same-workspace strangers and cross-tenant duplicates. Verify exact source text and anchors, measure evidence recall and false positives on answerable and empty cases separately, and run the same examples in a real Claude client. |
| Portal intake, processing status and file library | Upload synthetic PDF, DOCX and text, with one scanned or unsupported specimen and one malformed file. Confirm accurate ready or failed status, retry safety, correct owner's list, denial for both unauthorized identities, and deletion from original storage, evidence and search after restart. |
| Source links | Issue a short-lived link after checking an authorized synthetic document. Confirm the wrong account cannot mint it, the URL is scoped to one object, and it expires. If the link is a bearer URL, verify the documented replay window and ensure logs redact it. |
| Neutral job-description evidence mapping | Use a synthetic job description with a mix of supported, unsupported, and ambiguous requirements. Match every supported row to the right excerpt and mark gaps explicitly. Adversarial prompts asking for an applicant score, rank or recommendation must not cause the tool to produce one. |
| Cited evidence export | Export only authorized, selected excerpts from a synthetic job and candidate set. Compare every row and citation with the on-screen output. Check export authorization, retention, spreadsheet formula injection, and separate users exporting the same display name. |
| Requisitions | Two users and an administrator create, list, update and archive synthetic jobs. Verify the intended role matrix, exact success, cross-user denial, and audit records. |
| Account administration | Use fixture users with each role. Test invitation, role changes, disable and revoke, with no permission escalation or stale access after the documented revocation window. |
| Report history and downloads | Seed synthetic reports with duplicate names, deleted reports and a hostile filename. Assert the authorized download contains exactly the owner's bytes, foreign IDs fail, and no writer can escape its artifact namespace. Scored reports require their separate policy and quality review. |
| Template conversion and preview | Convert a synthetic PDF and DOCX containing dates, titles, skills and one ambiguity. Compare the generated content with source facts. Exercise preview, edit, regenerate and download with owner success, denial for another user, and unchanged victim bytes. Test duplicate display names and ambiguous legacy rows. |
| Public synthetic demo | A new reviewer can try the advertised use cases with fictional data. Verify that the demo has no path to real workspaces, no upload or scoring capability, and a tested rate limit and shutdown control. |

## First priority

The current templated holdout returns false evidence on 6 of 12 empty-label questions. The failure is a distinction between a skill mention and evidence of experience. Have one reviewer write the blind questions and labels, freeze them before tuning, then compare conservative abstention with the current baseline. Include counterexamples that mention both an actual skill and an unrelated negation in one passage. Track missed valid evidence as well as false answers. Keep this outcome separate from authorization checks and record cold and warm latency and per-workflow cost before choosing a release configuration.
