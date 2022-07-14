# -*- coding: utf-8 -*-
from networkx import Graph
from typing import List, Tuple, Set

from utils import EdmondsBlossomMatching
from models import JobMI, JobScheduleSI, Schedule, UnitJobPoolMI
from schedulers import AbstractScheduler


class MatchingScheduler(AbstractScheduler):

    @staticmethod
    def _create_job_schedules_for_job(
            i: int,
            jobs: List[JobMI],
            matching: Set[Tuple[int, int]],
    ) -> JobScheduleSI:
        for interval in jobs[i].availability_intervals:
            for t in range(interval.start, interval.end + 1):
                u = len(jobs) + 2 * t
                v = u + 1
                if (i, u) in matching or (i, v) in matching:
                    return JobScheduleSI(jobs[i], t, t)

    @classmethod
    def process(cls, job_pool: UnitJobPoolMI) -> Schedule:
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

        return Schedule(
            len(scheduled_jobs) == job_pool.size,
            list(cls._merge_active_timestamps(active_timestamps)),
            [cls._create_job_schedules_for_job(i, job_pool.jobs, matching) for i in range(job_pool.size)],
        )
