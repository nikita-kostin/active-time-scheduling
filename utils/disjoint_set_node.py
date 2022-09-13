# -*- coding: utf-8 -*-
from typing import Any


class DisjointSetNode(object):
    """
    A class representing a single node in a disjoint set.
    """

    def __init__(self, value: Any) -> None:
        self.value = value
        self.rank = 1
        self.parent = self

    def root(self) -> 'DisjointSetNode':
        """
        Gets the root of the set.
        :return: Node that represents the root.
        """
        if self.parent != self:
            self.parent = self.parent.root()
        return self.parent

    def unite_with(self, other: 'DisjointSetNode') -> None:
        """
        Unite two nodes into a single set.
        :param other: Node to unite with.
        :return: None
        """
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
