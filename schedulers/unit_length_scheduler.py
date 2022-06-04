# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Set

from models import ActiveTimeSlot, Job, JobSchedule, Schedule
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
            js: JobSchedule,
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

    @staticmethod
    def _get_jobs_for_timestamp(
            max_concurrency: int,
            t: int,
            available_jss: Set[JobSchedule],
            deadline_to_jss: Dict[int, Set[JobSchedule]],
    ):
        for js in deadline_to_jss[t]:
            available_jss.remove(js)

            js.execution_start = js.execution_end = t
            yield js

        for _ in range(max_concurrency - len(deadline_to_jss[t])):
            if not available_jss:
                break

            js = available_jss.pop()

            deadline_to_jss[js.execution_end].remove(js)

            js.execution_start = js.execution_end = t
            yield js

    @classmethod
    @abstractmethod
    def _phase_one(cls, max_concurrency: int, job_schedules: List[JobSchedule]) -> Iterable[JobSchedule]:
        pass

    @classmethod
    @abstractmethod
    def _phase_two(cls, max_concurrency: int, job_schedules: List[JobSchedule]) -> Iterable[JobSchedule]:
        pass

    @classmethod
    @abstractmethod
    def _get_active_time_slots(cls, job_schedules: List[JobSchedule]) -> Iterable[ActiveTimeSlot]:
        pass

    @classmethod
    def process(cls, max_concurrency: int, jobs: List[Job]) -> Schedule:
        job_schedules = [JobSchedule(job, job.release_time, job.deadline) for job in jobs]

        job_schedules = list(cls._phase_one(max_concurrency, job_schedules))
        job_schedules = list(cls._phase_two(max_concurrency, job_schedules))

        return Schedule(
            len(job_schedules) == len(jobs),
            list(cls._get_active_time_slots(job_schedules)),
            job_schedules,
        )


class UnitJobsSchedulerNLogN(AbstractUnitJobsScheduler):

    @classmethod
    def _phase_one(cls, max_concurrency: int, job_schedules: List[JobSchedule]) -> Iterable[JobSchedule]:
        jss_sorted_by_release_time = sorted(job_schedules)

        t_to_count = {}
        t_to_node = {}

        for js in reversed(jss_sorted_by_release_time):
            yield from cls._update_deadline_for_job_schedule(max_concurrency, js, t_to_count, t_to_node)

    @classmethod
    def _phase_two(cls, max_concurrency: int, job_schedules: List[JobSchedule]) -> Iterable[JobSchedule]:
        jss_sorted_by_release_time = sorted(job_schedules)

        deadline_to_jss = {}
        for js in job_schedules:
            deadline_to_jss.setdefault(js.execution_end, set())
            deadline_to_jss[js.execution_end].add(js)

        deadlines = sorted(deadline_to_jss.keys())

        i = 0
        available_jss = set()

        for t in deadlines:
            if not deadline_to_jss[t]:
                continue

            while i < len(jss_sorted_by_release_time) and jss_sorted_by_release_time[i].execution_start <= t:
                available_jss.add(jss_sorted_by_release_time[i])
                i += 1

            yield from cls._get_jobs_for_timestamp(max_concurrency, t, available_jss, deadline_to_jss)

    @classmethod
    def _get_active_time_slots(cls, job_schedules: List[JobSchedule]) -> Iterable[ActiveTimeSlot]:
        active_time_slots = [(js.execution_start, js.execution_end) for js in job_schedules]

        yield from cls._merge_active_time_slots(active_time_slots)


class UnitJobsSchedulerT(AbstractUnitJobsScheduler):

    @classmethod
    def _phase_one(cls, max_concurrency: int, job_schedules: List[JobSchedule]) -> Iterable[JobSchedule]:
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
    def _phase_two(cls, max_concurrency: int, job_schedules: List[JobSchedule]) -> Iterable[JobSchedule]:
        max_t = max(js.execution_end for js in job_schedules) + 1

        release_time_to_jss = {}
        deadline_to_jss = {}
        for js in job_schedules:
            release_time_to_jss.setdefault(js.execution_start, [])
            release_time_to_jss[js.execution_start].append(js)

            deadline_to_jss.setdefault(js.execution_end, set())
            deadline_to_jss[js.execution_end].add(js)

        available_jss = set()

        for t in range(max_t):
            for js in release_time_to_jss.get(t, []):
                available_jss.add(js)

            if not deadline_to_jss.get(t, []):
                continue

            yield from cls._get_jobs_for_timestamp(max_concurrency, t, available_jss, deadline_to_jss)

    @classmethod
    def _get_active_time_slots(cls, job_schedules: List[JobSchedule]) -> Iterable[ActiveTimeSlot]:
        active_timestamps = set()
        for js in job_schedules:
            active_timestamps.add(js.execution_start)

        yield from cls._merge_active_timestamps(active_timestamps)


UnitJobsScheduler = UnitJobsSchedulerT
