# -*- coding: utf-8 -*-
from typing import Dict, List, Set, Tuple

from models import Job, Schedule
from schedulers import AbstractScheduler
from utils import MaximumFlow


class FlowScheduler(AbstractScheduler):

    @staticmethod
    def _create_initial_graph_and_costs(
            max_concurrency: int,
            max_t: int,
            jobs: List[Job],
    ) -> Tuple[List[Set[int]], Dict[Tuple[int, int], int]]:
        graph = []
        c = dict()

        for _ in range(1 + len(jobs) + max_t + 1):
            graph.append(set())

        for i, job in enumerate(jobs):
            u, v = 0, 1 + i

            graph[u].add(v)
            graph[v].add(u)

            c[(u, v)] = job.duration

        for i in range(max_t):
            u = 1 + len(jobs) + i
            v = 1 + len(jobs) + max_t

            graph[u].add(v)
            graph[v].add(u)

            c[(u, v)] = max_concurrency

        return graph, c

    @staticmethod
    def _open_time_slot(t: int, jobs: List[Job], graph: List[Set[int]], c: Dict[Tuple[int, int], int]) -> None:
        for i, job in enumerate(jobs):
            if job.release_time <= t <= job.deadline:
                u = 1 + i
                v = 1 + len(jobs) + t

                graph[u].add(v)
                graph[v].add(u)

                c[(u, v)] = 1

    @staticmethod
    def _close_time_slot(t: int, jobs: List[Job], graph: List[Set[int]], c: Dict[Tuple[int, int], int]) -> None:
        for i, job in enumerate(jobs):
            if job.release_time <= t <= job.deadline:
                u = 1 + i
                v = 1 + len(jobs) + t

                graph[u].remove(v)
                graph[v].remove(u)

                c.pop((u, v))

    @classmethod
    def process(cls, max_concurrency: int, jobs: List[Job]) -> Schedule:
        max_t = max([job.deadline for job in jobs]) + 1

        graph, c = cls._create_initial_graph_and_costs(max_concurrency, max_t, jobs)

        for t in range(max_t):
            FlowScheduler._open_time_slot(t, jobs, graph, c)

        duration_sum = sum([job.duration for job in jobs])

        maximum_flow = MaximumFlow(graph, c, 0, 1 + len(jobs) + max_t)
        if maximum_flow.process() < duration_sum:
            return Schedule(False, None, None)

        active_timestamps = set()

        for t in range(max_t):
            FlowScheduler._close_time_slot(t, jobs, graph, c)

            if maximum_flow.process() < duration_sum:
                FlowScheduler._open_time_slot(t, jobs, graph, c)
                active_timestamps.add(t)

        return Schedule(
            True,
            list(cls._merge_active_timestamps(active_timestamps)),
            None,
        )
