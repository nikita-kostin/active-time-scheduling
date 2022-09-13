# -*- coding: utf-8 -*-
from networkx import Graph
from typing import Any, Dict, Tuple, Set, Union

from models import (
    JobMI,
    JobPool,
    JobPoolMI,
    JobScheduleMI,
    Schedule,
    UnitJobPool,
    UnitJobPoolMI,
    TimeInterval,
)
from schedulers import AbstractScheduler
from utils import EdmondsBlossomMatching, UpperDegreeConstrainedSubgraph


class MatchingScheduler(AbstractScheduler):
    """
    This algorithm is based on the matching algorithm presented in "A model for minimizing active processor time"
    (Chang et al., 2012). Given a set of jobs with unit lengths and arbitrary number of execution intervals, it computes
    an optimal solution by reducing the Active Time Problem to general matchings. To compute the matching problem, a
    O(V^3) version of Edmonds' Blossom Algorithm is used. The overall running complexity of the algorithm is therefore
    O((n + T)^3).
    """

    @staticmethod
    def _create_job_schedules_for_job(
            i: int,
            job: JobMI,
            job_pool: Union[UnitJobPoolMI, UnitJobPool],
            matching: Set[Tuple[int, int]],
    ) -> JobScheduleMI:
        for interval in job.availability_intervals:
            for t in range(interval.start, interval.end + 1):
                u = job_pool.size + 2 * t
                v = u + 1
                if (i, u) in matching or (i, v) in matching:
                    return JobScheduleMI(job, [TimeInterval(t, t)])

        return JobScheduleMI(job, [])

    @classmethod
    def process(cls, job_pool: Union[UnitJobPoolMI, UnitJobPool]) -> Schedule:
        """
        Given a set of jobs, computes an optimal solution. The maximum concurrency number B is fixed at 2 as due to the
        algorithm.
        :param job_pool: Job pool of jobs with unit length and arbitrary number of execution intervals.
        :return: Computed schedule.
        """
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


class DegreeConstrainedSubgraphScheduler(AbstractScheduler):
    """
    This algorithm represents the (upper) degree-constrained-subgraph algorithm developed in "A model for minimizing
    active processor time" (Chang et al., 2012). The DCS problem is reduced to general matchings using the technique
    from "Another look at the degree constrained subgraph problem" (Shiloach, 1981). To compute the matching itself,
    a O(V^3) version of Edmonds' Blossom Algorithm is used. The overall complexity of the algorithm is O((nT + L)^3).
    """

    @staticmethod
    def _create_job_schedules_for_job(
            i: int,
            job_pool: Union[JobPoolMI, JobPool],
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
    def process(cls, job_pool: Union[JobPoolMI, JobPool]) -> Schedule:
        """
        Given a set of jobs, computes an optimal solution. The maximum concurrency number B is fixed at 2 as due to the
        algorithm.
        :param job_pool: Job pool of jobs with unit length and arbitrary number of execution intervals.
        :return: Computed schedule.
        """
        if job_pool.size == 0:
            return Schedule(True, [], [])

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
