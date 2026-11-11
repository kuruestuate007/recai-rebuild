## CLAUDE-015 — Region decided

**Peer read through:** CODEX-018

- The owner chose **Ohio (`us-east-2`)**. Set it as the default region variable, set it explicitly in the provider block (the AWS profile's own default is Zurich and must not leak in), and use Ohio prices in the cost plan. The verified price list is in `Citation_generator\docs\rebuild-design-notes.md`.
- Still required before any apply: pinned account id, project tag, owner's approval of the cost numbers.
