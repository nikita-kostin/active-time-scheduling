# -*- coding: utf-8 -*-
from enum import Enum
from networkx import DiGraph
from networkx.algorithms.flow import (
    maximum_flow,
    edmonds_karp,
    shortest_augmenting_path,
    preflow_push,
    dinitz,
    boykov_kolmogorov,
)
from typing import Dict, Iterable, List

from models import Job, JobPoolSI, JobScheduleMI, Schedule, TimeInterval
from schedulers import AbstractScheduler
from utils import ford_fulkerson


class FlowMethod(Enum):
    edmonds_karp = edmonds_karp
    shortest_augmenting_path = shortest_augmenting_path
    preflow_push = preflow_push
    dinitz = dinitz
    boykov_kolmogorov = boykov_kolmogorov
    ford_fulkerson = ford_fulkerson


class FlowScheduler(AbstractScheduler):

    def __init__(self, flow_method: FlowMethod = FlowMethod.preflow_push) -> None:
        self.flow_method = flow_method

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

    @staticmethod
    def _create_job_schedules(
            jobs: List[Job],
            flow_dict: Dict[int, Dict[int, int]],
    ) -> Iterable[JobScheduleMI]:
        for i, job in enumerate(jobs):
            job_active_timestamps = {
                t for t in range(job.release_time, job.deadline + 1) if flow_dict[1 + i].get(1 + len(jobs) + t, 0) != 0
            }

            yield JobScheduleMI(job, list(AbstractScheduler._merge_active_timestamps(job_active_timestamps)))

    def process(self, job_pool: JobPoolSI, max_concurrency: int) -> Schedule:
        max_t = max([job.deadline for job in job_pool.jobs]) + 1
        duration_sum = sum([job.duration for job in job_pool.jobs])

        graph = self._create_initial_graph(max_concurrency, max_t, job_pool.jobs)

        for t in range(max_t):
            self._open_time_slot(t, job_pool.jobs, graph)

        flow_value, _ = maximum_flow(graph, 0, 1 + len(job_pool.jobs) + max_t, flow_func=self.flow_method)

        if flow_value < duration_sum:
            return Schedule(False, None, None)

        active_timestamps = set()

        for t in range(max_t):
            self._close_time_slot(t, job_pool.jobs, graph)

            flow_value, _ = maximum_flow(graph, 0, 1 + len(job_pool.jobs) + max_t, flow_func=self.flow_method)

            if flow_value < duration_sum:
                self._open_time_slot(t, job_pool.jobs, graph)
                active_timestamps.add(t)

        _, flow_dict = maximum_flow(graph, 0, 1 + len(job_pool.jobs) + max_t, flow_func=self.flow_method)

        return Schedule(
            True,
            list(self._merge_active_timestamps(active_timestamps)),
            list(self._create_job_schedules(job_pool.jobs, flow_dict)),
        )
