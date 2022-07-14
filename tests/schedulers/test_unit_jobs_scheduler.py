# -*- coding: utf-8 -*-
import pytest
from itertools import islice
from random import randint
from typing import List, Type

from models import Job, Schedule, UnitJobPoolSI
from schedulers import BruteForceScheduler, UnitJobsSchedulerNLogN, UnitJobsSchedulerT
from schedulers.unit_jobs_scheduler import AbstractUnitJobsScheduler
from tests.generators import JobsGenerator


class TestUnitJobsScheduler(object):

    @staticmethod
    def _compare_schedules(jobs: List[Job], schedule_a: Schedule, schedule_b: Schedule) -> None:
        expected = schedule_a.all_jobs_scheduled
        actual = schedule_b.all_jobs_scheduled
        assert actual == expected, str(jobs)

        if schedule_a.all_jobs_scheduled is True:
            expected = sum([ts.end - ts.start + 1 for ts in schedule_a.active_time_slots])
            actual = sum([ts.end - ts.start + 1 for ts in schedule_b.active_time_slots])
            assert actual == expected, str(jobs)

    @pytest.mark.repeat(1000)
    @pytest.mark.parametrize('scheduler_b', [UnitJobsSchedulerNLogN, UnitJobsSchedulerT])
    def test_against_brute_force(self, scheduler_b: Type[AbstractUnitJobsScheduler]) -> None:
        max_t = randint(2, 6)
        max_concurrency = randint(1, 5)
        jobs_count = randint(max_t // 2, max_t * max_concurrency)

        jobs = list(islice(JobsGenerator(1, max_t), jobs_count))
        job_pool = UnitJobPoolSI()
        job_pool.jobs = jobs

        self._compare_schedules(
            jobs,
            BruteForceScheduler().process(job_pool, max_concurrency),
            scheduler_b().process(job_pool, max_concurrency),
        )

    @pytest.mark.repeat(1000)
    def test_against_each_other(self) -> None:
        max_t = randint(50, 100)
        max_concurrency = randint(1, 7)
        jobs_count = randint(max_t // 2, max_t * max_concurrency)

        jobs = list(islice(JobsGenerator(1, max_t), jobs_count))
        job_pool = UnitJobPoolSI()
        job_pool.jobs = jobs

        self._compare_schedules(
            jobs,
            UnitJobsSchedulerNLogN.process(job_pool, max_concurrency),
            UnitJobsSchedulerT.process(job_pool, max_concurrency),
        )
