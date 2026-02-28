from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Node(BaseModel):
    id: str
    label: str
    type: str  # 'drug', 'condition', 'trial', 'paper'


class Edge(BaseModel):
    source: str
    target: str
    relationship: str


class MedicalGraph(BaseModel):
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)

    def add_node(self, id: str, label: str, node_type: str):
        if not any(n.id == id for n in self.nodes):
            self.nodes.append(Node(id=id, label=label, type=node_type))

    def add_edge(self, source: str, target: str, relationship: str):
        if not any(e.source == source and e.target == target for e in self.edges):
            self.edges.append(
                Edge(source=source, target=target, relationship=relationship)
            )
