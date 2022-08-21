# -*- coding: utf-8 -*-
import pytest
from numpy.random import randint
from typing import Type

from models import JobPool
from schedulers import (
    AbstractFlowScheduler,
    BruteForceScheduler,
    FlowIntervalScheduler,
    FlowScheduler,
    UnitJobsSchedulerT,
    UpperDegreeConstrainedSubgraphScheduler,
)
from tests.schedulers.common import check_equality, check_2_approximation, generate_jobs_uniform_distribution


class TestFlowScheduler(object):

    @pytest.mark.repeat(1000)
    def test_interval_scheduler(self) -> None:
        max_length = randint(1, 5)
        max_t = randint(15, 31)
        max_concurrency = randint(1, 4)
        number_of_jobs = randint(1, max_t * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, max_length))

        schedule_a = FlowScheduler().process(job_pool, max_concurrency)
        schedule_b = FlowIntervalScheduler().process(job_pool, max_concurrency)

        check_equality(schedule_a, schedule_b, job_pool, max_concurrency)

    @pytest.mark.repeat(1000)
    @pytest.mark.parametrize('scheduler_b', [FlowIntervalScheduler, FlowScheduler])
    def test_against_brute_force(self, scheduler_b: Type[AbstractFlowScheduler]) -> None:
        max_length = randint(1, 5)
        max_t = randint(4, 9)
        max_concurrency = randint(1, 4)
        number_of_jobs = randint(1, max_t // max_length * max_concurrency + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, max_length))

        schedule_a = BruteForceScheduler().process(job_pool, max_concurrency)
        schedule_b = scheduler_b().process(job_pool, max_concurrency)

        check_2_approximation(schedule_a, schedule_b, job_pool, max_concurrency)

    @pytest.mark.repeat(1000)
    @pytest.mark.parametrize('scheduler_b', [FlowIntervalScheduler, FlowScheduler])
    def test_against_lazy_activation(self, scheduler_b: Type[AbstractFlowScheduler]) -> None:
        max_length = randint(1, 5)
        max_t = randint(15, 31)
        max_concurrency = randint(1, 4)
        number_of_jobs = randint(1, max_t * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, 1))

        schedule_a = UnitJobsSchedulerT().process(job_pool, max_concurrency)  # noqa
        schedule_b = scheduler_b().process(job_pool, max_concurrency)

        check_2_approximation(schedule_a, schedule_b, job_pool, max_concurrency)

    @pytest.mark.repeat(1000)
    @pytest.mark.parametrize('scheduler_b', [FlowIntervalScheduler, FlowScheduler])
    def test_against_udcs(self, scheduler_b: Type[AbstractFlowScheduler]) -> None:
        max_length = randint(5, 11)
        max_t = randint(15, 31)
        number_of_jobs = randint(1, max_t // max_length * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, max_length))

        schedule_a = UpperDegreeConstrainedSubgraphScheduler().process(job_pool)
        schedule_b = scheduler_b().process(job_pool, 2)

        check_2_approximation(schedule_a, schedule_b, job_pool, 2)

    @pytest.mark.parametrize('scheduler', [FlowIntervalScheduler, FlowScheduler])
    def test_tight_example(self, scheduler: Type[AbstractFlowScheduler]) -> None:
        job_pool = JobPool()

        for _ in range(10):
            job_pool.add_job(1, 11, 1)
        for _ in range(9):
            job_pool.add_job(2, 11, 10)
        job_pool.add_job(1, 21, 10)

        schedule = scheduler().process(job_pool, 10)
        active_time_slots_count = sum([ts.end - ts.start + 1 for ts in schedule.active_time_intervals])

        assert schedule.all_jobs_scheduled is True, schedule.all_jobs_scheduled
        assert active_time_slots_count == 20, active_time_slots_count
