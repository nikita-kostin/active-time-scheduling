# -*- coding: utf-8 -*-
import pytest
from itertools import islice
from random import randint

from models import Job, JobPoolSI, UnitJobPoolSI
from schedulers import BruteForceScheduler, FlowScheduler, UnitJobsSchedulerT, UpperDegreeConstrainedSubgraphScheduler
from tests.generators import JobsGenerator
from tests.schedulers.common import check_2_approximation


class TestFlowScheduler(object):

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
        schedule_b = FlowScheduler().process(job_pool, max_concurrency)

        check_2_approximation(schedule_a, schedule_b, job_pool, max_concurrency)

    @pytest.mark.repeat(1000)
    def test_against_lazy_activation(self) -> None:
        max_t = randint(15, 30)
        max_concurrency = randint(1, 3)
        jobs_count = randint(max_t // 2, max_t * 2)

        jobs = list(islice(JobsGenerator(1, max_t), jobs_count))
        job_pool = UnitJobPoolSI()
        job_pool.jobs = jobs

        schedule_a = UnitJobsSchedulerT().process(job_pool, max_concurrency)
        schedule_b = FlowScheduler().process(job_pool, max_concurrency)

        check_2_approximation(schedule_a, schedule_b, job_pool, max_concurrency)

    @pytest.mark.repeat(1000)
    def test_against_udcs(self) -> None:
        max_duration = randint(5, 10)
        max_t = randint(15, 30)
        jobs_count = randint(max(1, max_t // max_duration // 2), max_t // max_duration * 2)

        jobs = list(islice(JobsGenerator(1, max_t), jobs_count))
        job_pool = JobPoolSI()
        job_pool.jobs = jobs

        schedule_a = UpperDegreeConstrainedSubgraphScheduler().process(job_pool)
        schedule_b = FlowScheduler().process(job_pool, 2)

        check_2_approximation(schedule_a, schedule_b, job_pool, 2)

    def test_tight_example(self) -> None:
        unit_length_jobs = [Job(1, 11, 1) for _ in range(10)]
        rigid_jobs = [Job(2, 11, 10) for _ in range(9)]
        jobs = [Job(1, 21, 10)] + unit_length_jobs + rigid_jobs
        job_pool = JobPoolSI()
        job_pool.jobs = jobs

        schedule = FlowScheduler().process(job_pool, 10)
        active_time_slots_count = sum([ts.end - ts.start + 1 for ts in schedule.active_time_intervals])

        assert schedule.all_jobs_scheduled is True, jobs
        assert active_time_slots_count == 20, active_time_slots_count
