# -*- coding: utf-8 -*-
from networkx import Graph
from typing import List, Tuple, Set

from utils import EdmondsBlossomMatching
from models import JobWithMultipleIntervals, JobScheduleSI, Schedule
from schedulers import AbstractScheduler


class MatchingScheduler(AbstractScheduler):

    @staticmethod
    def _create_job_schedules_for_job(
            i: int,
            jobs: List[JobWithMultipleIntervals],
            matching: Set[Tuple[int, int]],
    ) -> JobScheduleSI:
        for interval in jobs[i].intervals:
            for t in range(interval.start, interval.end + 1):
                u = len(jobs) + 2 * t
                v = u + 1
                if (i, u) in matching or (i, v) in matching:
                    return JobScheduleSI(jobs[i], t, t)

    @classmethod
    def process(cls, max_concurrency: int, jobs: List[JobWithMultipleIntervals]) -> Schedule:
        graph = Graph()

        for i, job in enumerate(jobs):
            for interval in job.intervals:
                for t in range(interval.start, interval.end + 1):
                    graph.add_edge(i, len(jobs) + 2 * t)
                    graph.add_edge(i, len(jobs) + 2 * t + 1)

        matching = EdmondsBlossomMatching().process(graph)

        for i, job in enumerate(jobs):
            for interval in job.intervals:
                for t in range(interval.start, interval.end + 1):
                    graph.add_edge(len(jobs) + 2 * t, len(jobs) + 2 * t + 1)

        matching = EdmondsBlossomMatching().process(graph, initial_matching=matching)
        matching = {(k, v) for k, v in matching.items() if k <= v}

        scheduled_jobs = set()
        active_timestamps = set()
        for u, v in matching:
            u, v = min(u, v), max(u, v)
            if u < len(jobs) <= v:
                scheduled_jobs.add(u)
                active_timestamps.add((v - len(jobs)) // 2)

        return Schedule(
            len(scheduled_jobs) == len(jobs),
            list(cls._merge_active_timestamps(active_timestamps)),
            [cls._create_job_schedules_for_job(i, jobs, matching) for i in range(len(jobs))],
        )
