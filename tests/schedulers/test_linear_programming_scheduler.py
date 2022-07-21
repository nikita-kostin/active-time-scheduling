# -*- coding: utf-8 -*-
import pytest
from random import randint

from schedulers import (
    BruteForceScheduler,
    LinearProgrammingRoundedScheduler,
    UnitJobsSchedulerT,
    UpperDegreeConstrainedSubgraphScheduler,
)
from tests.schedulers.common import check_2_approximation, generate_jobs_uniform_distribution


class TestLinearProgrammingScheduler(object):

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

        schedule_a = UnitJobsSchedulerT().process(job_pool, max_concurrency)
        schedule_b = LinearProgrammingRoundedScheduler().process(job_pool, max_concurrency)

        check_2_approximation(schedule_a, schedule_b, job_pool, max_concurrency)

    @pytest.mark.repeat(1000)
    def test_against_udcs(self) -> None:
        max_length = randint(5, 11)
        max_t = randint(15, 31)
        number_of_jobs = randint(1, max_t // max_length * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, max_length))

        schedule_a = UpperDegreeConstrainedSubgraphScheduler().process(job_pool)
        schedule_b = LinearProgrammingRoundedScheduler().process(job_pool, 2)

        check_2_approximation(schedule_a, schedule_b, job_pool, 2)
