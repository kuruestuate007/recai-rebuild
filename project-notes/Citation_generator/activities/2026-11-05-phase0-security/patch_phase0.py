import re
from pathlib import Path

R = Path(r"D:/2026-estuate/Anthropic-app-publishing/Citation_generator/mcp-code/citation_generator")


def rw(rel, fn):
    p = R / rel
    s = p.read_text(encoding="utf-8")
    new = fn(s)
    assert new != s, f"no change made in {rel}"
    p.write_text(new, encoding="utf-8", newline="\n")
    print("patched", rel)


# ---------------------------------------------------------------- new helper module
(R / "utils" / "safe_paths.py").write_text('''"""Safe handling of client-supplied file names and per-user upload locations."""
import os
import uuid
from pathlib import PurePosixPath, PureWindowsPath


def safe_filename(name: str) -> str:
    """Return only the final path component of a client-supplied file name.

    Strips directories written with either / or \\\\ and null bytes. Raises ValueError when nothing usable is left.
    """
    if not name:
        raise ValueError("empty file name")
    cleaned = str(name).replace("\\x00", "")
    base = PurePosixPath(PureWindowsPath(cleaned).name).name.strip()
    if not base or base in (".", ".."):
        raise ValueError("invalid file name")
    return base


def user_upload_path(upload_dir: str, user_id: str, filename: str) -> str:
    """Path for a user's upload: <upload_dir>/<user_id>/<safe file name>. Creates the user folder.

    Two users can upload the same file name without touching each other's file, and the result is
    guaranteed to stay inside the user's folder.
    """
    safe = safe_filename(filename)
    uid = str(uuid.UUID(str(user_id)))
    folder = os.path.join(upload_dir, uid)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, safe)
    root = os.path.realpath(folder)
    if os.path.commonpath([root, os.path.realpath(path)]) != root:
        raise ValueError("path escapes the user folder")
    return path
''', encoding="utf-8", newline="\n")
print("created utils/safe_paths.py")


# ---------------------------------------------------------------- MCP authentication
def oauth(s):
    start = s.index("async def validate_oauth_token(request: Request) -> dict:")
    head = s[:start]
    new_tail = '''async def validate_oauth_token(request: Request) -> dict:
    """
    Authenticate an MCP request.

    The ONLY accepted credential is an OAuth access token issued by this server's /oauth/token endpoint,
    sent as "Authorization: Bearer <token>". Cookies, web-session tokens, developer keys and localhost
    shortcuts are deliberately not accepted. Anything else raises 401 with the discovery header.
    """
    _cleanup_expired()
    base_url = str(request.base_url).rstrip("/")
    auth_headers = {
        "WWW-Authenticate": f'Bearer resource_metadata="{base_url}/.well-known/oauth-protected-resource"'
    }

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer ") or not auth_header[7:].strip():
        raise HTTPException(status_code=401, detail="Missing Bearer access token", headers=auth_headers)
    token = auth_header[7:].strip()

    token_data = _access_tokens.get(token)
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid or expired access token", headers=auth_headers)
    if token_data["expires_at"] < time.time():
        _access_tokens.pop(token, None)
        raise HTTPException(status_code=401, detail="Access token has expired", headers=auth_headers)
    return {
        "user_id": token_data["user_id"],
        "username": token_data["username"],
        "email": token_data["email"],
        "role": token_data["role"],
        "authenticated": True,
    }


async def get_optional_oauth_token(request: Request) -> Optional[dict]:
    """User context if a valid token was sent, otherwise None. Never invents an identity.

    Used so that discovery methods (initialize, tools/list) work without a token; tools/call still
    requires authentication in process_jsonrpc_request.
    """
    try:
        return await validate_oauth_token(request)
    except HTTPException:
        return None
'''
    return head + new_tail


rw("mcp_server/oauth.py", oauth)


# ---------------------------------------------------------------- report download
def folderp(s):
    start = s.index('@folder_processer_router.get("/download_report/{filename}")')
    end = s.index('@folder_processer_router.post("/process_folder")')
    new = '''@folder_processer_router.get("/download_report/{filename}")
async def download_report(filename: str, session = Depends(login_required)):
    """Serve a generated screening report. Owner or admin only."""
    if session is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        safe_name = safe_filename(filename)
    except ValueError:
        raise HTTPException(status_code=404, detail="Report not found")
    if safe_name != filename:
        raise HTTPException(status_code=404, detail="Report not found")

    user_id = session.get('user_id')
    user_role = session.get('role') if isinstance(session, dict) else None

    # Non-admins may only download a report that belongs to one of their own batches.
    if user_role != 'admin':
        clean_name = safe_name[:-5] if safe_name.endswith('.xlsx') else safe_name
        pool = await Database.get_pool()
        async with pool.acquire() as conn:
            batch = await conn.fetchrow("""
                SELECT id FROM core.screening_batches
                WHERE (report_name = $1 OR report_name = $2) AND user_id = $3
                  AND COALESCE(is_deleted, false) = false
            """, clean_name, safe_name, uuid.UUID(user_id))
        if not batch:
            raise HTTPException(status_code=403, detail="Access denied to report file")

    root = os.path.realpath(REPORTS_DIR)
    file_path = os.path.realpath(os.path.join(REPORTS_DIR, safe_name))
    if os.path.commonpath([root, file_path]) != root or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        path=file_path,
        filename=safe_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


'''
    s = s[:start] + new + s[end:]
    s = s.replace("load_dotenv(override=True)  # loads .env from the current working directory",
                  "load_dotenv()  # fills only variables that are not already set; real environment values win")
    old = "        file_name = os.path.basename(uploaded_file.filename)\n"
    assert old in s
    s = s.replace(old, "        try:\n            file_name = safe_filename(uploaded_file.filename)\n        except ValueError:\n            logger.warning(\"--- Skipping upload with an invalid file name ---\")\n            continue\n")
    old = "            new_file_path = os.path.join(UPLOAD_DIR, file_name)\n"
    assert old in s
    s = s.replace(old, "            new_file_path = user_upload_path(UPLOAD_DIR, user_id, file_name)\n")
    first_import = s.index("\nfrom ")
    s = s[:first_import] + "\nfrom utils.safe_paths import safe_filename, user_upload_path" + s[first_import:]
    return s


rw("routes/folderprocesser.py", folderp)


# ---------------------------------------------------------------- single upload
def filepy(s):
    s = s.replace("from hashlib import md5\n", "from hashlib import md5\nfrom utils.safe_paths import safe_filename, user_upload_path\n", 1)
    marker = "        UPLOAD_DIR = \"uploaded_files\"\n        os.makedirs(UPLOAD_DIR, exist_ok=True)\n        file_path = os.path.join(UPLOAD_DIR, file.filename)\n"
    assert marker in s
    s = s.replace(marker,
                  "        try:\n            safe_name = safe_filename(file.filename)\n        except ValueError:\n"
                  "            raise HTTPException(status_code=400, detail=\"Invalid file name\")\n"
                  "        UPLOAD_DIR = \"uploaded_files\"\n        os.makedirs(UPLOAD_DIR, exist_ok=True)\n"
                  "        file_path = user_upload_path(UPLOAD_DIR, user_id, safe_name)\n")
    head, tail = s.split("file_path = user_upload_path(UPLOAD_DIR, user_id, safe_name)\n", 1)
    stop = tail.index('@file_router.get("/list_files")')
    body = tail[:stop].replace("file.filename", "safe_name")
    return head + "file_path = user_upload_path(UPLOAD_DIR, user_id, safe_name)\n" + body + tail[stop:]


rw("routes/file.py", filepy)


# ---------------------------------------------------------------- chat ownership
def chat_thread(s):
    s = s.replace('''async def get_thread_messages(thread_id: str):
    """
    Fetch all messages for a specific thread, ordered by sequence number.
    """''', '''async def thread_owned_by(thread_id: str, user_id: str) -> bool:
    """True only if the thread exists, is not deleted, and belongs to this user."""
    try:
        thread_uuid = uuid.UUID(str(thread_id))
        user_uuid = uuid.UUID(str(user_id))
    except ValueError:
        return False
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        found = await conn.fetchval(
            "SELECT 1 FROM chathistory.chat_threads "
            "WHERE thread_id = $1 AND user_id = $2 AND COALESCE(is_deleted, false) = false",
            thread_uuid, user_uuid)
    return bool(found)


async def get_thread_messages(thread_id: str, user_id: str):
    """
    Fetch all messages for a thread the user owns, ordered by sequence number.
    Returns an empty list when the thread is not the user's.
    """
    if not await thread_owned_by(thread_id, user_id):
        return []''', 1)
    old = '''    async with pool.acquire() as conn:
        async with conn.transaction():
            # Get next sequence number'''
    assert old in s
    s = s.replace(old, '''    async with pool.acquire() as conn:
        async with conn.transaction():
            # Only the thread's owner may write to it (checked inside the same transaction).
            owner = await conn.fetchval(
                "SELECT user_id FROM chathistory.chat_threads "
                "WHERE thread_id = $1 AND COALESCE(is_deleted, false) = false FOR UPDATE",
                thread_uuid)
            if owner is None or str(owner) != str(user_id):
                raise PermissionError("thread not found or not owned by this user")
            # Get next sequence number''', 1)
    return s


rw("db/endpoints/chat_thread.py", chat_thread)


def chat_route(s):
    old = '''    from db.endpoints.chat_thread import get_thread_messages
    messages = await get_thread_messages(thread_id)
    return messages'''
    assert old in s
    s = s.replace(old, '''    from db.endpoints.chat_thread import get_thread_messages, thread_owned_by
    if not await thread_owned_by(thread_id, user_id):
        raise HTTPException(status_code=404, detail="Thread not found")
    messages = await get_thread_messages(thread_id, user_id)
    return messages''')
    old = '''            else:
                logger.info(f"=== Thread ID: {thread_id} ===")'''
    assert old in s
    s = s.replace(old, '''            else:
                from db.endpoints.chat_thread import thread_owned_by
                if not await thread_owned_by(thread_id, user_id):
                    return JSONResponse(status_code=404, content={'error': 'Thread not found.'})
                logger.info(f"=== Thread ID: {thread_id} ===")''')
    return s


rw("routes/chat.py", chat_route)


# ---------------------------------------------------------------- .env must not override the real environment
for rel in ("agents/agents_main.py", "document_processing/docxtpl_converter.py"):
    rw(rel, lambda s: s.replace("load_dotenv(override=True)", "load_dotenv()"))


# ---------------------------------------------------------------- converter: find the user's own upload through the database
def conv(s):
    s = s.replace("    resume_path = uploaded_dir / original_file\n    if not resume_path.exists():\n        logger.error",
                  "    resume_path = await _own_upload_path(user_id, original_file)\n    if resume_path is None or not resume_path.exists():\n        logger.error", 1)
    s = s.replace("    resume_path = uploaded_dir / original_file\n    if not resume_path.exists():\n        raise HTTPException(status_code=404, detail=\"Original resume not found to reprocess.\")",
                  "    resume_path = await _own_upload_path(user_id, original_file)\n    if resume_path is None or not resume_path.exists():\n        raise HTTPException(status_code=404, detail=\"Original resume not found to reprocess.\")", 1)
    helper = '''

async def _own_upload_path(user_id, original_file):
    """Path of the signed-in user's own uploaded file, looked up in the database (never built from client input)."""
    from routes.endpoint.filesendpoint import check_file_exists
    from utils.safe_paths import safe_filename
    try:
        name = safe_filename(original_file)
    except ValueError:
        return None
    row = await check_file_exists(name, user_id)
    return Path(row[2]) if row else None

'''
    idx = s.index("@fileconversionrouter.post(\"/convert\")")
    return s[:idx].rstrip("\n") + helper + "\n" + s[idx:]


rw("routes/fileconverstion.py", conv)
print("done")
