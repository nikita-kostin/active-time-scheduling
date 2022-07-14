# -*- coding: utf-8 -*-
import pytest
from itertools import islice
from random import randint

from models import JobPoolSI
from schedulers import (
    BruteForceScheduler,
    LinearProgrammingArbitraryPreemptionScheduler,
    LinearProgrammingRoundedScheduler,
)
from tests.generators import JobsGenerator


class TestLinearProgrammingScheduler(object):

    @pytest.mark.repeat(1000)
    def test_against_brute_force(self) -> None:
        max_duration = randint(1, 4)
        max_t = randint(4, 8)
        max_concurrency = randint(1, 3)
        jobs_count = randint(max(1, max_t // max_duration // 2), max_t // max_duration * max_concurrency)

        jobs = list(islice(JobsGenerator(max_duration, max_t), jobs_count))
        job_pool = JobPoolSI()
        job_pool.jobs = jobs

        schedule_a = BruteForceScheduler().process(job_pool, max_concurrency)
        schedule_b = LinearProgrammingRoundedScheduler().process(job_pool, max_concurrency)

        expected = schedule_a.all_jobs_scheduled
        actual = schedule_b.all_jobs_scheduled
        assert actual == expected, str(jobs)

        if schedule_a.all_jobs_scheduled is True:
            expected = sum([ts.end - ts.start + 1 for ts in schedule_a.active_time_slots])
            actual = sum([ts.end - ts.start + 1 for ts in schedule_b.active_time_slots])
            assert actual <= expected * 2, str(jobs)

    @pytest.mark.repeat(1000)
    def test_against_non_rounded(self) -> None:
        max_duration = randint(1, 5)
        max_t = randint(5, 10)
        max_concurrency = randint(1, 3)
        jobs_count = randint(max(1, max_t // max_duration // 2), max_t // max_duration * max_concurrency)

        jobs = list(islice(JobsGenerator(max_duration, max_t), jobs_count))
        job_pool = JobPoolSI()
        job_pool.jobs = jobs

        schedule_a = LinearProgrammingArbitraryPreemptionScheduler().process(job_pool, max_concurrency)
        schedule_b = LinearProgrammingRoundedScheduler().process(job_pool, max_concurrency)

        expected = schedule_a.all_jobs_scheduled
        actual = schedule_b.all_jobs_scheduled
        assert actual == expected, str(jobs)

        if schedule_a.all_jobs_scheduled is True:
            expected = sum([ts.end - ts.start for ts in schedule_a.active_time_slots])
            actual = sum([ts.end - ts.start + 1 for ts in schedule_b.active_time_slots])
            assert actual <= expected * 2, str(jobs)
