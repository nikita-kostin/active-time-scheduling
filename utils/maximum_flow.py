# -*- coding: utf-8 -*-
from typing import Dict, List, Set, Tuple


class FordFulkerson(object):

    def __init__(self, graph: List[Set[int]], c: Dict[Tuple[int, int], int], s: int, t: int) -> None:
        self.graph = graph
        self.c = c
        self.s = s
        self.t = t

    def _find_augmenting_path(self, u: int, pc: int, used: List[bool], f: Dict[Tuple[int, int], int]) -> int:
        if u == self.t:
            return pc

        used[u] = True

        for v in self.graph[u]:
            self.c.setdefault((u, v), 0)
            f.setdefault((u, v), 0)
            f.setdefault((v, u), 0)

            ec = self.c[(u, v)] - f[(u, v)]

            if used[v] or ec == 0:
                continue

            a = self._find_augmenting_path(v, min(pc, ec), used, f)

            f[(u, v)] += a
            f[(v, u)] -= a

            if a > 0:
                return a

        return 0

    def process(self) -> int:
        if self.s == self.t:
            return 0

        ans = 0
        f = dict()

        while True:
            used = [False] * len(self.graph)
            a = self._find_augmenting_path(self.s, int(1e9), used, f)

            if a == 0:
                break

            ans += a

        return ans
