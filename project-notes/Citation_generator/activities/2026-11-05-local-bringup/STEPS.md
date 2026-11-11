# Bring RecAI up locally

Date: 2026-11-05. Owner: Kishore Kunal. Branch: `estuate/local-bringup` in the Estuate repo (commits b961414 and the line-ending commit after it, local only, not pushed). Status: RUN on 2026-11-05. Database and backend start; login, session, chat threads and file list return 200. Upload, search, chat and screening not tested (need the outside API keys). Front end not started.

## Purpose

Run the backend and a PostgreSQL database on the laptop to see the app work, and learn what blocks a first start, before building the AWS setup.

## What the app needs to start

- **PostgreSQL: required.** Login, users, files, chat threads, screening batches and reports all live there. The app cannot run without it. Any PostgreSQL 14 or newer works, as long as the `pgcrypto` extension is available. It does not have to be the production database or contain production data.
- **A schema the code agrees with: currently missing.**
  - `core.bulk_screening_results` and `core.document_chunks` are used by the code but exist in no SQL file in the repo.
  - `core.users.is_active` is used by the code but `table.sql` never creates it (patched in `docker/initdb/03-schema-patch.sql`).
  - The correct fix is a schema-only dump from production (`pg_dump --schema-only`): structure only, no data. Akshay or whoever has production access runs it. Do not guess column types.
- **Outside services, only for the features that call them:**
  - Pinecone (API key and index name): upload, search, chat, screening.
  - OpenAI (embeddings), Cohere (rerank), Anthropic (chat, screening, resume conversion).
  - With the keys empty the app still starts, and login and user pages work.
- **System tools, only for some features:** Tesseract (scanned resumes), LibreOffice (DOCX to PDF), FFmpeg. The Dockerfile installs the first and last; LibreOffice is optional (`WITH_LIBREOFFICE=true`).
- **Python:** this laptop has only 3.14, which the pinned packages do not support. The Docker image uses 3.12.

## Prerequisites

- Docker Desktop started (the Docker command-line tool is installed but its engine was not running on 2026-11-05).
- A `.env` file made from `.env.example`. Passwords, the cookie-signing key and API keys are filled in by Kishore. Never commit or share them.
- Node.js (installed) for the React front end.

## Steps

1. Start Docker Desktop and wait until it says it is running.
2. In `mcp-code/citation_generator`, copy `.env.example` to `.env` and fill the values (db password, secret_key, DEV_ADMIN_EMAIL and DEV_ADMIN_PASSWORD at minimum).
3. Start the stack: `docker compose up --build`. First run builds the image (slow) and creates the database, runs the SQL scripts and seeds the admin user.
4. Check the backend: open `http://localhost:8000/` (expect `{"message": "Backend is running"}`) and `http://localhost:8000/docs`.
5. Start the front end in a second terminal: `cd frontend`, `npm install --legacy-peer-deps`, `npm run dev`, then open `http://localhost:5173` and sign in with the admin email and password from `.env`.

## Verification

- `docker compose ps` shows `db` healthy and `app` running.
- Sign-in succeeds. The `/user/session` call returns the admin user.
- Upload, search, chat and screening will fail until the two missing tables exist and the outside keys are set. That is expected.

## Rollback

- `docker compose down -v` removes the containers and the database volume. Nothing else on the laptop is changed.

## Gotchas

- **The repo SQL cannot build a database.** Found by running it: `table.sql` alters `core.bulk_screening_results` before it exists, references `core.screening_batches` before it exists, and re-adds columns that already exist. The code also reads columns no SQL creates: `users.is_active`, `screening_batches.is_deleted`, `screening_batches.deleted_at`, `files.processing_state`, `chat_threads.is_deleted`. `docker/initdb/01-schema-draft.sql` (generated) and `03-schema-patch.sql` work around this with guessed types. Replace with the production dump.
- **Errors are swallowed.** A missing `chat_threads.is_deleted` made `/chat/threads` return an empty list instead of failing. Real problems can hide behind empty results.
- The image built first time on Python 3.12: all pinned packages install.
- On Windows Git Bash, add `MSYS_NO_PATHCONV=1` before `docker compose exec -w /app ...` or the path is mangled.
- **Finding 1 reproduced by running the code** (inside the container, fake request, no network): with `MCP_DEV_MODE` unset a remote caller gets role admin; with it set to false a remote caller is refused, but a loopback caller still gets admin.
- `POST /mcp` with `tools/list` and no token returns 200 (discovery is open). Whether `tools/call` is refused without a token still needs a test.
- `core.users` gets a default password `default123` for any row inserted without one (table.sql line 22). The app always sets one, but remove that default.
- The `/job`, `/conversion` and `/mcp` routes are not proxied by the Vite dev server or the production nginx file. Add them when testing those features.
- Compose publishes ports on 127.0.0.1 only, so nothing is reachable from the network.

## Follow-up

- Get the schema-only dump and turn it into proper migrations (Alembic is already in requirements).
- Seed data and a few fake resumes for testing. Never use real candidate data locally.
- Update STATUS.md and HISTORY.md after the first successful start.
