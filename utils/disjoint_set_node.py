# -*- coding: utf-8 -*-
from typing import Any


class DisjointSetNode(object):

    def __init__(self, value: Any) -> None:
        self.value = value
        self.rank = 1
        self.parent = self

    def root(self) -> 'DisjointSetNode':
        if self.parent != self:
            self.parent = self.parent.root()
        return self.parent

    def unite_with(self, other: 'DisjointSetNode') -> None:
        root = self.root()
        other_root = other.root()

        if root == other_root:
            return

        if root.value > other_root.value:
            other_root.rank += root.rank
            root.parent = other_root
        else:
            root.rank += other_root.rank
            other_root.parent = root
