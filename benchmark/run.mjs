import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { performance } from 'node:perf_hooks';

function read(name) {
  return JSON.parse(readFileSync(new URL(name, import.meta.url), 'utf8'));
}

const documents = read('corpus.json');
const queries = read('queries.json');

function tokens(text) {
  return new Set(text.toLowerCase().match(/[a-z0-9]+/g) ?? []);
}

function lexicalSearch(query) {
  const allowed = new Set(query.allowedDocuments);
  const searchTerms = tokens(query.question);
  return documents
    .filter(document => document.tenant === query.tenant && allowed.has(document.id))
    .flatMap(document => document.pages.map(passage => ({
      ...passage,
      documentId: document.id,
      tenant: document.tenant,
      score: [...tokens(passage.text)].filter(term => searchTerms.has(term)).length,
    })))
    .filter(passage => passage.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);
}

assert.equal(documents.length, 60);
assert.equal(queries.length, 60);
const passages = new Map(documents.flatMap(document =>
  document.pages.map(passage => [passage.id, { document, passage }])));
assert.equal(passages.size, 120);

for (const query of queries) {
  for (const expected of query.expected) {
    const source = passages.get(expected.id);
    assert.ok(source);
    assert.equal(source.document.tenant, query.tenant);
    assert.ok(query.allowedDocuments.includes(source.document.id));
    assert.deepEqual(source.passage, expected);
  }
}

for (const split of ['development', 'holdout']) {
  let returned = 0;
  let correct = 0;
  let expected = 0;
  let emptyQueries = 0;
  let falseEvidence = 0;
  let wrongScope = 0;
  const times = [];

  for (const query of queries.filter(item => item.split === split)) {
    const start = performance.now();
    const results = lexicalSearch(query);
    times.push(performance.now() - start);
    returned += results.length;
    expected += query.expected.length;
    if (query.expected.length === 0) {
      emptyQueries++;
      if (results.length > 0) falseEvidence++;
    }

    for (const result of results) {
      if (result.tenant !== query.tenant || !query.allowedDocuments.includes(result.documentId)) wrongScope++;
      if (query.expected.some(label =>
        label.id === result.id && label.page === result.page && label.text === result.text)) correct++;
    }
  }

  assert.equal(wrongScope, 0, 'retrieval crossed a tenant or document boundary');
  times.sort((a, b) => a - b);
  console.log(JSON.stringify({
    split, citationPrecision: correct / returned, evidenceRecall: correct / expected,
    falseEvidence, emptyQueries, wrongScope,
    localP95Ms: Number(times[Math.ceil(times.length * 0.95) - 1].toFixed(3)),
  }));
}
