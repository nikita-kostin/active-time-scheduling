# -*- coding: utf-8 -*-
from copy import deepcopy
from networkx import Graph
from typing import Dict, List, Optional, Set, Tuple
from queue import Queue


class EdmondsBlossomMatching(object):

    @staticmethod
    def _mark_path(
            v: int,
            b: int,
            child: int,
            blossom: Set[int],
            base: List[int],
            matching: Dict[int, int],
            p: Dict[int, int],
    ) -> None:
        while base[v] != b:
            blossom.add(base[v])
            blossom.add(base[matching[v]])
            p[v] = child
            child = matching[v]
            v = p[matching[v]]

    @staticmethod
    def _find_lowest_common_ancestor(
            a: int,
            b: int,
            base: List[int],
            matching: Dict[int, int],
            p: Dict[int, int],
    ) -> int:
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
    def _find_path(root: int, g: Graph, matching: Dict[int, int]) -> Tuple[Dict[int, int], Optional[int]]:
        used = set()
        p = {}
        base = [i for i in range(10000)]

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
    def process(g: Graph, initial_matching: Optional[Dict[int, int]] = None) -> Dict[int, int]:
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
