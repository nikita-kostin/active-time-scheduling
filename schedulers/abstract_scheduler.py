# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Iterable, List, Set, Tuple

from models import ActiveTimeSlot, Job, Schedule


class AbstractScheduler(ABC):

    @staticmethod
    def _merge_active_time_slots(active_time_slots: Iterable[Tuple[int, int]]) -> Iterable[ActiveTimeSlot]:
        active_time_slots = sorted(active_time_slots)

        active_time_slot_start = None
        active_time_slot_end = None

        for start, end in active_time_slots:
            if active_time_slot_start is None or active_time_slot_end is None:
                active_time_slot_start = start
                active_time_slot_end = end
                continue

            if active_time_slot_start <= start <= active_time_slot_end:
                active_time_slot_end = max(active_time_slot_end, end)
            else:
                yield ActiveTimeSlot(active_time_slot_start, active_time_slot_end)
                active_time_slot_start = start
                active_time_slot_end = end

    @staticmethod
    def _merge_active_timestamps(active_timestamps: Set[int]) -> Iterable[ActiveTimeSlot]:
        max_t = max(active_timestamps) + 1

        active_time_slot_start = None

        for t in range(max_t):
            if active_time_slot_start is None and t in active_timestamps:
                active_time_slot_start = t
            if active_time_slot_start is not None and t not in active_timestamps:
                yield ActiveTimeSlot(active_time_slot_start, t - 1)
                active_time_slot_start = None

        if active_time_slot_start is not None:
            yield ActiveTimeSlot(active_time_slot_start, max_t - 1)

    @staticmethod
    def _add_edge(u: int, v: int, graph: List[Set[int]]) -> None:
        graph[u].add(v)
        graph[v].add(u)

    @classmethod
    @abstractmethod
    def process(cls, max_concurrency: int, jobs: List[Job]) -> Schedule:
        pass
