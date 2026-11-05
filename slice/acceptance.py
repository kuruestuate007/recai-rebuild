"""Run the synthetic lifecycle in-process or against a dedicated prototype URL."""
import argparse
import io
import uuid

import httpx
from starlette.testclient import TestClient

from app import LocalFixtureVerifier, build_app
from core import Evidence, MAX_BYTES, MemoryStore, PhraseIndex

ALICE = {"Authorization": "Bearer synthetic-alice"}
BOB = {"Authorization": "Bearer synthetic-bob"}
CAROL = {"Authorization": "Bearer synthetic-carol"}


def rpc(client, method, params=None, auth=ALICE):
    return client.post("/mcp", headers={**auth, "Accept": "application/json, text/event-stream"},
                       json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})


def tool(client, name, arguments, auth=ALICE):
    response = rpc(client, "tools/call", {"name": name, "arguments": arguments}, auth)
    assert response.status_code == 200, response.status_code
    payload = response.json()["result"]
    assert not payload.get("isError"), payload
    return payload["structuredContent"]


def lifecycle(client):
    document_id = uuid.uuid4().hex
    path = f"/documents/{document_id}"
    original = b"Synthetic evidence: deployed Kubernetes to a fictional test cluster."

    tools = rpc(client, "tools/list").json()["result"]["tools"]
    assert {tool["name"] for tool in tools} == {"search_evidence", "get_citation"}
    assert all(tool["annotations"]["readOnlyHint"] and tool["annotations"]["title"] for tool in tools)
    assert rpc(client, "tools/call", {"name": "search_evidence", "arguments": {"query": "K8s"}},
               auth={}).status_code == 401
    assert client.put(path + "?format=text", headers=ALICE, content=b"x" * (MAX_BYTES + 1)).status_code == 413
    for headers in (ALICE, BOB):
        assert client.put(path + "?format=text", headers=headers, content=original).status_code == 200
        assert client.put(path + "?format=text", headers=headers, content=original).status_code == 200

    try:
        result = tool(client, "search_evidence", {"query": "K8s"})
        assert len(result["evidence"]) == 1
        citation = result["evidence"][0]
        assert citation["text"] == original.decode() and citation["anchor"] == "section 1"
        args = {"document_id": document_id, "passage_id": citation["id"]}
        assert tool(client, "get_citation", args)["citation"] == citation
        assert client.get(path, headers=ALICE).content == original

        assert client.get(path, headers=CAROL).status_code == 404
        assert client.put(path + "?format=text", headers=CAROL, content=original).status_code == 404
        assert client.delete(path, headers=CAROL).status_code == 404
        assert tool(client, "get_citation", args, CAROL) == {"status": "no_evidence"}
        assert tool(client, "search_evidence", {"query": "K8s"}, CAROL)["evidence"] == []
        assert client.delete(path, headers=BOB).status_code == 204
        assert client.get(path, headers=BOB).status_code == 404
        assert tool(client, "get_citation", args, BOB) == {"status": "no_evidence"}
        assert tool(client, "search_evidence", {"query": "K8s"}, BOB)["evidence"] == []
        assert client.delete(path, headers=BOB).status_code == 404
        assert client.get(path, headers=ALICE).content == original

        assert client.delete(path, headers=ALICE).status_code == 204
        assert client.get(path, headers=ALICE).status_code == 404
        assert tool(client, "get_citation", args) == {"status": "no_evidence"}
        assert tool(client, "search_evidence", {"query": "K8s"})["evidence"] == []
    finally:
        client.delete(path, headers=ALICE)
        client.delete(path, headers=BOB)


def relevance_check():
    evidence = Evidence(MemoryStore(), PhraseIndex())
    evidence.ingest("tenant-a", "alice", "alias", b"Used Postgres.", [("page 1", "Used Postgres.")])
    evidence.ingest("tenant-a", "alice", "direct", b"Used PostgreSQL.", [("page 1", "Used PostgreSQL.")])
    result = evidence.search("tenant-a", "alice", "PostgreSQL", 1)
    assert result["evidence"][0]["document_id"] == "direct"


def parser_checks():
    from docx import Document
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    from app import extract

    docx = Document()
    docx.add_paragraph("Synthetic DOCX evidence.")
    buffer = io.BytesIO()
    docx.save(buffer)
    assert extract(buffer.getvalue(), "docx") == [["paragraph 1", "Synthetic DOCX evidence."]]

    pdf = PdfWriter()
    page = pdf.add_blank_page(612, 792)
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({
            NameObject("/F1"): DictionaryObject({
                NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }),
        }),
    })
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 50 720 Td (Synthetic PDF evidence.) Tj ET")
    page[NameObject("/Contents")] = pdf._add_object(stream)
    buffer = io.BytesIO()
    pdf.write(buffer)
    assert extract(buffer.getvalue(), "pdf") == [["page 1", "Synthetic PDF evidence."]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", help="Dedicated synthetic prototype with the fixture verifier")
    args = parser.parse_args()
    if args.base_url:
        with httpx.Client(base_url=args.base_url, timeout=15, follow_redirects=False) as client:
            lifecycle(client)
    else:
        store, index = MemoryStore(), PhraseIndex()
        with TestClient(build_app(Evidence(store, index), LocalFixtureVerifier()), base_url="http://127.0.0.1:8765") as client:
            lifecycle(client)
        assert store.documents == {} and index.passages == {}
        parser_checks()
        relevance_check()
    print("Synthetic acceptance checks passed.")



