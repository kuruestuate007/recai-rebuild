"""Run the local retrieval methods over the MCP HTTP tool contract."""
import argparse
import json
from pathlib import Path
import re
from statistics import quantiles
from time import perf_counter

from starlette.testclient import TestClient

from acceptance import tool
from app import LocalFixtureVerifier, build_app
from core import Document, Evidence, MemoryStore, Passage, PhraseIndex


class TokenIndex(PhraseIndex):
    def search(self, tenant, query, limit, allowed):
        terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        hits = []
        for (owner, document_id), passages in self.passages.items():
            if owner != tenant or not allowed(document_id):
                continue
            for passage in passages:
                score = len(terms & set(re.findall(r"[a-z0-9]+", passage.text.lower())))
                if score:
                    hits.append((score, document_id, passage.id))
        hits.sort(key=lambda hit: -hit[0])
        return [(doc, passage) for _, doc, passage in hits[:limit]]


def manual_examples():
    return [
        ("java-negative", "Where did they use Java?", "Built a JavaScript checkout page.", False),
        ("spark-negative", "Find Apache Spark experience.", "Set up SparkPost for email delivery.", False),
        ("phrase", "Find infrastructure as code evidence.", "Reviewed application code with the infrastructure team.", False),
        ("alias-positive", "Where did they use PostgreSQL?", "Migrated billing tables to Postgres.", True),
        ("typo-positive", "Where did they use Kubernets?", "Operated Kubernetes in a test cluster.", True),
    ]


def samples(folder):
    docs = json.loads((folder / "corpus.json").read_text(encoding="utf-8"))
    queries = json.loads((folder / "queries.json").read_text(encoding="utf-8"))
    for query in queries:
        selected = [doc for doc in docs if doc["id"] in query["allowedDocuments"]]
        labels = [(p["id"], f'page {p["page"]}', p["text"]) for p in query["expected"]]
        yield query["split"], selected, query["question"], labels
    for name, question, text, positive in manual_examples():
        doc = {"id": name, "tenant": "tenant-a", "pages": [{"id": name, "page": 3, "text": text}]}
        yield "manual_challenges", [doc], question, [(name, "page 3", text)] if positive else []


def evaluate(index, folder):
    store = MemoryStore()
    scores = {}
    with TestClient(build_app(Evidence(store, index), LocalFixtureVerifier()), base_url="http://127.0.0.1:8765") as client:
        for split, selected, question, labels in samples(folder):
            store.documents.clear()
            index.passages.clear()
            owners = {}
            for doc in selected:
                owner = doc["tenant"]
                doc_id = doc["id"]
                owners[doc_id] = owner
                passages = tuple(Passage(p["id"], doc_id, p["text"], f'page {p["page"]}') for p in doc["pages"])
                store.put(owner, doc_id, Document("fixture", b"", passages, "alice" if owner == "tenant-a" else "bob"))
                index.put(owner, doc_id, passages)

            started = perf_counter()
            response = tool(client, "search_evidence", {"query": question})
            elapsed = (perf_counter() - started) * 1000
            hits = response["evidence"]
            assert all(owners[hit["document_id"]] == "tenant-a" for hit in hits)
            scores.setdefault(split, []).append((labels, hits, elapsed))

    for split, rows in scores.items():
        expected_docs = {p["id"]: d["id"] for d in json.loads((folder / "corpus.json").read_text(encoding="utf-8"))
                         for p in d["pages"]}
        expected_docs.update({name: name for name, _, _, _ in manual_examples()})
        returned = sum(len(hits) for _, hits, _ in rows)
        expected = sum(len(labels) for labels, _, _ in rows)
        matched = sum((h["id"], h["anchor"], h["text"]) in labels for labels, hits, _ in rows for h in hits)
        doc_hits = sum(h["document_id"] in {expected_docs[label[0]] for label in labels}
                       for labels, hits, _ in rows for h in hits)
        page_hits = sum((h["document_id"], h["anchor"]) in {(expected_docs[label[0]], label[1]) for label in labels}
                        for labels, hits, _ in rows for h in hits)
        abstained = sum(not hits for _, hits, _ in rows)
        correct_abstentions = sum(not hits and not labels for labels, hits, _ in rows)
        false_evidence = sum(bool(hits) and not labels for labels, hits, _ in rows)
        ratio = lambda a, b: round(a / b, 3) if b else None
        print(json.dumps({"method": type(index).__name__, "split": split,
                          "citation_precision": ratio(matched, returned), "evidence_recall": ratio(matched, expected),
                          "document_precision": ratio(doc_hits, returned), "page_precision": ratio(page_hits, returned),
                          "no_evidence_precision": ratio(correct_abstentions, abstained), "false_evidence": false_evidence,
                          "http_in_process_p95_ms": round(quantiles([t for _, _, t in rows], n=20, method="inclusive")[-1], 2)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).resolve().parent.parent / "benchmark")
    args = parser.parse_args()
    for index in (TokenIndex(), PhraseIndex()):
        evaluate(index, args.fixtures)


