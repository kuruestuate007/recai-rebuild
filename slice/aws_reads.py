"""Unwired read-side AWS adapters. Clients are injected and never created here."""
import json

from core import Document, Passage


class DynamoDocumentStore:
    def __init__(self, table, objects, bucket):
        self.table, self.objects, self.bucket = table, objects, bucket

    def get(self, tenant, document_id):
        item = self.table.get_item(Key={"tenant": tenant, "document_id": document_id},
                                   ConsistentRead=True).get("Item")
        if not item or item["state"] != "ready":
            return None
        blob = self.objects.get_object(Bucket=self.bucket, Key=item["manifest_key"])
        with blob["Body"] as stream:
            manifest = json.load(stream)
        return Document(item["digest"], b"", tuple(Passage(**p) for p in manifest["passages"]), item["owner"])


class S3VectorIndex:
    def __init__(self, client, bucket, index, embed):
        self.client, self.bucket, self.index, self.embed = client, bucket, index, embed

    def search(self, tenant, query, limit, allowed):
        result = self.client.query_vectors(
            vectorBucketName=self.bucket, indexName=self.index,
            queryVector={"float32": self.embed(query)}, topK=limit,
            filter={"tenant": {"$eq": tenant}}, returnMetadata=True,
        )
        return [(hit["metadata"]["document_id"], hit["key"]) for hit in result["vectors"]
                if hit.get("metadata", {}).get("tenant") == tenant and allowed(hit["metadata"]["document_id"])]

