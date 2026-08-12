from neo4j import GraphDatabase


class Neo4jHandler:
    def __init__(self, connection_uri, username, password):
        self.driver = GraphDatabase.driver(connection_uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def get_entities_and_relationships(self, entities):
        results = []
        with self.driver.session() as session:
            for entity in entities:
                if hasattr(session, "execute_read"):
                    result = session.execute_read(self._retrieve_relationships, entity)
                else:
                    result = session.read_transaction(self._retrieve_relationships, entity)
                results.extend(result)
        return results

    @staticmethod
    def _retrieve_relationships(tx, entity_name):
        query = """
        MATCH (e1:Entity {name: $entity_name})-[r:RELATION]->(e2:Entity)
        RETURN e1.name AS entity1, r.predicate AS relationship, e2.name AS entity2
        """
        result = tx.run(query, entity_name=entity_name)
        return [(record["entity1"], record["relationship"], record["entity2"]) for record in result]
