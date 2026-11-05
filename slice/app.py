"""Loopback-only synthetic prototype. No production token issuer is configured."""
import asyncio
from contextvars import ContextVar
from hmac import compare_digest
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Protocol

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from starlette.responses import JSONResponse, Response

from core import Evidence, MAX_BYTES, MemoryStore, PhraseIndex

identity_context = ContextVar("identity")
FIXTURE_TOKENS = {"synthetic-alice": ("tenant-a", "alice"), "synthetic-bob": ("tenant-b", "bob"),
                  "synthetic-carol": ("tenant-a", "carol")}


class TokenVerifier(Protocol):
    def verify(self, token: str) -> tuple[str, str] | None: ...


class LocalFixtureVerifier:
    def verify(self, token):
        return next((identity for candidate, identity in FIXTURE_TOKENS.items()
                     if compare_digest(candidate.encode(), token.encode())), None)


class RequireTenant:
    def __init__(self, app, verifier):
        self.app, self.verifier = app, verifier

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        scheme, _, credential = headers.get(b"authorization", b"").decode("latin-1").partition(" ")
        identity = self.verifier.verify(credential) if scheme.lower() == "bearer" else None
        if identity is None:
            return await JSONResponse({"error": "unauthorized"}, 401,
                                      headers={"WWW-Authenticate": "Bearer"})(scope, receive, send)
        token = identity_context.set(identity)
        try:
            await self.app(scope, receive, send)
        finally:
            identity_context.reset(token)


def extract(body, kind):
    command = [sys.executable, str(Path(__file__).with_name("extract.py")), kind]
    result = subprocess.run(command, input=body, capture_output=True, timeout=8)
    if result.returncode:
        raise ValueError("document extraction failed")
    return json.loads(result.stdout)


def build_app(evidence, verifier):
    server = FastMCP("RecAI synthetic evidence", stateless_http=True, json_response=True)
    parse_slots = asyncio.Semaphore(2)

    @server.tool(structured_output=True, annotations=ToolAnnotations(title="Search resume evidence", readOnlyHint=True, destructiveHint=False))
    def search_evidence(query: str, top_k: int = 3) -> dict[str, Any]:
        return evidence.search(*identity_context.get(), query, top_k)

    @server.tool(structured_output=True, annotations=ToolAnnotations(title="Get a source citation", readOnlyHint=True, destructiveHint=False))
    def get_citation(document_id: str, passage_id: str) -> dict[str, Any]:
        citation = evidence.citation(*identity_context.get(), document_id, passage_id)
        return {"status": "evidence", "citation": citation} if citation else {"status": "no_evidence"}

    @server.custom_route("/documents/{document_id}", methods=["PUT", "GET", "DELETE"])
    async def documents(request):
        document_id = request.path_params["document_id"]
        if not re.fullmatch(r"[a-f0-9]{32}", document_id):
            return JSONResponse({"error": "invalid document ID"}, 400)
        tenant, subject = identity_context.get()
        if request.method == "GET":
            document = evidence.document(tenant, subject, document_id)
            if document is None:
                return JSONResponse({"error": "not found"}, 404)
            return Response(document.original, media_type="application/octet-stream",
                            headers={"Content-Disposition": "attachment", "Cache-Control": "no-store"})
        if request.method == "DELETE":
            if not evidence.delete(tenant, subject, document_id):
                return JSONResponse({"error": "not found"}, 404)
            return Response(status_code=204)

        kind = request.query_params.get("format")
        if kind not in {"text", "pdf", "docx"}:
            return JSONResponse({"error": "unsupported format"}, 415)
        if parse_slots.locked():
            return JSONResponse({"error": "upload capacity reached"}, 429)
        async with parse_slots:
            body = bytearray()
            try:
                async with asyncio.timeout(8):
                    async for chunk in request.stream():
                        if len(body) + len(chunk) > MAX_BYTES:
                            return JSONResponse({"error": "document too large"}, 413)
                        body.extend(chunk)
                anchors = await asyncio.to_thread(extract, bytes(body), kind)
                evidence.ingest(tenant, subject, document_id, bytes(body), anchors)
            except (TimeoutError, subprocess.TimeoutExpired):
                return JSONResponse({"error": "upload or extraction timed out"}, 408)
            except PermissionError:
                return JSONResponse({"error": "not found"}, 404)
            except ValueError:
                return JSONResponse({"error": "invalid document or conflicting document ID"}, 422)
        return JSONResponse({"document_id": document_id, "status": "ready"})

    return RequireTenant(server.streamable_http_app(), verifier)


app = build_app(Evidence(MemoryStore(), PhraseIndex()), LocalFixtureVerifier())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)


