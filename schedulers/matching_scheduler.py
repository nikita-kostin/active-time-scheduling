# -*- coding: utf-8 -*-
from typing import List, Set

from models import Job, Schedule
from schedulers import AbstractScheduler
from utils import MaximumMatching


class MatchingScheduler(AbstractScheduler):

    @classmethod
    def process(cls, max_concurrency: int, jobs: List[Job]) -> Schedule:
        max_t = max([job.deadline for job in jobs]) + 1

        graph = []
        for i in range(len(jobs) + 2 * max_t):
            graph.append(set())

        for i, job in enumerate(jobs):
            for t in range(job.release_time, job.deadline + 1):
                cls._add_edge(i, len(jobs) + 2 * t, graph)
                cls._add_edge(i, len(jobs) + 2 * t + 1, graph)
                cls._add_edge(len(jobs) + 2 * t, len(jobs) + 2 * t + 1, graph)

        m = MaximumMatching.process(graph)

        scheduled_jobs = set()
        active_timestamps = set()
        for u, v in m.items():
            if 0 <= u <= len(jobs) - 1 and len(jobs) <= v:
                scheduled_jobs.add(u)
                active_timestamps.add((v - len(jobs)) // 2)

        return Schedule(
            len(scheduled_jobs) == len(jobs),
            list(cls._merge_active_timestamps(active_timestamps)),
            None,
        )
