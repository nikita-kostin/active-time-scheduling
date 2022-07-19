# -*- coding: utf-8 -*-
import pytest
from itertools import islice
from random import randint
from typing import Type

from models import UnitJobPoolSI
from schedulers import BruteForceScheduler, UnitJobsSchedulerNLogN, UnitJobsSchedulerT
from schedulers.unit_jobs_scheduler import AbstractUnitJobsScheduler
from tests.generators import JobsGenerator
from tests.schedulers.common import check_equality


class TestUnitJobsScheduler(object):

    @pytest.mark.repeat(1000)
    @pytest.mark.parametrize('scheduler_b', [UnitJobsSchedulerNLogN, UnitJobsSchedulerT])
    def test_against_brute_force(self, scheduler_b: Type[AbstractUnitJobsScheduler]) -> None:
        max_t = randint(2, 6)
        max_concurrency = randint(1, 5)
        jobs_count = randint(max_t // 2, max_t * max_concurrency)

        jobs = list(islice(JobsGenerator(1, max_t), jobs_count))
        job_pool = UnitJobPoolSI()
        job_pool.jobs = jobs

        schedule_a = BruteForceScheduler().process(job_pool, max_concurrency)
        schedule_b = scheduler_b().process(job_pool, max_concurrency)

        check_equality(schedule_a, schedule_b, job_pool, max_concurrency)

    @pytest.mark.repeat(1000)
    def test_against_each_other(self) -> None:
        max_t = randint(50, 100)
        max_concurrency = randint(1, 7)
        jobs_count = randint(max_t // 2, max_t * max_concurrency)

        jobs = list(islice(JobsGenerator(1, max_t), jobs_count))
        job_pool = UnitJobPoolSI()
        job_pool.jobs = jobs

        schedule_a = UnitJobsSchedulerNLogN.process(job_pool, max_concurrency)
        schedule_b = UnitJobsSchedulerT.process(job_pool, max_concurrency)

        check_equality(schedule_a, schedule_b, job_pool, max_concurrency)
