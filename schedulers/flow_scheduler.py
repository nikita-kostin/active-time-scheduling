# -*- coding: utf-8 -*-
from enum import Enum
from networkx import DiGraph
from networkx.algorithms.flow import maximum_flow, edmonds_karp, preflow_push, dinitz
from typing import List

from models import Job, Schedule
from schedulers import AbstractScheduler


class FlowMethod(Enum):
    edmonds_karp = edmonds_karp
    preflow_push = preflow_push
    dinitz = dinitz


class FlowScheduler(AbstractScheduler):

    def __init__(self, method: FlowMethod = preflow_push) -> None:
        self.method = method

    @staticmethod
    def _create_initial_graph(
            max_concurrency: int,
            max_t: int,
            jobs: List[Job],
    ) -> DiGraph:
        graph = DiGraph()

        for i, job in enumerate(jobs):
            u, v = 0, 1 + i

            graph.add_edge(u, v, capacity=job.duration)

        for t in range(max_t):
            u = 1 + len(jobs) + t
            v = 1 + len(jobs) + max_t

            graph.add_edge(u, v, capacity=max_concurrency)

        return graph

    @staticmethod
    def _open_time_slot(t: int, jobs: List[Job], graph: DiGraph) -> None:
        for i, job in enumerate(jobs):
            if job.release_time <= t <= job.deadline:
                u = 1 + i
                v = 1 + len(jobs) + t

                graph.add_edge(u, v, capacity=1)

    @staticmethod
    def _close_time_slot(t: int, jobs: List[Job], graph: DiGraph) -> None:
        for i, job in enumerate(jobs):
            if job.release_time <= t <= job.deadline:
                u = 1 + i
                v = 1 + len(jobs) + t

                graph.remove_edge(u, v)

    def process(self, max_concurrency: int, jobs: List[Job]) -> Schedule:
        max_t = max([job.deadline for job in jobs]) + 1
        duration_sum = sum([job.duration for job in jobs])

        graph = self._create_initial_graph(max_concurrency, max_t, jobs)

        for t in range(max_t):
            self._open_time_slot(t, jobs, graph)

        flow_value, _ = maximum_flow(graph, 0, 1 + len(jobs) + max_t)

        if flow_value < duration_sum:
            return Schedule(False, None, None)

        active_timestamps = set()

        for t in range(max_t):
            self._close_time_slot(t, jobs, graph)

            flow_value, _ = maximum_flow(graph, 0, 1 + len(jobs) + max_t)

            if flow_value < duration_sum:
                self._open_time_slot(t, jobs, graph)
                active_timestamps.add(t)

        return Schedule(
            True,
            list(self._merge_active_timestamps(active_timestamps)),
            None,
        )
