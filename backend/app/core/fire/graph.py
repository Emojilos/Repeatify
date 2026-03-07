"""Knowledge graph for FIRe credit/penalty propagation.

Loads topic_dependencies from Supabase and exposes prerequisite/dependent lookups.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from supabase import Client


@dataclass
class Edge:
    """Directed edge representing a dependency between topics."""

    topic_id: str
    weight: float  # 0.0–1.0; higher = stronger dependency


@dataclass
class KnowledgeGraph:
    """In-memory bidirectional graph of topic dependencies.

    Graph direction: prerequisite → dependent
    (A is prerequisite of B means A must be learned before B)

    For credit propagation we traverse *upstream* (to prerequisites).
    For penalty propagation we traverse *downstream* (to dependents).
    """

    # prerequisites[topic_id] = list of prerequisite edges (incoming)
    prerequisites: dict[str, list[Edge]] = field(default_factory=dict)
    # dependents[topic_id] = list of dependent edges (outgoing)
    dependents: dict[str, list[Edge]] = field(default_factory=dict)

    @classmethod
    def from_supabase(cls, sb: Client) -> KnowledgeGraph:
        """Build the graph from the topic_dependencies table."""
        resp = (
            sb.table("topic_dependencies")
            .select("prerequisite_topic_id, dependent_topic_id, weight")
            .execute()
        )
        graph = cls()
        for row in resp.data or []:
            prereq = row["prerequisite_topic_id"]
            dep = row["dependent_topic_id"]
            weight = float(row.get("weight") or 1.0)

            graph.prerequisites.setdefault(dep, []).append(Edge(topic_id=prereq, weight=weight))
            graph.dependents.setdefault(prereq, []).append(Edge(topic_id=dep, weight=weight))

        return graph

    @classmethod
    def from_edges(cls, edges: list[tuple[str, str, float]]) -> KnowledgeGraph:
        """Build a graph from a list of (prerequisite_id, dependent_id, weight) tuples.

        Useful for unit tests without a live Supabase client.
        """
        graph = cls()
        for prereq, dep, weight in edges:
            graph.prerequisites.setdefault(dep, []).append(Edge(topic_id=prereq, weight=weight))
            graph.dependents.setdefault(prereq, []).append(Edge(topic_id=dep, weight=weight))
        return graph

    def get_prerequisites(self, topic_id: str) -> list[Edge]:
        """Return all direct prerequisite topics for a given topic."""
        return self.prerequisites.get(topic_id, [])

    def get_dependents(self, topic_id: str) -> list[Edge]:
        """Return all topics that directly depend on a given topic."""
        return self.dependents.get(topic_id, [])
