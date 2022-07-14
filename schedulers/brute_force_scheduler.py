# -*- coding: utf-8 -*-
from networkx.algorithms.flow import maximum_flow
from typing import Dict, List, Set, Tuple

from models import Job, JobPoolMI, Schedule
from schedulers import FlowScheduler


class BruteForceScheduler(FlowScheduler):

    def _compute_flow(
            self,
            max_concurrency: int,
            max_t: int,
            jobs: List[Job],
            active_timestamps: Set[int],
    ) -> Tuple[int, Dict[int, Dict[int, int]]]:
        graph = self._create_initial_graph(max_concurrency, max_t, jobs)

        for t in range(max_t):
            if t in active_timestamps:
                self._open_time_slot(t, jobs, graph)

        return maximum_flow(graph, 0, 1 + len(jobs) + max_t, flow_func=self.flow_method)

    def process(self, job_pool: JobPoolMI, max_concurrency: int) -> Schedule:
        max_t = max([job.deadline for job in job_pool.jobs]) + 1
        duration_sum = sum([job.duration for job in job_pool.jobs])

        active_timestamps = set()
        for job in job_pool.jobs:
            for t in range(job.release_time, job.deadline + 1):
                active_timestamps.add(t)

        flow_value, _ = self._compute_flow(max_concurrency, max_t, job_pool.jobs, active_timestamps)

        if flow_value != duration_sum:
            return Schedule(False, None, None)

        job_schedules = None

        for bitmask in range(2 ** max_t):
            candidate_active_timestamps = set()

            for t in range(max_t):
                if bitmask & (1 << t) != 0:
                    candidate_active_timestamps.add(t)

            if len(candidate_active_timestamps) > len(active_timestamps):
                continue

            flow_value, flow_dict = self._compute_flow(
                max_concurrency, max_t, job_pool.jobs, candidate_active_timestamps
            )

            if flow_value == duration_sum:
                active_timestamps = candidate_active_timestamps
                job_schedules = list(self._create_job_schedules(job_pool.jobs, flow_dict))

        return Schedule(
            True,
            list(self._merge_active_timestamps(active_timestamps)),
            job_schedules,
        )
