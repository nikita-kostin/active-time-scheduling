# -*- coding: utf-8 -*-
import pytest
from random import randint

from schedulers import (
    BruteForceScheduler,
    MatchingScheduler,
    UnitJobsSchedulerT,
    UpperDegreeConstrainedSubgraphScheduler,
)
from tests.schedulers.common import check_equality, generate_jobs_uniform_distribution


class TestMatchingScheduler(object):

    @pytest.mark.repeat(1000)
    def test_matching_against_brute_force(self) -> None:
        max_length = randint(1, 5)
        max_t = randint(4, 9)
        number_of_jobs = randint(max_t // 2, max_t * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, 1))

        schedule_a = BruteForceScheduler().process(job_pool, 2)
        schedule_b = MatchingScheduler().process(job_pool)

        check_equality(schedule_a, schedule_b, job_pool, 2)

    @pytest.mark.repeat(1000)
    def test_matching_against_lazy_activation(self) -> None:
        max_length = randint(1, 31)
        max_t = randint(50, 101)
        number_of_jobs = randint(max_t // 2, max_t * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, 1))

        schedule_a = UnitJobsSchedulerT().process(job_pool, 2)
        schedule_b = MatchingScheduler().process(job_pool)

        check_equality(schedule_a, schedule_b, job_pool, 2)

    @pytest.mark.repeat(1000)
    def test_udcs_against_brute_force(self) -> None:
        max_length = randint(1, 5)
        max_t = randint(4, 9)
        number_of_jobs = randint(max_t // 2, max_t * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, max_length))

        schedule_a = BruteForceScheduler().process(job_pool, 2)
        schedule_b = UpperDegreeConstrainedSubgraphScheduler().process(job_pool)

        check_equality(schedule_a, schedule_b, job_pool, 2)
