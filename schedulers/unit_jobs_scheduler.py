# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional
from queue import PriorityQueue

from models import UnitJobPoolSI, JobScheduleSI, Schedule, TimeInterval
from schedulers import AbstractScheduler
from utils import DisjointSetNode


class AbstractUnitJobsScheduler(AbstractScheduler, ABC):

    @staticmethod
    def _init_for_timestamp(t: int, t_to_count: Dict[int, int], t_to_node: Dict[int, DisjointSetNode]) -> None:
        if t_to_node.get(t, None) is None:
            t_to_count[t] = 0
            t_to_node[t] = DisjointSetNode(t)

    @classmethod
    def _update_deadline_for_job_schedule(
            cls,
            max_concurrency: int,
            js: JobScheduleSI,
            t_to_count: Dict[int, int],
            t_to_node: Dict[int, DisjointSetNode],
    ) -> None:
        cls._init_for_timestamp(js.execution_end, t_to_count, t_to_node)

        js.execution_end = t_to_node[js.execution_end].root().value

        if js.execution_start <= js.execution_end:
            t_to_count[js.execution_end] += 1
            yield js

        if t_to_count[js.execution_end] == max_concurrency:
            cls._init_for_timestamp(js.execution_end - 1, t_to_count, t_to_node)

            t_to_node[js.execution_end].unite_with(t_to_node[js.execution_end - 1])

    @classmethod
    @abstractmethod
    def _phase_one(cls, max_concurrency: int, job_schedules: List[JobScheduleSI]) -> Iterable[JobScheduleSI]:
        pass

    @classmethod
    @abstractmethod
    def _phase_two(cls, max_concurrency: int, job_schedules: List[JobScheduleSI]) -> Iterable[JobScheduleSI]:
        pass

    @classmethod
    @abstractmethod
    def _get_active_time_slots(cls, job_schedules: List[JobScheduleSI]) -> Iterable[TimeInterval]:
        pass

    @classmethod
    def process(cls, job_pool: UnitJobPoolSI, max_concurrency: int) -> Schedule:
        job_schedules = [JobScheduleSI(job, job.release_time, job.deadline) for job in job_pool.jobs]

        job_schedules = list(cls._phase_one(max_concurrency, job_schedules))
        job_schedules = list(cls._phase_two(max_concurrency, job_schedules))

        return Schedule(
            len(job_schedules) == job_pool.size,
            list(cls._get_active_time_slots(job_schedules)),
            job_schedules,
        )


class UnitJobsSchedulerNLogN(AbstractUnitJobsScheduler):

    @classmethod
    def _phase_one(cls, max_concurrency: int, job_schedules: List[JobScheduleSI]) -> Iterable[JobScheduleSI]:
        jss_sorted_by_release_time = sorted(job_schedules)

        t_to_count = {}
        t_to_node = {}

        for js in reversed(jss_sorted_by_release_time):
            yield from cls._update_deadline_for_job_schedule(max_concurrency, js, t_to_count, t_to_node)

    @classmethod
    def _phase_two(cls, max_concurrency: int, job_schedules: List[JobScheduleSI]) -> Iterable[JobScheduleSI]:
        jss_sorted_by_release_time = sorted(job_schedules)

        deadline_to_jss = {}
        for js in job_schedules:
            deadline_to_jss.setdefault(js.execution_end, set())
            deadline_to_jss[js.execution_end].add(js)

        deadlines = sorted(deadline_to_jss.keys())

        i = 0
        used = set()
        available_jss = PriorityQueue()

        for t in deadlines:
            if not deadline_to_jss[t]:
                continue

            while i < len(jss_sorted_by_release_time) and jss_sorted_by_release_time[i].execution_start <= t:
                js = jss_sorted_by_release_time[i]
                available_jss.put((js.execution_end, js))
                i += 1

            for js in deadline_to_jss[t]:
                used.add(js)

                js.execution_start = js.execution_end = t
                yield js

            for _ in range(max_concurrency - len(deadline_to_jss[t])):
                js = None

                while True:
                    if available_jss.empty() is True:
                        break

                    _, js = available_jss.get()
                    if js in used:
                        js = None
                        continue

                    break

                if js is None:
                    break

                deadline_to_jss[js.execution_end].remove(js)

                js.execution_start = js.execution_end = t
                yield js

    @classmethod
    def _get_active_time_slots(cls, job_schedules: List[JobScheduleSI]) -> Iterable[TimeInterval]:
        active_time_intervals = [TimeInterval(js.execution_start, js.execution_end) for js in job_schedules]

        yield from TimeInterval.merge_time_intervals(active_time_intervals)


class UnitJobsSchedulerT(AbstractUnitJobsScheduler):

    @classmethod
    def _phase_one(cls, max_concurrency: int, job_schedules: List[JobScheduleSI]) -> Iterable[JobScheduleSI]:
        max_t = max(js.execution_end for js in job_schedules) + 1

        release_time_to_jss = {}
        for js in job_schedules:
            release_time_to_jss.setdefault(js.execution_start, [])
            release_time_to_jss[js.execution_start].append(js)

        t_to_count = {}
        t_to_node = {}

        for t in range(max_t - 1, -1, -1):
            if release_time_to_jss.get(t, None) is None:
                continue

            for js in release_time_to_jss[t]:
                yield from cls._update_deadline_for_job_schedule(max_concurrency, js, t_to_count, t_to_node)

    @classmethod
    def _phase_two(cls, max_concurrency: int, job_schedules: List[JobScheduleSI]) -> Iterable[JobScheduleSI]:
        max_t = max(js.execution_end for js in job_schedules) + 1

        release_time_to_jss = {}
        deadline_to_jss = {}
        for js in job_schedules:
            release_time_to_jss.setdefault(js.execution_start, [])
            release_time_to_jss[js.execution_start].append(js)

            deadline_to_jss.setdefault(js.execution_end, [])
            deadline_to_jss[js.execution_end].append(js)

        release_time_to_idx = {}
        deadline_to_idx = {}
        deadlines = []
        t_to_count = {}
        t_to_node = {}

        for t in range(max_t):
            if t in release_time_to_jss:
                release_time_to_idx[t] = len(deadlines)
            if t in deadline_to_jss:
                deadline_to_idx[t] = len(deadlines)

                deadlines.append(t)

                t_to_count[t] = 0
                t_to_node[t] = DisjointSetNode(-t)

        for deadline in deadlines:
            used = False

            for js in deadline_to_jss[deadline]:
                rounded_release_time = deadlines[release_time_to_idx[js.execution_start]]

                t = -t_to_node[rounded_release_time].root().value

                while t_to_count[t] == max_concurrency:
                    next_deadline = deadlines[deadline_to_idx[t] + 1]
                    t_to_node[t].unite_with(t_to_node[next_deadline])
                    t = -t_to_node[t].root().value

                js.execution_start = js.execution_end = t
                yield js

                if t == deadline:
                    used = True

                t_to_count[t] += 1

            if used is False:
                t_to_count[deadline] = max_concurrency

    @classmethod
    def _get_active_time_slots(cls, job_schedules: List[JobScheduleSI]) -> Iterable[TimeInterval]:
        active_timestamps = set()
        for js in job_schedules:
            active_timestamps.add(js.execution_start)

        yield from TimeInterval.merge_timestamps(active_timestamps)


UnitJobsScheduler = UnitJobsSchedulerT
