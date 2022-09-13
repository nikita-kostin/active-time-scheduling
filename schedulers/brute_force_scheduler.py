# -*- coding: utf-8 -*-
from networkx.algorithms.flow import maximum_flow
from typing import Dict, List, Set, Tuple, Union

from models import JobMI, JobPool, JobPoolMI, Schedule, TimeInterval
from schedulers import GreedyScheduler


class BruteForceScheduler(GreedyScheduler):
    """
    This class is used solely for testing purposes. The algorithm iterates among all possible combinations of open and
    closed time slots and selects the feasible schedule with the least amount of active time. The feasibility is
    confirmed using the feasibility network as described in "Energy-aware batch scheduling" (Chang, 2013).
    """

    def _compute_flow(
            self,
            max_concurrency: int,
            max_t: int,
            jobs: List[JobMI],
            active_timestamps: Set[int],
    ) -> Tuple[int, Dict[int, Dict[int, int]]]:
        graph = self._create_initial_graph(max_concurrency, max_t, jobs)

        for t in range(max_t):
            if t in active_timestamps:
                self._open_time_slot(t, jobs, graph)

        return maximum_flow(graph, 0, 1 + len(jobs) + max_t, flow_func=self.flow_func)  # noqa

    def process(self, job_pool: Union[JobPoolMI, JobPool], max_concurrency: int) -> Schedule:
        """
        Computes the optimal schedule given a set of job and maximum concurrency.
        :param job_pool: Job pool of arbitrary type jobs.
        :param max_concurrency: Maximum number of jobs allowed to run concurrently.
        :return: Computed schedule.
        """
        if job_pool.size == 0:
            return Schedule(True, [], [])

        max_t = max(
            [interval.end for job in job_pool.jobs for interval in job.availability_intervals],
            default=0,
        ) + 1
        duration_sum = sum([job.duration for job in job_pool.jobs])

        active_timestamps = set()
        for job in job_pool.jobs:
            for interval in job.availability_intervals:
                for t in range(interval.start, interval.end + 1):
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
            TimeInterval.merge_timestamps(active_timestamps),
            job_schedules,
        )
