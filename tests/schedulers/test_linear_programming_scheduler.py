# -*- coding: utf-8 -*-
import pytest
from random import randint

from models import JobPool
from schedulers import (
    BruteForceScheduler,
    DegreeConstrainedSubgraphScheduler,
    LazyActivationSchedulerT,
    LinearProgrammingRoundedScheduler,
)
from tests.schedulers.common import check_2_approximation, generate_jobs_uniform_distribution


class TestLinearProgrammingScheduler(object):

    def test_empty(self) -> None:
        job_pool = JobPool()

        schedule = LinearProgrammingRoundedScheduler().process(job_pool, 2)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == []
        assert len(schedule.job_schedules) == 0

        job_pool = JobPool()
        job_pool.add_job(1, 5, 0)
        job_pool.add_job(3, 7, 0)

        schedule = LinearProgrammingRoundedScheduler().process(job_pool, 2)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == []
        assert len(schedule.job_schedules) == 2

    @pytest.mark.repeat(1000)
    def test_against_brute_force(self) -> None:
        max_length = randint(1, 5)
        max_t = randint(4, 9)
        max_concurrency = randint(1, 4)
        number_of_jobs = randint(1, max_t // max_length * max_concurrency + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, max_length))

        schedule_a = BruteForceScheduler().process(job_pool, max_concurrency)
        schedule_b = LinearProgrammingRoundedScheduler().process(job_pool, max_concurrency)

        check_2_approximation(schedule_a, schedule_b, job_pool, max_concurrency)

    @pytest.mark.repeat(1000)
    def test_against_lazy_activation(self) -> None:
        max_length = randint(1, 5)
        max_t = randint(15, 31)
        max_concurrency = randint(1, 4)
        number_of_jobs = randint(1, max_t * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, 1))

        schedule_a = LazyActivationSchedulerT().process(job_pool, max_concurrency)  # noqa
        schedule_b = LinearProgrammingRoundedScheduler().process(job_pool, max_concurrency)

        check_2_approximation(schedule_a, schedule_b, job_pool, max_concurrency)

    @pytest.mark.repeat(1000)
    def test_against_udcs(self) -> None:
        max_length = randint(5, 11)
        max_t = randint(15, 31)
        number_of_jobs = randint(1, max_t // max_length * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, max_length))

        schedule_a = DegreeConstrainedSubgraphScheduler().process(job_pool)
        schedule_b = LinearProgrammingRoundedScheduler().process(job_pool, 2)

        check_2_approximation(schedule_a, schedule_b, job_pool, 2)
