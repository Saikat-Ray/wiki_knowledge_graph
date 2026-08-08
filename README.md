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
