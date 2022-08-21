# -*- coding: utf-8 -*-
from networkx import Graph
from typing import Any, Dict, List, Tuple, Set

from models import JobMI, JobPoolMI, JobScheduleMI, JobScheduleSI, Schedule, UnitJobPoolMI, TimeInterval
from schedulers import AbstractScheduler
from utils import EdmondsBlossomMatching, UpperDegreeConstrainedSubgraph


class MatchingScheduler(AbstractScheduler):

    @staticmethod
    def _create_job_schedules_for_job(
            i: int,
            job: JobMI,
            job_pool: JobPoolMI,
            matching: Set[Tuple[int, int]],
    ) -> JobScheduleSI:
        for interval in job.availability_intervals:
            for t in range(interval.start, interval.end + 1):
                u = job_pool.size + 2 * t
                v = u + 1
                if (i, u) in matching or (i, v) in matching:
                    return JobScheduleSI(job, t, t)

    @classmethod
    def process(cls, job_pool: UnitJobPoolMI, **kwargs) -> Schedule:
        graph = Graph()

        for i, job in enumerate(job_pool.jobs):
            for interval in job.availability_intervals:
                for t in range(interval.start, interval.end + 1):
                    graph.add_edge(i, job_pool.size + 2 * t)
                    graph.add_edge(i, job_pool.size + 2 * t + 1)

        matching = EdmondsBlossomMatching().process(graph)

        for i, job in enumerate(job_pool.jobs):
            for interval in job.availability_intervals:
                for t in range(interval.start, interval.end + 1):
                    graph.add_edge(job_pool.size + 2 * t, job_pool.size + 2 * t + 1)

        matching = EdmondsBlossomMatching().process(graph, initial_matching=matching)
        matching = {(k, v) for k, v in matching.items() if k <= v}

        scheduled_jobs = set()
        active_timestamps = set()
        for u, v in matching:
            u, v = min(u, v), max(u, v)
            if u < job_pool.size <= v:
                scheduled_jobs.add(u)
                active_timestamps.add((v - job_pool.size) // 2)

        all_jobs_scheduled = len(scheduled_jobs) == job_pool.size

        return Schedule(
            all_jobs_scheduled,
            None if all_jobs_scheduled is False else TimeInterval.merge_timestamps(active_timestamps),
            None if all_jobs_scheduled is False else [
                cls._create_job_schedules_for_job(i, job, job_pool, matching) for i, job in enumerate(job_pool.jobs)
            ],
        )


class UpperDegreeConstrainedSubgraphScheduler(AbstractScheduler):

    @staticmethod
    def _create_job_schedules_for_job(
            i: int,
            job_pool: JobPoolMI,
            job: JobMI,
            dcs: Dict[Any, Set[Any]],
    ) -> JobScheduleMI:
        active_timestamps = set()

        for interval in job.availability_intervals:
            for t in range(interval.start, interval.end + 1):
                u = job_pool.size + 3 * t
                if u in dcs[i]:
                    active_timestamps.add(t)

        return JobScheduleMI(job, TimeInterval.merge_timestamps(active_timestamps))

    @classmethod
    def process(cls, job_pool: JobPoolMI, **kwargs) -> Schedule:
        g = Graph()

        constraints = {}

        for i, job in enumerate(job_pool.jobs):
            for interval in job.availability_intervals:
                for t in range(interval.start, interval.end + 1):
                    g.add_edge(i, job_pool.size + 3 * t)

                    g.add_node(job_pool.size + 3 * t + 1)
                    g.add_node(job_pool.size + 3 * t + 2)

                    constraints[i] = job.duration
                    constraints[job_pool.size + 3 * t] = 2
                    constraints[job_pool.size + 3 * t + 1] = 1
                    constraints[job_pool.size + 3 * t + 2] = 1

        h = UpperDegreeConstrainedSubgraph().construct_h(g, constraints)
        matching = EdmondsBlossomMatching().process(h)

        for i, job in enumerate(job_pool.jobs):
            for interval in job.availability_intervals:
                for t in range(interval.start, interval.end + 1):
                    g.add_edge(job_pool.size + 3 * t, job_pool.size + 3 * t + 1)
                    g.add_edge(job_pool.size + 3 * t + 1, job_pool.size + 3 * t + 2)
                    g.add_edge(job_pool.size + 3 * t + 2, job_pool.size + 3 * t)

        h = UpperDegreeConstrainedSubgraph().construct_h(g, constraints)
        matching = EdmondsBlossomMatching().process(h, initial_matching=matching)

        dcs = UpperDegreeConstrainedSubgraph().construct_dcs(g, matching)

        demand = {i: job.duration for i, job in enumerate(job_pool.jobs)}
        active_timestamps = set()
        for u, vs in dcs.items():
            for v in vs:
                if u < job_pool.size <= v:
                    demand[u] -= 1
                    active_timestamps.add((v - job_pool.size) // 3)

        all_jobs_scheduled = max(demand.values()) == 0

        return Schedule(
            all_jobs_scheduled,
            None if all_jobs_scheduled is False else TimeInterval.merge_timestamps(active_timestamps),
            None if all_jobs_scheduled is False else [
                cls._create_job_schedules_for_job(i, job_pool, job, dcs) for i, job in enumerate(job_pool.jobs)
            ],
        )
