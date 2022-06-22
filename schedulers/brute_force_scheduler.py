# -*- coding: utf-8 -*-
from networkx.algorithms.flow import maximum_flow
from typing import List, Set

from models import Job, Schedule
from schedulers import FlowScheduler


class BruteForceScheduler(FlowScheduler):

    def _is_feasible(
            self,
            max_concurrency: int,
            max_t: int,
            jobs: List[Job],
            duration_sum: int,
            active_timestamps: Set[int],
    ) -> bool:
        graph = self._create_initial_graph(max_concurrency, max_t, jobs)

        for t in range(max_t):
            if t in active_timestamps:
                self._open_time_slot(t, jobs, graph)

        flow_value, _ = maximum_flow(graph, 0, 1 + len(jobs) + max_t)

        return flow_value == duration_sum

    def process(self, max_concurrency: int, jobs: List[Job]) -> Schedule:
        max_t = max([job.deadline for job in jobs]) + 1
        duration_sum = sum([job.duration for job in jobs])

        active_timestamps = set()
        for job in jobs:
            for t in range(job.release_time, job.deadline + 1):
                active_timestamps.add(t)

        if self._is_feasible(max_concurrency, max_t, jobs, duration_sum, active_timestamps) is False:
            return Schedule(False, None, None)

        for bitmask in range(2 ** max_t):
            candidate_active_timestamps = set()

            for t in range(max_t):
                if bitmask & (1 << t) != 0:
                    candidate_active_timestamps.add(t)

            if len(candidate_active_timestamps) > len(active_timestamps):
                continue

            if self._is_feasible(max_concurrency, max_t, jobs, duration_sum, candidate_active_timestamps) is True:
                active_timestamps = candidate_active_timestamps

        return Schedule(
            True,
            list(self._merge_active_timestamps(active_timestamps)),
            None,
        )
