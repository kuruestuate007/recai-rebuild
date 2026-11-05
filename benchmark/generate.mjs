import { writeFileSync } from 'node:fs';

const skillPairs = [
  ['Kubernetes', 'K8s'], ['PostgreSQL', 'Postgres'],
  ['Amazon S3', 'S3'], ['SAP Integration Suite', 'SAP CPI'],
  ['continuous integration', 'CI'], ['infrastructure as code', 'IaC'],
  ['single sign-on', 'SSO'], ['disaster recovery', 'DR'],
  ['Apache Kafka', 'Kafka'], ['access control', 'RBAC'],
  ['Optical Character Recognition', 'OCR'], ['OpenID Connect', 'OIDC'],
];

const documents = [];
const queries = [];

function addDocument(tenant, id, text) {
  const passage = { id: id + '-p2', page: 2, text };
  documents.push({
    id, tenant, pages: [
      { id: id + '-p1', page: 1, text: 'Synthetic profile. Responsibilities and evidence follow.' },
      passage,
    ],
  });
  return passage;
}

for (const [index, [skill, alias]] of skillPairs.entries()) {
  const key = String(index + 1).padStart(2, '0');
  const split = index < 6 ? 'development' : 'holdout';
  const exact = addDocument('tenant-a', 'exact-' + key, 'Built and operated a production workflow using ' + skill + '.');
  const alternate = addDocument('tenant-a', 'alias-' + key, 'Maintained a production workflow using ' + alias + '.');
  addDocument('tenant-a', 'negated-' + key, 'Observed a demo of ' + skill + ' but did not use it on a project.');
  addDocument('tenant-a', 'unrelated-' + key, 'Documented support handovers and tracked the issue backlog.');
  addDocument('tenant-b', 'restricted-' + key, 'Implemented ' + skill + ' in production and trained the support team.');

  function addQuery(kind, allowedDocuments, question, expected) {
    queries.push({
      id: kind + '-' + key, split, kind, tenant: 'tenant-a', allowedDocuments,
      question, expected: expected.map(({ id, page, text }) => ({ id, page, text })),
    });
  }

  addQuery('exact', ['exact-' + key], 'Where does this resume show hands-on ' + skill + ' experience?', [exact]);
  addQuery('alias', ['alias-' + key], 'Find evidence of practical experience with ' + skill + '.', [alternate]);
  addQuery('distractors', ['exact-' + key, 'alias-' + key, 'negated-' + key, 'unrelated-' + key],
    'Which passages show hands-on experience with ' + skill + '?', [exact, alternate]);
  addQuery('no-evidence', ['negated-' + key, 'unrelated-' + key],
    'Did this candidate use ' + skill + ' on a project? Cite evidence if present.', []);
  addQuery('cross-tenant', ['restricted-' + key], 'Find the production evidence for ' + skill + '.', []);
}

writeFileSync(new URL('corpus.json', import.meta.url), JSON.stringify(documents, null, 2) + '\n');
writeFileSync(new URL('queries.json', import.meta.url), JSON.stringify(queries, null, 2) + '\n');
