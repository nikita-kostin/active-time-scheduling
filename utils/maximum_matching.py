# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from queue import Queue


class AbstractMaximumMatching(ABC):

    @staticmethod
    @abstractmethod
    def process(graph: List[Set[int]]) -> Dict[int, int]:
        pass


def is_matching_feasible(graph: List[Set[int]], m: Dict[int, int]) -> bool:
    used = set()

    for u, v in m.items():
        if u not in graph[v] or v not in graph[u]:
            return False

        if u != m[v] or v != m[u]:
            return False

        if u < v:
            if u in used or v in used:
                return False

            used.add(u)
            used.add(v)

    return True


class BruteForceMaximumMatching(AbstractMaximumMatching):

    @staticmethod
    def process(graph: List[Set[int]]) -> Dict[int, int]:
        edges = []

        for u in range(len(graph)):
            for v in graph[u]:
                if u < v:
                    edges.append((u, v))

        best_m = {}

        for bitmask in range(1 << len(edges)):
            m = {}

            for i, edge in enumerate(edges):
                if bitmask & (1 << i) != 0:
                    u, v = edge
                    m[u] = v
                    m[v] = u

            if len(m) > len(best_m) and is_matching_feasible(graph, m):
                best_m = m

        return best_m


class TreeNode(object):

    def __init__(self, value: Any, parent: Optional['TreeNode'] = None) -> None:
        self.value = value
        self.parent = parent

        self.root = self
        self.depth = 0
        if parent is not None:
            self.root = parent.root
            self.depth = parent.depth + 1

        self.children = []

    def add_child(self, value: Any) -> 'TreeNode':
        self.children.append(TreeNode(value, self))
        return self.children[-1]

    def __eq__(self, other: 'TreeNode') -> bool:
        return self.value == other.value

    def __str__(self) -> str:
        return "TreeNode(%s)" % self.value

    __repr__ = __str__


class BlossomMaximumMatching(AbstractMaximumMatching):

    @staticmethod
    def _alternate_path(path: List[int], m: Dict[int, int]) -> None:
        for i in range(len(path)):
            if path[i] in m:
                m.pop(m[path[i]])
                m.pop(path[i])
            if i % 2 == 1:
                m[path[i - 1]] = path[i]
                m[path[i]] = path[i - 1]

    @staticmethod
    def _get_path_to_root(u: TreeNode) -> List[TreeNode]:
        path = []

        while u is not None:
            path.append(u)
            u = u.parent

        return path

    @staticmethod
    def _get_blossom(v_path: List[TreeNode], w_path: List[TreeNode]) -> List[int]:
        while min(len(v_path), len(w_path)) > 1 and v_path[-1] == w_path[-1] and v_path[-2] == w_path[-2]:
            v_path.pop()
            w_path.pop()

        return [u.value for u in v_path] + [u.value for u in reversed(w_path[:-1])]

    @staticmethod
    def _get_contracted_ids(n: int, blossom_set: Set[int]) -> Tuple[Dict[int, int], Dict[int, int]]:
        current_contracted_id = 1

        id_to_contracted = {}
        contracted_to_id = {}

        for u in range(n):
            if u in blossom_set:
                id_to_contracted[u] = 0
            if u not in blossom_set:
                id_to_contracted[u] = current_contracted_id
                contracted_to_id[current_contracted_id] = u
                current_contracted_id += 1

        return id_to_contracted, contracted_to_id

    @staticmethod
    def _contract_graph(graph: List[Set[int]], id_to_contracted: Dict[int, int]) -> List[Set[int]]:
        contracted_graph = []
        for u in range(len(id_to_contracted)):
            contracted_graph.append(set())

        for u1 in range(len(graph)):
            for u in graph[u1]:
                if id_to_contracted[u1] != 0 or id_to_contracted[u] != 0:
                    contracted_graph[id_to_contracted[u1]].add(id_to_contracted[u])

        return contracted_graph

    @staticmethod
    def _get_path_between(u1: int, u2: int, path: Iterable[int]) -> List[int]:
        path_between = []

        state = 0
        for u in path:
            if u == u1:
                state = 1
            if state == 1 and u == u2:
                state = 2
            if state > 0:
                path_between.append(u)
            if state == 2:
                break

        return path_between

    @staticmethod
    def _lift_path(
            path: List[int],
            blossom: List[int],
            blossom_root: int,
            graph: List[Set[int]],
            contracted_to_id: Dict[int, int]
    ) -> List[int]:
        u1, u2 = blossom_root, blossom_root
        for i in range(len(path)):
            if path[i] == 0:
                if i != 0:
                    for u in blossom:
                        if contracted_to_id[path[i - 1]] in graph[u]:
                            u1 = u
                if i != len(path) - 1:
                    for u in blossom:
                        if contracted_to_id[path[i + 1]] in graph[u]:
                            u2 = u

        p1 = BlossomMaximumMatching._get_path_between(u1, u2, blossom + blossom)
        p2 = BlossomMaximumMatching._get_path_between(u1, u2, reversed(blossom + blossom))

        lifted_path = []

        for u in path:
            if u == 0:
                if (len(path) - 1 + len(p1)) % 2 == 0:
                    lifted_path.extend(p1)
                else:
                    lifted_path.extend(p2)
            else:
                lifted_path.append(contracted_to_id[u])

        return lifted_path

    @staticmethod
    def _find_augmenting_path(graph: List[Set[int]], m: Dict[int, int], exposed: Set[int]) -> Optional[List[int]]:
        q = Queue()

        f = {}
        for u in exposed:
            f[u] = TreeNode(u)
            q.put(u)

        while not q.empty():
            v = q.get()

            if f[v].depth % 2 != 0:
                continue

            for w in graph[v]:
                if m.get(w, None) == v:
                    continue

                if w not in f:
                    f[w] = f[v].add_child(w)

                    x = m[w]
                    f[x] = f[w].add_child(x)

                    q.put(m[w])
                    continue

                if f[w].depth % 2 != 0:
                    continue

                v_path = BlossomMaximumMatching._get_path_to_root(f[v])
                w_path = BlossomMaximumMatching._get_path_to_root(f[w])

                if f[v].root != f[w].root:
                    return [u.value for u in reversed(v_path)] + [u.value for u in w_path]

                blossom = BlossomMaximumMatching._get_blossom(v_path, w_path)
                blossom_set = set(blossom)
                blossom_root = v_path[-1].value

                id_to_contracted, contracted_to_id = BlossomMaximumMatching._get_contracted_ids(len(graph), blossom_set)
                contracted_graph = BlossomMaximumMatching._contract_graph(graph, id_to_contracted)
                contracted_m = {id_to_contracted[u]: id_to_contracted[v] for u, v in m.items()}
                contracted_exposed = {id_to_contracted[u] for u in exposed}

                path = BlossomMaximumMatching._find_augmenting_path(
                    contracted_graph, contracted_m, contracted_exposed
                )

                if path is None:
                    continue

                return BlossomMaximumMatching._lift_path(path, blossom, blossom_root, graph, contracted_to_id)

        return None

    @staticmethod
    def process(graph: List[Set[int]]) -> Dict[int, int]:
        m = {}

        while True:
            exposed = {u for u in range(len(graph)) if u not in m}

            path = BlossomMaximumMatching._find_augmenting_path(graph, m, exposed)

            if path is None:
                break

            BlossomMaximumMatching._alternate_path(path, m)

        return m


MaximumMatching = BlossomMaximumMatching
