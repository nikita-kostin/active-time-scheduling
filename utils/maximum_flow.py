# -*- coding: utf-8 -*-
from networkx import DiGraph
from networkx.algorithms.flow import build_residual_network
from typing import Any, Dict


class FordFulkerson(object):
    """
    Ford-Fulkerson algorithm for solving the maximum flow problem. The running complexity of this algorithm is O(Ef)
    where f is the maximum flow in the network. The class is designed in such a way that it can be used in the networkx
    package.
    """

    def __init__(self, graph: DiGraph) -> None:
        """
        Initialize the class with parameters.
        :param graph: Flow network.
        """
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

    def _build_residual_network(self) -> DiGraph:
        r = build_residual_network(self.graph, 'capacity')
        r.graph['flow_value'] = 0

        for u, v in r.edges:
            r[u][v]['flow'] = 0

        return r

    def process(self, s: Any, t: Any) -> DiGraph:
        """
        Find the maximum flow from source to sink.
        :param s: Source of the network.
        :param t: Sink of the network.
        :return: Resulting residual network.
        """
        r = self._build_residual_network()

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
    """
    Function that constructs the FordFulkerson object and computes the maximum flow. Can be used as the flow_func
    argument of the maximum_flow function in the networkx package.
    :param graph: Network to process.
    :param s: Source of the network.
    :param t: Sink of the network.
    :param args: Args to pass to the function.
    :param kwargs: Kwargs to pass to the function.
    :return: Resulting residual network.
    """
    ff = FordFulkerson(graph)
    return ff.process(s, t)
