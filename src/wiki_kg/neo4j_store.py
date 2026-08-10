"""Persistence for the extracted graph in a Neo4j graph database."""

from __future__ import annotations

from typing import Any

import networkx as nx


class Neo4jGraphStore:
    """Load a NetworkX knowledge graph into Neo4j with idempotent source facts."""

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j") -> None:
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            raise RuntimeError("Neo4j support is not installed. Run: pip install -r requirements.txt") from exc
        self.database = database
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self.driver.close()

    def load_graph(self, graph: nx.MultiDiGraph, source_title: str | None, source_url: str | None) -> int:
        """Upsert all graph edges and return the number of distinct facts written.

        An edge is identified by its source, target, predicate, and Wikipedia URL,
        so rerunning an import replaces its stored evidence instead of duplicating it.
        """
        facts = [
            {
                "subject": subject,
                "object": object_,
                "predicate": data["predicate"],
                "count": data["count"],
                "sentences": data["sentences"],
            }
            for subject, object_, _, data in graph.edges(keys=True, data=True)
        ]
        if not facts:
            return 0
        with self.driver.session(database=self.database) as session:
            session.execute_write(self._ensure_schema)
            session.execute_write(self._upsert_facts, facts, source_title, source_url)
        return len(facts)

    @staticmethod
    def _ensure_schema(tx: Any) -> None:
        tx.run(
            "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS "
            "FOR (entity:Entity) REQUIRE entity.name IS UNIQUE"
        ).consume()

    @staticmethod
    def _upsert_facts(
        tx: Any, facts: list[dict[str, Any]], source_title: str | None, source_url: str | None
    ) -> None:
        tx.run(
            """
            UNWIND $facts AS fact
            MERGE (subject:Entity {name: fact.subject})
            MERGE (object:Entity {name: fact.object})
            MERGE (subject)-[relation:RELATION {
                predicate: fact.predicate,
                source_url: $source_url
            }]->(object)
            SET relation.count = fact.count,
                relation.sentences = fact.sentences,
                relation.source_title = $source_title
            """,
            facts=facts,
            source_title=source_title,
            source_url=source_url,
        ).consume()
