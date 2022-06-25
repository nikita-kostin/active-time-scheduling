# -*- coding: utf-8 -*-
from networkx import Graph
from random import shuffle
from typing import Iterator, Optional, Type


class GraphGenerator(object):

    def __init__(self, n: int, m: int, graph_class: Type[Graph], max_capacity: Optional[int] = None) -> None:
        self.n = n
        self.m = m
        self.graph_class = graph_class
        self.max_capacity = max_capacity

    def __iter__(self) -> Iterator[Graph]:
        return self

    def __next__(self) -> Graph:
        graph = self.graph_class()

        edges = [(u, v) for u in range(self.n) for v in range(self.n) if u != v]
        shuffle(edges)

        for u, v in edges[:self.m]:
            graph.add_edge(u, v, capacity=1 if self.max_capacity is None else self.max_capacity)

        return graph
