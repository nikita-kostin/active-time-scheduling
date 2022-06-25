# -*- coding: utf-8 -*-
from networkx import Graph, max_weight_matching
from typing import List

from models import JobWithMultipleIntervals, Schedule
from schedulers import AbstractScheduler


class MatchingScheduler(AbstractScheduler):

    @classmethod
    def process(cls, max_concurrency: int, jobs: List[JobWithMultipleIntervals]) -> Schedule:
        graph = Graph()

        for i, job in enumerate(jobs):
            for interval in job.intervals:
                for t in range(interval.start, interval.end + 1):
                    graph.add_edge(i, len(jobs) + 2 * t, weight=2)
                    graph.add_edge(i, len(jobs) + 2 * t + 1, weight=2)
                    graph.add_edge(len(jobs) + 2 * t, len(jobs) + 2 * t + 1, weight=1)

        matching = max_weight_matching(graph, maxcardinality=True)

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
            None,
        )
