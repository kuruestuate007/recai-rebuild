from dataclasses import asdict, dataclass
from hashlib import sha256
from threading import RLock
from typing import Protocol
import re
import uuid

MAX_BYTES = 2 * 1024 * 1024
ALIASES = (("kubernetes", "k8s"), ("postgresql", "postgres"), ("amazon s3", "s3"),
           ("sap integration suite", "sap cpi"), ("continuous integration", "ci"),
           ("infrastructure as code", "iac"), ("single sign-on", "sso"),
           ("disaster recovery", "dr"), ("apache kafka", "kafka"),
           ("access control", "rbac"), ("optical character recognition", "ocr"),
           ("openid connect", "oidc"), ("java",), ("spark",))


@dataclass(frozen=True)
class Passage:
    id: str
    document_id: str
    text: str
    anchor: str


@dataclass(frozen=True)
class Document:
    digest: str
    original: bytes
    passages: tuple[Passage, ...]
    owner: str


class Store(Protocol):
    def get(self, tenant: str, document_id: str) -> Document | None: ...
    def put(self, tenant: str, document_id: str, doc: Document) -> None: ...
    def delete(self, tenant: str, document_id: str) -> None: ...


class Index(Protocol):
    def put(self, tenant: str, document_id: str, passages: tuple[Passage, ...]) -> None: ...
    def delete(self, tenant: str, document_id: str) -> None: ...
    def search(self, tenant: str, query: str, limit: int, allowed) -> list[tuple[str, str]]: ...


class MemoryStore:
    def __init__(self):
        self.documents = {}

    def get(self, tenant, document_id):
        return self.documents.get((tenant, document_id))

    def put(self, tenant, document_id, doc):
        self.documents[tenant, document_id] = doc

    def delete(self, tenant, document_id):
        self.documents.pop((tenant, document_id), None)


def contains(text, term):
    return re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text) is not None


class PhraseIndex:
    def __init__(self):
        self.passages = {}

    def put(self, tenant, document_id, passages):
        self.passages[tenant, document_id] = passages

    def delete(self, tenant, document_id):
        self.passages.pop((tenant, document_id), None)

    def search(self, tenant, query, limit, allowed):
        query = query.casefold().strip()
        groups = [group for group in ALIASES if any(contains(query, term) for term in group)]
        terms = {term for group in groups for term in group} or {query}
        direct = {term for term in terms if contains(query, term)}
        results = []
        for (owner, document_id), passages in self.passages.items():
            if owner != tenant or not allowed(document_id):
                continue
            for passage in passages:
                excerpt = passage.text.casefold()
                matches = {term for term in terms if contains(excerpt, term)}
                if matches:
                    score = len(matches) + len(matches & direct)
                    results.append((-score, document_id, passage.id))
        return [(doc, passage) for _, doc, passage in sorted(results)[:limit]]


class Evidence:
    def __init__(self, store: Store, index: Index):
        self.store, self.index = store, index
        self.lock = RLock()

    def ingest(self, tenant, subject, document_id, original, anchors):
        if not original or len(original) > MAX_BYTES:
            raise ValueError("invalid upload size")
        digest = sha256(original).hexdigest()
        passages = tuple(
            Passage(sha256(f"{document_id}:{digest}:{anchor}:{offset}".encode()).hexdigest()[:32],
                    document_id, text[offset:offset + 900], anchor)
            for anchor, text in anchors for offset in range(0, len(text), 800)
            if text[offset:offset + 900].strip()
        )
        if not passages:
            raise ValueError("no extractable text")
        with self.lock:
            existing = self.store.get(tenant, document_id)
            if existing and existing.owner != subject:
                raise PermissionError("document not found")
            if existing and existing.digest != digest:
                raise ValueError("document ID already used")
            self.store.put(tenant, document_id, Document(digest, original, passages, subject))
            self.index.put(tenant, document_id, passages)
        return document_id

    def document(self, tenant, subject, document_id):
        with self.lock:
            document = self.store.get(tenant, document_id)
            return document if document and document.owner == subject else None

    def citation(self, tenant, subject, document_id, passage_id):
        with self.lock:
            document = self.document(tenant, subject, document_id)
            if document:
                return next((asdict(p) for p in document.passages if p.id == passage_id), None)
        return None

    def search(self, tenant, subject, query, top_k):
        if not query.strip() or len(query) > 400 or not 1 <= top_k <= 10:
            raise ValueError("invalid query or result limit")
        with self.lock:
            hits = self.index.search(tenant, query, top_k,
                                     lambda doc: self.document(tenant, subject, doc) is not None)
            excerpts = [self.citation(tenant, subject, doc, passage) for doc, passage in hits]
        evidence = [excerpt for excerpt in excerpts if excerpt]
        return {"status": "evidence" if evidence else "no_evidence", "evidence": evidence}

    def delete(self, tenant, subject, document_id):
        with self.lock:
            if not self.document(tenant, subject, document_id):
                return False
            self.store.delete(tenant, document_id)
            self.index.delete(tenant, document_id)
            return True


def new_document_id():
    return uuid.uuid4().hex

