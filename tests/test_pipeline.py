import unittest

import spacy

from wiki_kg.pipeline import KnowledgeGraphPipeline, Triple


def make_pipeline() -> KnowledgeGraphPipeline:
    pipeline = KnowledgeGraphPipeline.__new__(KnowledgeGraphPipeline)
    pipeline.nlp = spacy.load("en_core_web_sm")
    return pipeline


class PipelineTests(unittest.TestCase):
    def test_extracts_lemmatized_spo_triple(self):
        pipeline = make_pipeline()
        triples = pipeline.extract_triples(["Ada Lovelace wrote notes."])
        self.assertIn(Triple("ada lovelace", "write", "note", "Ada Lovelace wrote notes."), triples)

    def test_query_supports_wildcards(self):
        pipeline = make_pipeline()
        pipeline.build_graph([Triple("ada", "write", "note", "Ada wrote notes.")])
        self.assertEqual(
            pipeline.query(subject="Ada"),
            [Triple("ada", "write", "note", "Ada wrote notes.")],
        )
