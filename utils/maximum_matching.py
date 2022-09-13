# -*- coding: utf-8 -*-
from copy import deepcopy
from networkx import Graph
from typing import Any, Dict, Optional, Set, Tuple
from queue import Queue


class EdmondsBlossomMatching(object):
    """
    The implementation of the Edmonds' Blossom Algorithm for finding maximum matching on arbitrary graphs that is based
    on C++ implementation available at https://e-maxx.ru/algo/matching_edmonds. The running complexity of this
    particular implementation is O(V^3).
    """

    @staticmethod
    def _mark_path(
            v: Any,
            b: Any,
            child: Any,
            blossom: Set[Any],
            base: Dict[Any, Any],
            matching: Dict[Any, Any],
            p: Dict[Any, Any],
    ) -> None:
        while base[v] != b:
            blossom.add(base[v])
            blossom.add(base[matching[v]])
            p[v] = child
            child = matching[v]
            v = p[matching[v]]

    @staticmethod
    def _find_lowest_common_ancestor(
            a: Any,
            b: Any,
            base: Dict[Any, Any],
            matching: Dict[Any, Any],
            p: Dict[Any, Any],
    ) -> Any:
        used = set()

        while True:
            a = base[a]
            used.add(a)
            if matching.get(a, None) is None:
                break
            a = p[matching[a]]

        while True:
            b = base[b]
            if b in used:
                return b
            b = p[matching[b]]

    @staticmethod
    def _find_path(root: Any, g: Graph, matching: Dict[Any, Any]) -> Tuple[Dict[Any, Any], Optional[Any]]:
        used = set()
        p = {}
        base = {u: u for u in g.nodes}

        used.add(root)
        q = Queue()
        q.put(root)

        while not q.empty():
            v = q.get()

            for to in g[v]:
                if base[v] == base[to] or matching.get(v, None) == to:
                    continue
                if to == root or matching.get(to, None) is not None and p.get(matching[to], None) is not None:
                    curbase = EdmondsBlossomMatching._find_lowest_common_ancestor(v, to, base, matching, p)

                    blossom = set()
                    EdmondsBlossomMatching._mark_path(v, curbase, to, blossom, base, matching, p)
                    EdmondsBlossomMatching._mark_path(to, curbase, v, blossom, base, matching, p)

                    for u in g.nodes:
                        if base[u] in blossom:
                            base[u] = curbase
                            if u not in used:
                                used.add(u)
                                q.put(u)
                elif p.get(to, None) is None:
                    p[to] = v

                    if matching.get(to, None) is None:
                        return p, to

                    to = matching[to]
                    used.add(to)
                    q.put(to)

        return p, None

    @staticmethod
    def process(g: Graph, initial_matching: Optional[Dict[Any, Any]] = None) -> Dict[Any, Any]:
        """
        Computes the maximum matching.
        :param g: The input graph.
        :param initial_matching: Initial matching to extend, considered empty if none is provided.
        :return: Computed matching.
        """
        matching = {} if initial_matching is None else deepcopy(initial_matching)

        for u in g.nodes:
            if matching.get(u, None) is None:
                p, v = EdmondsBlossomMatching._find_path(u, g, matching)

                while v is not None:
                    pv = p[v]
                    ppv = matching.get(pv, None)
                    matching[v] = pv
                    matching[pv] = v
                    v = ppv

        return matching


class UpperDegreeConstrainedSubgraph(object):
    """
    An algorithm for solving the upper degree constrained subgraph problem based on "Another look at the degree
    constrained subgraph problem" (Shiloach, 1981) that reduces the problem to ordinary matchings on general graphs.
    """

    @staticmethod
    def construct_h(g: Graph, constraints: Dict[int, int]) -> Graph:
        """
        Construct helper graph.
        :param g: Original graph.
        :param constraints: Degree constrains.
        :return: Resulting helper graph.
        """
        h = Graph()

        for u in g.nodes:
            for i in range(constraints[u]):
                h.add_node("v_%s^%d" % (u, i))

        for i, e in enumerate(g.edges):
            u, v = e

            h.add_node("u_{%s, %s}" % (u, v))
            h.add_node("w_{%s, %s}" % (u, v))
            h.add_edge("u_{%s, %s}" % (u, v), "w_{%s, %s}" % (u, v))

            for j in range(constraints[u]):
                h.add_edge("u_{%s, %s}" % (u, v), "v_%s^%d" % (u, j))
            for j in range(constraints[v]):
                h.add_edge("w_{%s, %s}" % (u, v), "v_%s^%d" % (v, j))

        return h

    @staticmethod
    def construct_dcs(g: Graph, matching: Dict[Any, Any]) -> Dict[Any, Set[Any]]:
        """
        Construct the DCS solution from matching.
        :param g: Corresponding graph.
        :param matching: Matching solution.
        :return: DCS solution.
        """
        degree_constrained_subgraph = {}
        for u in g.nodes:
            degree_constrained_subgraph[u] = set()

        for i, e in enumerate(g.edges):
            u, v = e

            if (
                    matching.get("u_{%s, %s}" % (u, v), '').startswith("v_") and
                    matching.get("w_{%s, %s}" % (u, v), '').startswith("v_")
            ):
                degree_constrained_subgraph[u].add(v)
                degree_constrained_subgraph[v].add(u)

        return degree_constrained_subgraph

    @staticmethod
    def process(g: Graph, constraints: Dict[int, int]) -> Dict[Any, Set[Any]]:
        """
        Process the input using Edmonds' Blossom Algorithm.
        :param g: Graph to process.
        :param constraints: Degree constraints.
        :return: Resulting solution.
        """
        h = Graph()

        for u in g.nodes:
            for i in range(constraints[u]):
                h.add_node("v_%s^%d" % (u, i))

        for i, e in enumerate(g.edges):
            u, v = e

            h.add_node("u_%d" % i)
            h.add_node("w_%d" % i)
            h.add_edge("u_%d" % i, "w_%d" % i)

            for j in range(constraints[u]):
                h.add_edge("u_%d" % i, "v_%s^%d" % (u, j))
            for j in range(constraints[v]):
                h.add_edge("w_%d" % i, "v_%s^%d" % (v, j))

        matching = EdmondsBlossomMatching().process(h)

        degree_constrained_subgraph = {}
        for u in g.nodes:
            degree_constrained_subgraph[u] = set()

        for i, e in enumerate(g.edges):
            u, v = e

            if matching.get("u_%d" % i, '').startswith("v_") and matching.get("w_%d" % i, '').startswith("v_"):
                degree_constrained_subgraph[u].add(v)
                degree_constrained_subgraph[v].add(u)

        return degree_constrained_subgraph
