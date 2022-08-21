# -*- coding: utf-8 -*-
import pytest
from random import randint
from typing import Type

from models import UnitJobPool, TimeInterval
from schedulers import BruteForceScheduler, LazyActivationSchedulerNLogN, LazyActivationSchedulerT
from schedulers.lazy_activation_scheduler import AbstractLazyActivationScheduler
from tests.schedulers.common import check_equality, generate_jobs_uniform_distribution


class TestLazyActivationScheduler(object):

    @pytest.mark.parametrize('scheduler', [LazyActivationSchedulerNLogN, LazyActivationSchedulerT])
    def test_simple_examples(self, scheduler: Type[AbstractLazyActivationScheduler]) -> None:
        job_pool = UnitJobPool()
        job_pool.add_job(1, 4)
        job_pool.add_job(4, 8)
        job_pool.add_job(10, 10)

        schedule = scheduler().process(job_pool, 2)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == [
            TimeInterval(4, 4),
            TimeInterval(10, 10),
        ]
        assert len(schedule.job_schedules) == 3

        job_pool = UnitJobPool()
        job_pool.add_job(1, 1)
        job_pool.add_job(1, 1)

        schedule = scheduler().process(job_pool, 1)

        assert schedule.all_jobs_scheduled is False
        assert schedule.active_time_intervals == [
            TimeInterval(1, 1)
        ]
        assert len(schedule.job_schedules) == 1

    @pytest.mark.parametrize('scheduler', [LazyActivationSchedulerNLogN, LazyActivationSchedulerT])
    def test_empty(self, scheduler: Type[AbstractLazyActivationScheduler]) -> None:
        job_pool = UnitJobPool()

        schedule = scheduler().process(job_pool, 2)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == []
        assert len(schedule.job_schedules) == 0

    @pytest.mark.repeat(1000)
    @pytest.mark.parametrize('scheduler_b', [LazyActivationSchedulerNLogN, LazyActivationSchedulerT])
    def test_against_brute_force(self, scheduler_b: Type[AbstractLazyActivationScheduler]) -> None:
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

        schedule_a = LazyActivationSchedulerNLogN.process(job_pool, max_concurrency)  # noqa
        schedule_b = LazyActivationSchedulerT.process(job_pool, max_concurrency)  # noqa

        check_equality(schedule_a, schedule_b, job_pool, max_concurrency)
