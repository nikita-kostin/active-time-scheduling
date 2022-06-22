# -*- coding: utf-8 -*-
import pytest
from itertools import islice
from random import randint

from models import Job
from schedulers import BruteForceScheduler, FlowScheduler
from tests.generators import JobsGenerator


class TestFlowScheduler(object):

    @pytest.mark.repeat(1000)
    def test_against_brute_force(self) -> None:
        max_duration = randint(1, 4)
        max_t = randint(4, 10)
        max_concurrency = randint(1, 3)
        jobs_count = randint(max(1, max_t // max_duration // 2), max_t // max_duration * max_concurrency)

        jobs = list(islice(JobsGenerator(max_duration, max_t), jobs_count))

        schedule_a = BruteForceScheduler.process(max_concurrency, jobs)
        schedule_b = FlowScheduler.process(max_concurrency, jobs)

        expected = schedule_a.all_jobs_scheduled
        actual = schedule_b.all_jobs_scheduled
        assert actual == expected, str(jobs)

        if schedule_a.all_jobs_scheduled is True:
            expected = sum([ts.end - ts.start + 1 for ts in schedule_a.active_time_slots])
            actual = sum([ts.end - ts.start + 1 for ts in schedule_b.active_time_slots])
            assert actual <= expected * 2, str(jobs)

    def test_tight_example(self) -> None:
        unit_length_jobs = [Job(1, 11, 1) for _ in range(10)]
        rigid_jobs = [Job(2, 11, 10) for _ in range(9)]
        jobs = [Job(1, 21, 10)] + unit_length_jobs + rigid_jobs

        schedule = FlowScheduler.process(10, jobs)
        active_time_slots_count = sum([ts.end - ts.start + 1 for ts in schedule.active_time_slots])

        assert schedule.all_jobs_scheduled is True, jobs
        assert active_time_slots_count == 20, active_time_slots_count
