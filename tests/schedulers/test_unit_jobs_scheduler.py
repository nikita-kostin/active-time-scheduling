# -*- coding: utf-8 -*-
import pytest
from random import randint
from typing import Type

from schedulers import BruteForceScheduler, UnitJobsSchedulerNLogN, UnitJobsSchedulerT
from schedulers.unit_jobs_scheduler import AbstractUnitJobsScheduler
from tests.schedulers.common import check_equality, generate_jobs_uniform_distribution


class TestUnitJobsScheduler(object):

    @pytest.mark.repeat(1000)
    @pytest.mark.parametrize('scheduler_b', [UnitJobsSchedulerNLogN, UnitJobsSchedulerT])
    def test_against_brute_force(self, scheduler_b: Type[AbstractUnitJobsScheduler]) -> None:
        max_length = randint(1, 5)
        max_t = randint(4, 9)
        max_concurrency = randint(1, 4)
        number_of_jobs = randint(1, max_t // max_length * max_concurrency + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, 1))

        schedule_a = BruteForceScheduler().process(job_pool, max_concurrency)
        schedule_b = scheduler_b().process(job_pool, max_concurrency)  # noqa

        check_equality(schedule_a, schedule_b, job_pool, max_concurrency)

    @pytest.mark.repeat(1000)
    def test_against_each_other(self) -> None:
        max_length = randint(1, 31)
        max_t = randint(50, 101)
        max_concurrency = randint(1, 8)
        number_of_jobs = randint(1, max_t // max_length * max_concurrency + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, 1))

        schedule_a = UnitJobsSchedulerNLogN.process(job_pool, max_concurrency)  # noqa
        schedule_b = UnitJobsSchedulerT.process(job_pool, max_concurrency)  # noqa

        check_equality(schedule_a, schedule_b, job_pool, max_concurrency)
