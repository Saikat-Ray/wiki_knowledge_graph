import unittest

import spacy

from wiki_kg.pipeline import KnowledgeGraphPipeline, Triple


def make_pipeline() -> KnowledgeGraphPipeline:
    pipeline = KnowledgeGraphPipeline.__new__(KnowledgeGraphPipeline)
    pipeline.nlp = spacy.load("en_core_web_sm")
    pipeline.page_title = None
    pipeline.page_url = None
    return pipeline


class PipelineTests(unittest.TestCase):
    def test_extracts_lemmatized_spo_triple(self):
        pipeline = make_pipeline()
        triples = pipeline.extract_triples(["Roger Federer won matches."])
        self.assertIn(Triple("roger federer", "win", "match", "Roger Federer won matches."), triples)

    def test_query_supports_wildcards(self):
        pipeline = make_pipeline()
        pipeline.build_graph([Triple("roger federer", "win", "match", "Roger Federer won matches.")])
        self.assertEqual(
            pipeline.query(subject="Roger Federer"),
            [Triple("roger federer", "win", "match", "Roger Federer won matches.")],
        )
