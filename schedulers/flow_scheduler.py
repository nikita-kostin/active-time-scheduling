# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
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


class AbstractFlowScheduler(AbstractScheduler, ABC):

    def __init__(self, flow_method: FlowMethod = FlowMethod.preflow_push) -> None:
        self.flow_method = flow_method

    @abstractmethod
    def process(self, job_pool: JobPoolSI, max_concurrency: int) -> Schedule:
        pass


class FlowScheduler(AbstractFlowScheduler):

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


class FlowIntervalScheduler(AbstractFlowScheduler):

    @staticmethod
    def _create_initial_graph(
            max_concurrency: int,
            intervals: List[TimeInterval],
            jobs: List[Job],
    ) -> DiGraph:
        graph = DiGraph()

        for i, job in enumerate(jobs):
            u, v = 0, 1 + i

            graph.add_edge(u, v, capacity=job.duration)

        for i, interval in enumerate(intervals):
            u = 1 + len(jobs) + i
            v = 1 + len(jobs) + len(intervals)

            graph.add_edge(u, v, capacity=max_concurrency * interval.duration)

        return graph

    @staticmethod
    def _extend_interval(
            jobs: List[Job],
            i: int,
            intervals: List[TimeInterval],
            graph: DiGraph,
            max_concurrency: int,
            delta: int,
    ) -> None:
        for j, job in enumerate(jobs):
            if job.release_time <= intervals[i].start and intervals[i].end <= job.deadline:
                u = 1 + j
                v = 1 + len(jobs) + i

                if graph.has_edge(u, v) is False:
                    graph.add_edge(u, v, capacity=0)

                graph[u][v]['capacity'] += delta

        u = 1 + len(jobs) + i
        v = 1 + len(jobs) + len(intervals)

        graph[u][v]['capacity'] += max_concurrency * delta

    @staticmethod
    def _reduce_interval(
            jobs: List[Job],
            i: int,
            intervals: List[TimeInterval],
            graph: DiGraph,
            max_concurrency: int,
            delta: int,
    ) -> None:
        FlowIntervalScheduler._extend_interval(jobs, i, intervals, graph, max_concurrency, -delta)

    def process(self, job_pool: JobPoolSI, max_concurrency: int) -> Schedule:
        duration_sum = sum([job.duration for job in job_pool.jobs])

        release_time_timestamps = [job.release_time for job in job_pool.jobs]
        deadline_timestamps = [job.deadline + 1 for job in job_pool.jobs]

        timestamps = sorted(set(release_time_timestamps + deadline_timestamps))
        intervals = [
            TimeInterval(timestamps[i], timestamps[i + 1] - 1) for i in range(len(timestamps) - 1)
        ]

        graph = self._create_initial_graph(max_concurrency, intervals, job_pool.jobs)

        for i, interval in enumerate(intervals):
            self._extend_interval(job_pool.jobs, i, intervals, graph, max_concurrency, interval.duration)

        flow_value, _ = maximum_flow(graph, 0, 1 + len(job_pool.jobs) + len(intervals), flow_func=self.flow_method)

        if flow_value < duration_sum:
            return Schedule(False, None, None)

        active_intervals = []

        for i in range(len(intervals)):
            left, right = 0, intervals[i].duration + 1

            while right - left > 1:
                middle = (left + right) // 2

                self._reduce_interval(job_pool.jobs, i, intervals, graph, max_concurrency, middle)

                flow_value, _ = maximum_flow(
                    graph, 0, 1 + len(job_pool.jobs) + len(intervals), flow_func=self.flow_method
                )

                if flow_value == duration_sum:
                    left = middle
                else:
                    right = middle

                self._extend_interval(job_pool.jobs, i, intervals, graph, max_concurrency, middle)

            self._reduce_interval(job_pool.jobs, i, intervals, graph, max_concurrency, left)

            if left != intervals[i].duration:
                active_intervals.append((intervals[i].start + left, intervals[i].end))

        _, flow_dict = maximum_flow(graph, 0, 1 + len(job_pool.jobs) + len(intervals), flow_func=self.flow_method)

        return Schedule(
            True,
            list(self._merge_active_time_slots(active_intervals)),
            None,
        )
