# -*- coding: utf-8 -*-
from copy import deepcopy
from networkx import DiGraph
from typing import Any, Dict


class FordFulkerson(object):

    def __init__(self, graph: DiGraph) -> None:
        self.graph = graph

    @staticmethod
    def _find_augmenting_path(r: DiGraph, u: Any, t: Any, pc: int, used: Dict[Any, bool]) -> int:
        if u == t:
            return pc

        used[u] = True

        for v in r[u]:
            ec = r[u][v]['capacity'] - r[u][v]['flow']

            if used.get(v, False) is True or ec == 0:
                continue

            a = FordFulkerson._find_augmenting_path(r, v, t, min(pc, ec), used)

            r[u][v]['flow'] += a
            r[v][u]['flow'] -= a

            if a > 0:
                return a

        return 0

    def _create_residual_network(self) -> DiGraph:
        r = deepcopy(self.graph)
        r.graph['flow_value'] = 0

        for u, v in r.edges:
            if u not in self.graph[v]:
                r.add_edge(v, u, capacity=0)

            r[u][v]['flow'] = 0
            r[v][u]['flow'] = 0

        return r

    def process(self, s: Any, t: Any) -> DiGraph:
        r = self._create_residual_network()

        if s == t:
            return r

        while True:
            used = {}
            a = self._find_augmenting_path(r, s, t, int(1e9), used)

            r.graph['flow_value'] += a

            if a == 0:
                break

        return r


def ford_fulkerson(graph: DiGraph, s: Any, t: Any, *args, **kwargs) -> DiGraph:
    ff = FordFulkerson(graph)
    return ff.process(s, t)
