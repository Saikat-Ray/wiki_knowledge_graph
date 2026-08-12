import unittest

import app.Neo4j as neo4j_module


class FakeDriver:
    def __init__(self, session):
        self.session_obj = session

    def session(self):
        return self.session_obj


class FakeSession:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute_read(self, callback, entity_name):
        self.calls.append(("execute_read", entity_name))
        return [(entity_name, "KNOWS", "bar")]


class Neo4jHandlerTests(unittest.TestCase):
    def test_uses_execute_read_when_available(self):
        session = FakeSession()
        driver = FakeDriver(session)
        original_driver = neo4j_module.GraphDatabase.driver
        neo4j_module.GraphDatabase.driver = lambda *args, **kwargs: driver

        try:
            handler = neo4j_module.Neo4jHandler("bolt://localhost:7687", "neo4j", "password")
            result = handler.get_entities_and_relationships(["foo"])
        finally:
            neo4j_module.GraphDatabase.driver = original_driver

        self.assertEqual(result, [("foo", "KNOWS", "bar")])
        self.assertEqual(session.calls, [("execute_read", "foo")])
