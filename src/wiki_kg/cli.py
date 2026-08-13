"""Command-line entry point for the Wikipedia knowledge-graph pipeline."""

from __future__ import annotations

import argparse
import os

from .neo4j_store import Neo4jGraphStore
from .pipeline import KnowledgeGraphPipeline, summarize_triples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and query a knowledge graph from a Wikipedia article.")
    parser.add_argument("title", help="Exact Wikipedia page title, e.g. 'Federer–Nadal rivalry'")
    parser.add_argument("--max-sentences", type=int, default=120, help="Limit processing for a smaller graph")
    parser.add_argument("--output", default="knowledge_graph.html", help="Interactive HTML graph output")
    parser.add_argument("--subject", help="Exact normalized subject filter")
    parser.add_argument("--predicate", help="Exact normalized predicate filter (a lemma, e.g. 'found')")
    parser.add_argument("--object", dest="object_", help="Exact normalized object filter")
    parser.add_argument("--neo4j-uri", help="Bolt URI to persist the graph, e.g. bolt://localhost:7687")
    parser.add_argument("--neo4j-user", default="neo4j", help="Neo4j username")
    parser.add_argument("--neo4j-password", default=os.getenv("NEO4J_PASSWORD"), help="Neo4j password")
    parser.add_argument("--neo4j-database", default="neo4j", help="Neo4j database name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        pipeline = KnowledgeGraphPipeline()
        article = pipeline.gather(args.title)
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
    sentences = pipeline.preprocess(article, args.max_sentences)
    triples = pipeline.extract_triples(sentences)
    graph = pipeline.build_graph(triples)
    output = pipeline.render(args.output)

    loaded_facts = None
    if args.neo4j_uri:
        if not args.neo4j_password:
            raise SystemExit("Error: supply --neo4j-password or set NEO4J_PASSWORD.")
        store: Neo4jGraphStore | None = None
        try:
            store = Neo4jGraphStore(args.neo4j_uri, args.neo4j_user, args.neo4j_password, args.neo4j_database)
            loaded_facts = store.load_graph(graph, pipeline.page_title, pipeline.page_url)
        except RuntimeError as exc:
            raise SystemExit(f"Error: {exc}") from exc
        finally:
            if store is not None:
                store.close()

    print(f"Page: {pipeline.page_title} ({pipeline.page_url})")
    print(f"Processed sentences: {len(sentences)} | facts: {len(triples)} | graph edges: {graph.number_of_edges()}")
    if args.subject or args.predicate or args.object_:
        matches = pipeline.query(args.subject, args.predicate, args.object_)
        print("Query results:\n" + summarize_triples(matches))
    else:
        print("Sample facts:\n" + summarize_triples(triples))
    if loaded_facts is not None:
        print(f"Neo4j: loaded {loaded_facts} distinct facts into {args.neo4j_uri}")
    print(f"Interactive graph: {output}")


if __name__ == "__main__":
    main()
