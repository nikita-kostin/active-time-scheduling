# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from enum import Enum
from itertools import permutations
from networkx import DiGraph
from networkx.algorithms.flow import (
    maximum_flow,
    edmonds_karp,
    shortest_augmenting_path,
    preflow_push,
    dinitz,
    boykov_kolmogorov,
)
from random import shuffle
from typing import Callable, Dict, Iterable, List, Set

from models import Job, JobMI, JobPool, JobScheduleMI, Schedule, TimeInterval
from schedulers import AbstractScheduler
from utils import ford_fulkerson


class FlowMethod(str, Enum):
    EDMONDS_KARP = 'edmonds_karp'
    SHORTEST_AUGMENTING_PATH = 'shortest_augmenting_path'
    PREFLOW_PUSH = 'preflow_push'
    DINITZ = 'dinitz'
    BOYKOV_KOLMOGOROV = 'boykov_kolmogorov'
    FORD_FULKERSON = 'ford_fulkerson'


class AbstractGreedyScheduler(AbstractScheduler, ABC):

    def __init__(self, flow_method: FlowMethod = FlowMethod.PREFLOW_PUSH) -> None:
        self.flow_method = flow_method

    @property
    def flow_func(self) -> Callable:
        return {
            'edmonds_karp': edmonds_karp,
            'shortest_augmenting_path': shortest_augmenting_path,
            'preflow_push': preflow_push,
            'dinitz': dinitz,
            'boykov_kolmogorov': boykov_kolmogorov,
            'ford_fulkerson': ford_fulkerson,
        }[self.flow_method]

    @abstractmethod
    def process(self, job_pool: JobPool, max_concurrency: int) -> Schedule:
        pass


class GreedyScheduler(AbstractGreedyScheduler):

    @staticmethod
    def _create_initial_graph(
            max_concurrency: int,
            max_t: int,
            jobs: List[JobMI],
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
    def _open_time_slot(t: int, jobs: List[JobMI], graph: DiGraph) -> None:
        for i, job in enumerate(jobs):
            for interval in job.availability_intervals:
                if interval.start <= t <= interval.end:
                    u = 1 + i
                    v = 1 + len(jobs) + t

                    graph.add_edge(u, v, capacity=1)

    @staticmethod
    def _close_time_slot(t: int, jobs: List[JobMI], graph: DiGraph) -> None:
        for i, job in enumerate(jobs):
            for interval in job.availability_intervals:
                if interval.start <= t <= interval.end:
                    u = 1 + i
                    v = 1 + len(jobs) + t

                    graph.remove_edge(u, v)

    @staticmethod
    def _create_job_schedules(
            jobs: List[JobMI],
            flow_dict: Dict[int, Dict[int, int]],
    ) -> Iterable[JobScheduleMI]:
        for i, job in enumerate(jobs):
            job_active_timestamps = set()

            for interval in job.availability_intervals:
                for t in range(interval.start, interval.end + 1):
                    if flow_dict[1 + i].get(1 + len(jobs) + t, 0) != 0:
                        job_active_timestamps.add(t)

            yield JobScheduleMI(job, TimeInterval.merge_timestamps(job_active_timestamps))

    @staticmethod
    def _get_t_ordering(job_pool: JobPool) -> List[int]:
        min_t = min([job.release_time for job in job_pool.jobs])
        max_t = max([job.deadline for job in job_pool.jobs]) + 1
        return list(range(min_t, max_t))

    def _apply_optimizations(
            self,
            job_pool: JobPool,
            graph: DiGraph,
            active_timestamps: Set[int],
            max_concurrency: int,
    ) -> None:
        return

    def process(self, job_pool: JobPool, max_concurrency: int) -> Schedule:
        if job_pool.size == 0:
            return Schedule(True, [], [])

        max_t = max([job.deadline for job in job_pool.jobs]) + 1
        duration_sum = sum([job.duration for job in job_pool.jobs])

        graph = self._create_initial_graph(max_concurrency, max_t, job_pool.jobs)

        for t in range(max_t):
            self._open_time_slot(t, job_pool.jobs, graph)

        flow_value, _ = maximum_flow(graph, 0, 1 + len(job_pool.jobs) + max_t, flow_func=self.flow_func)  # noqa

        if flow_value < duration_sum:
            return Schedule(False, None, None)

        active_timestamps = set()

        for t in self._get_t_ordering(job_pool):
            self._close_time_slot(t, job_pool.jobs, graph)

            flow_value, _ = maximum_flow(graph, 0, 1 + len(job_pool.jobs) + max_t, flow_func=self.flow_func)  # noqa

            if flow_value < duration_sum:
                self._open_time_slot(t, job_pool.jobs, graph)
                active_timestamps.add(t)

        _, flow_dict = maximum_flow(graph, 0, 1 + len(job_pool.jobs) + max_t, flow_func=self.flow_func)  # noqa

        self._apply_optimizations(job_pool, graph, active_timestamps, max_concurrency)

        return Schedule(
            True,
            TimeInterval.merge_timestamps(active_timestamps),
            list(self._create_job_schedules(job_pool.jobs, flow_dict)),
        )


class GreedyLocalSearchScheduler(GreedyScheduler):

    def _try_close_open(
            self,
            job_pool: JobPool,
            graph: DiGraph,
            active_timestamps: Set[int],
            max_concurrency: int,
    ) -> bool:
        if len(active_timestamps) < max_concurrency:
            return False

        max_t = max([job.deadline for job in job_pool.jobs]) + 1
        duration_sum = sum([job.duration for job in job_pool.jobs])

        for ts_to_close in permutations(active_timestamps, max_concurrency):
            for ts_to_open in permutations(active_timestamps, max_concurrency - 1):
                ts_to_close = set(ts_to_close).intersection(active_timestamps)
                ts_to_open = set(ts_to_open).difference(active_timestamps)

                for t in ts_to_close:
                    active_timestamps.remove(t)
                    self._close_time_slot(t, job_pool.jobs, graph)
                for t in ts_to_open:
                    active_timestamps.add(t)
                    self._open_time_slot(t, job_pool.jobs, graph)

                flow_value, _ = maximum_flow(graph, 0, 1 + len(job_pool.jobs) + max_t, flow_func=self.flow_func)  # noqa

                if flow_value == duration_sum:
                    return True

                for t in ts_to_open:
                    active_timestamps.remove(t)
                    self._close_time_slot(t, job_pool.jobs, graph)
                for t in ts_to_close:
                    active_timestamps.add(t)
                    self._open_time_slot(t, job_pool.jobs, graph)

        return False

    def _apply_optimizations(
            self,
            job_pool: JobPool,
            graph: DiGraph,
            active_timestamps: Set[int],
            max_concurrency: int,
    ) -> None:
        any_improvements = True

        while any_improvements is True:
            any_improvements = self._try_close_open(job_pool, graph, active_timestamps, max_concurrency)


class GreedyLowestDensityFirstScheduler(GreedyScheduler):

    @staticmethod
    def _get_t_ordering(job_pool: JobPool) -> List[int]:
        frequency = {}
        for job in job_pool.jobs:
            for t in range(job.release_time, job.deadline + 1):
                frequency.setdefault(t, 0)
                frequency[t] += 1

        t_ordering = sorted((item[1], item[0]) for item in frequency.items())

        return [t for _, t in t_ordering]


class GreedyIntervalsScheduler(AbstractGreedyScheduler):

    @staticmethod
    def _create_initial_graph(
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

            graph.add_edge(u, v, capacity=0)

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
        GreedyIntervalsScheduler._extend_interval(jobs, i, intervals, graph, max_concurrency, -delta)

    @staticmethod
    def _create_job_schedules(
            jobs: List[Job],
            intervals: List[TimeInterval],
            flow_dict: Dict[int, Dict[int, int]],
    ) -> Iterable[JobScheduleMI]:
        time_within_interval = {}

        for j, job in enumerate(jobs):
            active_intervals = []

            for i, interval in enumerate(intervals):
                scheduled_time = flow_dict.get(1 + j, {}).get(1 + len(jobs) + i, 0)
                if scheduled_time == 0:
                    continue

                time_within_interval.setdefault(i, 0)

                time_from = time_within_interval[i]
                time_within_interval[i] = (time_within_interval[i] + scheduled_time) % interval.duration
                time_to = time_within_interval[i]

                if time_to <= time_from:
                    active_intervals.append(TimeInterval(interval.start + time_from, interval.end))
                    time_from = 0

                if time_from != time_to:
                    active_intervals.append(TimeInterval(interval.start + time_from, interval.start + time_to - 1))

            yield JobScheduleMI(job, TimeInterval.merge_time_intervals(active_intervals))

    def process(self, job_pool: JobPool, max_concurrency: int) -> Schedule:
        if job_pool.size == 0:
            return Schedule(True, [], [])

        duration_sum = sum([job.duration for job in job_pool.jobs])

        release_time_timestamps = [job.release_time for job in job_pool.jobs]
        deadline_timestamps = [job.deadline + 1 for job in job_pool.jobs]

        timestamps = sorted(set(release_time_timestamps + deadline_timestamps))
        intervals = [
            TimeInterval(timestamps[i], timestamps[i + 1] - 1) for i in range(len(timestamps) - 1)
        ]

        graph = self._create_initial_graph(intervals, job_pool.jobs)

        for i, interval in enumerate(intervals):
            self._extend_interval(job_pool.jobs, i, intervals, graph, max_concurrency, interval.duration)

        flow_value, _ = maximum_flow(
            graph, 0, 1 + len(job_pool.jobs) + len(intervals), flow_func=self.flow_func  # noqa
        )

        if flow_value < duration_sum:
            return Schedule(False, None, None)

        active_intervals = []

        for i in range(len(intervals)):
            left, right = 0, intervals[i].duration + 1

            while right - left > 1:
                middle = (left + right) // 2

                self._reduce_interval(job_pool.jobs, i, intervals, graph, max_concurrency, middle)

                flow_value, _ = maximum_flow(
                    graph, 0, 1 + len(job_pool.jobs) + len(intervals), flow_func=self.flow_func  # noqa
                )

                if flow_value == duration_sum:
                    left = middle
                else:
                    right = middle

                self._extend_interval(job_pool.jobs, i, intervals, graph, max_concurrency, middle)

            self._reduce_interval(job_pool.jobs, i, intervals, graph, max_concurrency, left)

            if left != intervals[i].duration:
                active_intervals.append(TimeInterval(intervals[i].start, intervals[i].end - left))

        _, flow_dict = maximum_flow(graph, 0, 1 + len(job_pool.jobs) + len(intervals), flow_func=self.flow_func)  # noqa

        return Schedule(
            True,
            TimeInterval.merge_time_intervals(active_intervals),
            list(self._create_job_schedules(job_pool.jobs, intervals, flow_dict)),
        )


class MinFeasScheduler(GreedyScheduler):

    @staticmethod
    def _get_t_ordering(job_pool: JobPool) -> List[int]:
        t_ordering = GreedyScheduler._get_t_ordering(job_pool)
        shuffle(t_ordering)
        return t_ordering
