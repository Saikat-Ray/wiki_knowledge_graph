"""Command-line entry point for the Wikipedia knowledge-graph pipeline."""

from __future__ import annotations

import argparse

from .pipeline import KnowledgeGraphPipeline, summarize_triples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and query a knowledge graph from a Wikipedia article.")
    parser.add_argument("title", help="Exact Wikipedia page title, e.g. 'Ada Lovelace'")
    parser.add_argument("--max-sentences", type=int, default=120, help="Limit processing for a smaller graph")
    parser.add_argument("--output", default="knowledge_graph.html", help="Interactive HTML graph output")
    parser.add_argument("--subject", help="Exact normalized subject filter")
    parser.add_argument("--predicate", help="Exact normalized predicate filter (a lemma, e.g. 'found')")
    parser.add_argument("--object", dest="object_", help="Exact normalized object filter")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pipeline = KnowledgeGraphPipeline()
    article = pipeline.gather(args.title)
    sentences = pipeline.preprocess(article, args.max_sentences)
    triples = pipeline.extract_triples(sentences)
    graph = pipeline.build_graph(triples)
    output = pipeline.render(args.output)

    print(f"Page: {pipeline.page_title} ({pipeline.page_url})")
    print(f"Processed sentences: {len(sentences)} | facts: {len(triples)} | graph edges: {graph.number_of_edges()}")
    if args.subject or args.predicate or args.object_:
        matches = pipeline.query(args.subject, args.predicate, args.object_)
        print("Query results:\n" + summarize_triples(matches))
    else:
        print("Sample facts:\n" + summarize_triples(triples))
    print(f"Interactive graph: {output}")


if __name__ == "__main__":
    main()
