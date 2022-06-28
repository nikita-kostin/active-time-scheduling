# -*- coding: utf-8 -*-
import pytest
from itertools import islice
from random import randint

from schedulers import BruteForceScheduler, MatchingScheduler, UnitJobsSchedulerT
from tests.generators import JobsGenerator


class TestLinearProgrammingScheduler(object):

    @pytest.mark.repeat(1000)
    def test_against_brute_force(self) -> None:
        max_t = randint(4, 8)
        jobs_count = randint(max_t // 2, max_t * 2)

        jobs = list(islice(JobsGenerator(1, max_t), jobs_count))

        schedule_a = BruteForceScheduler().process(2, jobs)
        schedule_b = MatchingScheduler().process(2, jobs)

        expected = schedule_a.all_jobs_scheduled
        actual = schedule_b.all_jobs_scheduled
        assert actual == expected, str(jobs)

        if schedule_a.all_jobs_scheduled is True:
            expected = sum([ts.end - ts.start + 1 for ts in schedule_a.active_time_slots])
            actual = sum([ts.end - ts.start + 1 for ts in schedule_b.active_time_slots])
            assert actual == expected, str(jobs)

    @pytest.mark.repeat(1000)
    def test_against_lazy_activation(self) -> None:
        max_t = randint(50, 100)
        jobs_count = randint(max_t // 2, max_t * 2)

        jobs = list(islice(JobsGenerator(1, max_t), jobs_count))

        schedule_a = UnitJobsSchedulerT().process(2, jobs)
        schedule_b = MatchingScheduler().process(2, jobs)

        expected = schedule_a.all_jobs_scheduled
        actual = schedule_b.all_jobs_scheduled
        assert actual == expected, str(jobs)

        if schedule_a.all_jobs_scheduled is True:
            expected = sum([ts.end - ts.start + 1 for ts in schedule_a.active_time_slots])
            actual = sum([ts.end - ts.start + 1 for ts in schedule_b.active_time_slots])
            assert actual == expected, str(jobs)
