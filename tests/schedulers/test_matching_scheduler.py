# -*- coding: utf-8 -*-
import pytest
from random import randint, random

from models import JobPoolMI, TimeInterval, UnitJobPoolMI
from schedulers import (
    BruteForceScheduler,
    DegreeConstrainedSubgraphScheduler,
    LazyActivationSchedulerT,
    MatchingScheduler,
)
from tests.schedulers.common import check_equality, generate_jobs_uniform_distribution, generate_mi_jobs


class TestMatchingScheduler(object):

    def test_matching_simple_examples(self) -> None:
        job_pool = UnitJobPoolMI()
        job_pool.add_job([(1, 1), (3, 3)])
        job_pool.add_job([(1, 1), (3, 3)])
        job_pool.add_job([(1, 1), (3, 3)])
        job_pool.add_job([(1, 1), (3, 3)])

        schedule = MatchingScheduler().process(job_pool)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == [
            TimeInterval(1, 1),
            TimeInterval(3, 3),
        ]
        assert len(schedule.job_schedules) == 4

        job_pool = UnitJobPoolMI()
        job_pool.add_job([(1, 1)])
        job_pool.add_job([(1, 1)])
        job_pool.add_job([(1, 1)])

        schedule = MatchingScheduler().process(job_pool)

        assert schedule.all_jobs_scheduled is False
        assert schedule.active_time_intervals is None
        assert schedule.job_schedules is None

    def test_udcs_simple_examples(self) -> None:
        job_pool = JobPoolMI()
        job_pool.add_job([(1, 2), (4, 5)], 2)
        job_pool.add_job([(1, 2), (4, 5)], 2)
        job_pool.add_job([(1, 2), (4, 5)], 2)
        job_pool.add_job([(1, 2), (4, 5)], 2)

        schedule = DegreeConstrainedSubgraphScheduler().process(job_pool)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == [
            TimeInterval(1, 2),
            TimeInterval(4, 5),
        ]
        assert len(schedule.job_schedules) == 4

        job_pool = JobPoolMI()
        job_pool.add_job([(1, 2)], 2)
        job_pool.add_job([(1, 2)], 2)
        job_pool.add_job([(1, 2)], 2)

        schedule = DegreeConstrainedSubgraphScheduler().process(job_pool)

        assert schedule.all_jobs_scheduled is False
        assert schedule.active_time_intervals is None
        assert schedule.job_schedules is None

    def test_matching_empty(self) -> None:
        job_pool = UnitJobPoolMI()

        schedule = MatchingScheduler().process(job_pool)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == []
        assert len(schedule.job_schedules) == 0

        job_pool = UnitJobPoolMI()
        job_pool.add_job([])

        schedule = MatchingScheduler().process(job_pool)

        assert schedule.all_jobs_scheduled is False
        assert schedule.active_time_intervals is None
        assert schedule.job_schedules is None

    def test_udcs_empty(self) -> None:
        job_pool = JobPoolMI()

        schedule = DegreeConstrainedSubgraphScheduler().process(job_pool)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == []
        assert len(schedule.job_schedules) == 0

        job_pool = JobPoolMI()
        job_pool.add_job([(1, 2)], 0)
        job_pool.add_job([(4, 5)], 0)

        schedule = DegreeConstrainedSubgraphScheduler().process(job_pool)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == []
        assert len(schedule.job_schedules) == 2

    @pytest.mark.repeat(1000)
    def test_matching_against_brute_force(self) -> None:
        max_length = randint(1, 5)
        max_t = randint(4, 9)
        number_of_jobs = randint(max_t // 2, max_t * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, 1))

        schedule_a = BruteForceScheduler().process(job_pool, 2)
        schedule_b = MatchingScheduler().process(job_pool)  # noqa

        check_equality(schedule_a, schedule_b, job_pool, 2)

    @pytest.mark.repeat(1000)
    def test_udcs_against_brute_force(self) -> None:
        max_length = randint(1, 5)
        max_p = random()
        max_t = randint(4, 9)
        number_of_jobs = randint(max_t // 2, max_t * 2 + 1)

        job_pool = generate_mi_jobs(number_of_jobs, max_t, (0, max_p), max_length)

        schedule_a = BruteForceScheduler().process(job_pool, 2)
        schedule_b = DegreeConstrainedSubgraphScheduler().process(job_pool)

        check_equality(schedule_a, schedule_b, job_pool, 2)

    @pytest.mark.repeat(1000)
    def test_matching_against_lazy_activation(self) -> None:
        max_length = randint(1, 31)
        max_t = randint(50, 101)
        number_of_jobs = randint(max_t // 2, max_t * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, 1))

        schedule_a = LazyActivationSchedulerT().process(job_pool, 2)  # noqa
        schedule_b = MatchingScheduler().process(job_pool)  # noqa

        check_equality(schedule_a, schedule_b, job_pool, 2)
