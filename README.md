# Wikipedia spaCy Knowledge Graph

A small end-to-end NLP project that turns an English Wikipedia article into a queryable, interactive knowledge graph.

It uses:

- `wikipedia` to gather article text from Wikipedia
- `spaCy` for sentence splitting, preprocessing, lemmatization (root-form conversion), and dependency-based subject–predicate–object (SPO) extraction
- `NetworkX` to create and query a directed multigraph
- `PyVis` to render the graph as an interactive HTML file

## Setup

Requires Python 3.10+.

```bash
cd /Users/admin/Documents/Codex/2026-08-07/build/outputs/wiki_knowledge_graph
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
export PYTHONPATH="$PWD/src"
```

If you created the environment before this update, repair it with:

```bash
pip install --upgrade --force-reinstall -r requirements.txt
```

## Docker Compose local development

Docker Compose builds an isolated Python 3.12 environment with the spaCy English
model already installed. Your project folder is mounted into the container, so
source edits are immediately available on the next run and generated HTML files
remain in this folder.

```bash
cd /Users/admin/Documents/Codex/2026-08-07/build/outputs/wiki_knowledge_graph
docker compose up --build
```

The default run starts Neo4j, creates `knowledge_graph.html` using the Ada
Lovelace article, and imports its facts into Neo4j. The database is ready in
Neo4j Browser at `http://localhost:7474`. Set `NEO4J_PASSWORD` before the first
start to use your own local password.

```bash
export NEO4J_PASSWORD='choose-a-local-password'
docker compose up --build
```

Use a different page or query by passing CLI arguments to a one-off container:

```bash
docker compose run --rm wiki-kg "Marie Curie" --max-sentences 80 --output marie_curie_graph.html
docker compose run --rm wiki-kg "Ada Lovelace" --subject "ada lovelace"
```

Run the test suite inside the same development image:

```bash
docker compose run --rm --entrypoint python wiki-kg -m unittest discover -s tests -v
```

## Load the knowledge graph into Neo4j

The Compose stack includes Neo4j, exposed at `http://localhost:7474` (Neo4j
Browser) and `bolt://localhost:7687` (the application connection). Start the
database, then load a Wikipedia graph through the `wiki-kg` service:

```bash
export NEO4J_PASSWORD='choose-a-local-password'
docker compose up -d neo4j
# Rebuild after this project's dependency changes (the Neo4j driver is in requirements.txt).
docker compose build wiki-kg
docker compose run --rm -e NEO4J_PASSWORD wiki-kg "Ada Lovelace" \
  --max-sentences 100 \
  --output ada_lovelace_graph.html \
  --neo4j-uri bolt://neo4j:7687 \
  --neo4j-password "$NEO4J_PASSWORD"
```

Sign in to Neo4j Browser at `http://localhost:7474` with username `neo4j` and
the password above. The importer creates `(:Entity)` nodes and `[:RELATION]`
edges. Each relationship stores `predicate`, `count`, `sentences`,
`source_title`, and `source_url`. Reimporting the same article updates its
evidence rather than duplicating relationships.

Example Cypher queries:

```cypher
MATCH (subject:Entity)-[relation:RELATION]->(object:Entity)
RETURN subject, relation, object
LIMIT 50;

MATCH (subject:Entity {name: 'ada lovelace'})-[relation:RELATION]->(object:Entity)
RETURN subject.name, relation.predicate, object.name, relation.sentences;
```

## Build a graph

```bash
python -m wiki_kg.cli "Ada Lovelace" --max-sentences 100 --output ada_lovelace_graph.html
```

Open `ada_lovelace_graph.html` in a browser. Hover over an edge to see source-sentence evidence.

## Query facts

All query terms use the normalized forms stored in the graph: lowercase lemmas with stop words removed. For example, `wrote` becomes `write` and `notes` becomes `note`.

```bash
# Find every fact whose subject is normalized to "ada lovelace"
python -m wiki_kg.cli "Ada Lovelace" --subject "ada lovelace"

# Find a particular relation
python -m wiki_kg.cli "Ada Lovelace" --predicate write --object note
```

## Pipeline

```text
Wikipedia page → English sentence filtering → spaCy parse + lemmas
               → dependency SPO triples → NetworkX MultiDiGraph → PyVis HTML
```

The extractor captures grammatical subjects and direct/attribute objects, plus prepositional objects attached to a verb. It is deliberately transparent and rule-based; it will not resolve all pronouns, implicit subjects, or complex coordinated clauses.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```
