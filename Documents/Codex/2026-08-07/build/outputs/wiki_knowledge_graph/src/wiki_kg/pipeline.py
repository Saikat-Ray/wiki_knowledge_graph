"""Wikipedia, spaCy, NetworkX, and PyVis integration for a compact KG."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import networkx as nx
import spacy
import wikipedia
from spacy.language import Language
from spacy.tokens import Doc, Token


SUBJECT_DEPS = {"nsubj", "nsubjpass", "csubj", "csubjpass"}
OBJECT_DEPS = {"dobj", "obj", "attr", "oprd", "dative"}
PREPOSITION_DEPS = {"prep", "agent"}


@dataclass(frozen=True)
class Triple:
    """One normalized fact with its source sentence."""

    subject: str
    predicate: str
    object: str
    sentence: str


class KnowledgeGraphPipeline:
    """Fetch a page, extract dependency-based SPO triples, and expose a graph."""

    def __init__(self, model: str = "en_core_web_sm") -> None:
        # The package also supports other Wikipedia editions; fix this pipeline to English.
        wikipedia.set_lang("en")
        try:
            self.nlp: Language = spacy.load(model)
        except OSError as exc:
            raise RuntimeError(
                f"spaCy model '{model}' is not installed. Run: "
                f"python -m spacy download {model}"
            ) from exc
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self.page_url: str | None = None
        self.page_title: str | None = None

    def gather(self, title: str) -> str:
        """Get plain English article text using the ``wikipedia`` library."""
        try:
            page = wikipedia.page(title, auto_suggest=False, redirect=True)
        except wikipedia.DisambiguationError as exc:
            choices = ", ".join(exc.options[:8])
            raise ValueError(f"'{title}' is ambiguous. Try one of: {choices}") from exc
        except wikipedia.PageError as exc:
            raise ValueError(f"Wikipedia page not found: {title}") from exc

        self.page_title = page.title
        self.page_url = page.url
        return page.content

    def preprocess(self, text: str, max_sentences: int | None = None) -> list[str]:
        """Keep substantive English sentences, stripping citation-style whitespace."""
        doc = self.nlp(text.replace("\n", " "))
        sentences = [
            sent.text.strip()
            for sent in doc.sents
            if len([t for t in sent if t.is_alpha]) >= 3
            and not sent.text.lstrip().startswith(("==", "["))
        ]
        return sentences[:max_sentences] if max_sentences else sentences

    def extract_triples(self, sentences: Iterable[str]) -> list[Triple]:
        """Lemmatize words and extract dependency-based subject–predicate–object facts."""
        triples: list[Triple] = []
        for doc in self.nlp.pipe(sentences):
            triples.extend(self._triples_from_doc(doc))
        return triples

    def build_graph(self, triples: Iterable[Triple]) -> nx.MultiDiGraph:
        """Create a directed multigraph; repeated facts accumulate evidence counts."""
        self.graph = nx.MultiDiGraph(title=self.page_title, source_url=self.page_url)
        for triple in triples:
            key = triple.predicate
            if self.graph.has_edge(triple.subject, triple.object, key=key):
                edge = self.graph[triple.subject][triple.object][key]
                edge["count"] += 1
                edge["sentences"].append(triple.sentence)
            else:
                self.graph.add_edge(
                    triple.subject,
                    triple.object,
                    key=key,
                    predicate=triple.predicate,
                    count=1,
                    sentences=[triple.sentence],
                )
        return self.graph

    def query(
        self, subject: str | None = None, predicate: str | None = None, object_: str | None = None
    ) -> list[Triple]:
        """Match graph facts; omitted fields are wildcards (case-insensitive)."""
        wanted = tuple(value.lower() if value else None for value in (subject, predicate, object_))
        found: list[Triple] = []
        for source, target, _, data in self.graph.edges(keys=True, data=True):
            values = (source, data["predicate"], target)
            if all(expected is None or expected == actual.lower() for expected, actual in zip(wanted, values)):
                for sentence in data["sentences"]:
                    found.append(Triple(source, data["predicate"], target, sentence))
        return found

    def render(self, output: str | Path) -> Path:
        """Write an interactive HTML visualization with PyVis."""
        from pyvis.network import Network

        destination = Path(output).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        network = Network(height="780px", width="100%", directed=True, bgcolor="#ffffff")
        network.barnes_hut(gravity=-35000, central_gravity=0.25, spring_length=170)
        for node in self.graph.nodes:
            network.add_node(node, label=node, title=node, shape="dot", size=16)
        for source, target, _, data in self.graph.edges(keys=True, data=True):
            evidence = "<br>".join(data["sentences"][:3])
            network.add_edge(
                source,
                target,
                label=data["predicate"],
                title=f"Occurrences: {data['count']}<br>{evidence}",
                arrows="to",
            )
        network.write_html(str(destination), open_browser=False, notebook=False)
        return destination

    def _triples_from_doc(self, doc: Doc) -> list[Triple]:
        result: list[Triple] = []
        for verb in doc:
            if verb.pos_ not in {"VERB", "AUX"}:
                continue
            subjects = [child for child in verb.children if child.dep_ in SUBJECT_DEPS]
            objects = [child for child in verb.children if child.dep_ in OBJECT_DEPS]
            for prep in (child for child in verb.children if child.dep_ in PREPOSITION_DEPS):
                objects.extend(child for child in prep.children if child.dep_ == "pobj")
            predicate = self._root_form(verb)
            if not predicate:
                continue
            for subject in subjects:
                for object_token in objects:
                    source, target = self._entity(subject), self._entity(object_token)
                    if source and target and source != target:
                        result.append(Triple(source, predicate, target, doc.text.strip()))
        return list(dict.fromkeys(result))

    @staticmethod
    def _root_form(token: Token) -> str:
        """Return a lower-cased spaCy lemma, the word's root form."""
        lemma = token.lemma_.lower().strip()
        return "" if lemma in {"-pron-", ""} else lemma

    def _entity(self, token: Token) -> str:
        """Use the containing noun phrase when possible, then lemmatize its words."""
        phrase = next((chunk for chunk in token.doc.noun_chunks if token.i >= chunk.start and token.i < chunk.end), None)
        tokens = phrase if phrase is not None else token.subtree
        words = [
            self._root_form(part)
            for part in tokens
            if not part.is_stop and not part.is_punct and (part.is_alpha or part.like_num)
        ]
        return " ".join(word for word in words if word)


def summarize_triples(triples: Iterable[Triple], limit: int = 10) -> str:
    """Create a concise text preview for command-line use."""
    counts = Counter((t.subject, t.predicate, t.object) for t in triples)
    lines = [f"{s} --{p}--> {o} ({count} evidence)" for (s, p, o), count in counts.most_common(limit)]
    return "\n".join(lines) if lines else "No triples extracted."
