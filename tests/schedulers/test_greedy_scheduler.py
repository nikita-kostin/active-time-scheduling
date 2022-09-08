# -*- coding: utf-8 -*-
import pytest
from numpy.random import randint
from typing import Type

from models import JobPool, TimeInterval
from schedulers import (
    AbstractGreedyScheduler,
    BruteForceScheduler,
    DegreeConstrainedSubgraphScheduler,
    GreedyIntervalsScheduler,
    GreedyScheduler,
    LazyActivationSchedulerT,
)
from tests.schedulers.common import check_equality, check_2_approximation, generate_jobs_uniform_distribution


class TestGreedyScheduler(object):

    @pytest.mark.parametrize('scheduler', [GreedyIntervalsScheduler, GreedyScheduler])
    def test_simple_examples(self, scheduler: Type[AbstractGreedyScheduler]) -> None:
        job_pool = JobPool()
        job_pool.add_job(1, 4, 2)
        job_pool.add_job(3, 8, 2)
        job_pool.add_job(10, 11, 2)

        schedule = scheduler().process(job_pool, 2)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == [
            TimeInterval(3, 4),
            TimeInterval(10, 11),
        ]
        assert len(schedule.job_schedules) == 3

        job_pool = JobPool()
        job_pool.add_job(1, 2, 2)
        job_pool.add_job(1, 2, 2)

        schedule = scheduler().process(job_pool, 1)

        assert schedule.all_jobs_scheduled is False
        assert schedule.active_time_intervals is None
        assert schedule.job_schedules is None

    @pytest.mark.parametrize('scheduler', [GreedyIntervalsScheduler, GreedyScheduler])
    def test_empty(self, scheduler: Type[AbstractGreedyScheduler]) -> None:
        job_pool = JobPool()

        schedule = scheduler().process(job_pool, 2)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == []
        assert len(schedule.job_schedules) == 0

        job_pool = JobPool()
        job_pool.add_job(1, 5, 0)
        job_pool.add_job(3, 7, 0)

        schedule = scheduler().process(job_pool, 2)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == []
        assert len(schedule.job_schedules) == 2

    @pytest.mark.repeat(1000)
    def test_against_each_other(self) -> None:
        max_length = randint(1, 5)
        max_t = randint(15, 31)
        max_concurrency = randint(1, 4)
        number_of_jobs = randint(1, max_t * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, max_length))

        schedule_a = GreedyScheduler().process(job_pool, max_concurrency)
        schedule_b = GreedyIntervalsScheduler().process(job_pool, max_concurrency)

        check_equality(schedule_a, schedule_b, job_pool, max_concurrency)

    @pytest.mark.repeat(1000)
    @pytest.mark.parametrize('scheduler_b', [GreedyIntervalsScheduler, GreedyScheduler])
    def test_against_brute_force(self, scheduler_b: Type[AbstractGreedyScheduler]) -> None:
        max_length = randint(1, 5)
        max_t = randint(4, 9)
        max_concurrency = randint(1, 4)
        number_of_jobs = randint(1, max_t // max_length * max_concurrency + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, max_length))

        schedule_a = BruteForceScheduler().process(job_pool, max_concurrency)
        schedule_b = scheduler_b().process(job_pool, max_concurrency)

        check_2_approximation(schedule_a, schedule_b, job_pool, max_concurrency)

    @pytest.mark.repeat(1000)
    @pytest.mark.parametrize('scheduler_b', [GreedyIntervalsScheduler, GreedyScheduler])
    def test_against_lazy_activation(self, scheduler_b: Type[AbstractGreedyScheduler]) -> None:
        max_length = randint(1, 5)
        max_t = randint(15, 31)
        max_concurrency = randint(1, 4)
        number_of_jobs = randint(1, max_t * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, 1))

        schedule_a = LazyActivationSchedulerT().process(job_pool, max_concurrency)  # noqa
        schedule_b = scheduler_b().process(job_pool, max_concurrency)

        check_2_approximation(schedule_a, schedule_b, job_pool, max_concurrency)

    @pytest.mark.repeat(1000)
    @pytest.mark.parametrize('scheduler_b', [GreedyIntervalsScheduler, GreedyScheduler])
    def test_against_udcs(self, scheduler_b: Type[AbstractGreedyScheduler]) -> None:
        max_length = randint(5, 11)
        max_t = randint(15, 31)
        number_of_jobs = randint(1, max_t // max_length * 2 + 1)

        job_pool = generate_jobs_uniform_distribution(number_of_jobs, max_t, (1, max_length), (1, max_length))

        schedule_a = DegreeConstrainedSubgraphScheduler().process(job_pool)
        schedule_b = scheduler_b().process(job_pool, 2)

        check_2_approximation(schedule_a, schedule_b, job_pool, 2)

    @pytest.mark.parametrize('scheduler', [GreedyIntervalsScheduler, GreedyScheduler])
    def test_tight_example(self, scheduler: Type[AbstractGreedyScheduler]) -> None:
        job_pool = JobPool()

        for _ in range(10):
            job_pool.add_job(1, 11, 1)
        for _ in range(9):
            job_pool.add_job(2, 11, 10)
        job_pool.add_job(1, 21, 10)

        schedule = scheduler().process(job_pool, 10)

        assert schedule.all_jobs_scheduled is True, schedule.all_jobs_scheduled
        assert sum(interval.duration for interval in schedule.active_time_intervals) == 20
        assert len(schedule.job_schedules) == 20
