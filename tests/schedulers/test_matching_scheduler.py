# -*- coding: utf-8 -*-
import pytest
from itertools import islice
from random import randint

from models import JobPoolMI, UnitJobPoolMI
from schedulers import (
    BruteForceScheduler,
    MatchingScheduler,
    UnitJobsSchedulerT,
    UpperDegreeConstrainedSubgraphScheduler,
)
from tests.generators import JobsGenerator
from tests.schedulers.common import check_equality


class TestMatchingScheduler(object):

    @pytest.mark.repeat(1000)
    def test_matching_against_brute_force(self) -> None:
        max_t = randint(4, 8)
        jobs_count = randint(max_t // 2, max_t * 2)

        jobs = list(islice(JobsGenerator(1, max_t), jobs_count))
        job_pool = UnitJobPoolMI()
        job_pool.jobs = jobs

        schedule_a = BruteForceScheduler().process(job_pool, 2)
        schedule_b = MatchingScheduler().process(job_pool)

        check_equality(schedule_a, schedule_b, job_pool, 2)

    @pytest.mark.repeat(1000)
    def test_matching_against_lazy_activation(self) -> None:
        max_t = randint(50, 100)
        jobs_count = randint(max_t // 2, max_t * 2)

        jobs = list(islice(JobsGenerator(1, max_t), jobs_count))
        job_pool = UnitJobPoolMI()
        job_pool.jobs = jobs

        schedule_a = UnitJobsSchedulerT().process(job_pool, 2)
        schedule_b = MatchingScheduler().process(job_pool)

        check_equality(schedule_a, schedule_b, job_pool, 2)

    @pytest.mark.repeat(1000)
    def test_udcs_against_brute_force(self) -> None:
        max_t = randint(4, 8)
        jobs_count = randint(max_t // 2, max_t * 2)

        jobs = list(islice(JobsGenerator(1, max_t), jobs_count))
        job_pool = JobPoolMI()
        job_pool.jobs = jobs

        schedule_a = BruteForceScheduler().process(job_pool, 2)
        schedule_b = UpperDegreeConstrainedSubgraphScheduler().process(job_pool)

        check_equality(schedule_a, schedule_b, job_pool, 2)
