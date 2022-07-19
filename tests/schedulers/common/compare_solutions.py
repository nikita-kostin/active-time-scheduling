# -*- coding: utf-8 -*-
from typing import List

from models import AbstractJobPool, Schedule, TimeInterval


def _check_time_intervals(time_intervals: List[TimeInterval], job_pool: AbstractJobPool, max_concurrency: int) -> None:
    for i, time_interval in enumerate(time_intervals):
        assert time_interval.duration != 0, "%s is empty for %s, %d" % (time_interval, job_pool.jobs, max_concurrency)

        msg = "incorrect boundaries for %s for %s, %d" % (time_interval, job_pool.jobs, max_concurrency)
        assert time_interval.start <= time_interval.end, msg

        for j in range(i):
            msg = "%s intersects with %s for %s, %d" % (time_intervals[j], time_interval, job_pool.jobs, max_concurrency)
            assert time_intervals[j].end < time_interval.start, msg


def _check_feasibility(schedule: Schedule, job_pool: AbstractJobPool, max_concurrency: int) -> None:
    if schedule.all_jobs_scheduled is False:
        return

    msg = "'active_time_slots' is not set for %s, %s, %d" % (schedule, job_pool.jobs, max_concurrency)
    assert schedule.active_time_intervals is not None, msg

    msg = "'job_schedules' is not set for %s, %s, %d" % (schedule, job_pool.jobs, max_concurrency)
    assert schedule.job_schedules is not None, msg

    _check_time_intervals(schedule.active_time_intervals, job_pool, max_concurrency)

    active_timestamps = set()

    for time_interval in schedule.active_time_intervals:
        for t in time_interval:
            active_timestamps.add(t)

    jobs_cnt = {}

    for js in schedule.job_schedules:
        _check_time_intervals(js.execution_intervals, job_pool, max_concurrency)

        timestamps_cnt = sum(time_interval.duration for time_interval in js.execution_intervals)
        msg = "%s does not match the duration of the job for %s, %d" % (js, job_pool.jobs, max_concurrency)
        assert timestamps_cnt == js.job.duration, msg

        for time_interval in js.execution_intervals:
            for t in time_interval:
                jobs_cnt.setdefault(t, 0)
                jobs_cnt[t] += 1

    for t in jobs_cnt.keys():
        msg = "%d > %d at %d for %s, %s, %d" % (
            jobs_cnt[t], max_concurrency, t, schedule.job_schedules, job_pool.jobs, max_concurrency
        )
        assert jobs_cnt[t] <= max_concurrency, msg


def _check_approximation(
        schedule_a: Schedule,
        schedule_b: Schedule,
        job_pool: AbstractJobPool,
        max_concurrency: int,
        approximation_constant: int,
) -> None:
    msg = "%s != %s for %s, %d" % (
        schedule_a.all_jobs_scheduled, schedule_b.all_jobs_scheduled, job_pool.jobs, max_concurrency
    )
    assert schedule_a.all_jobs_scheduled == schedule_b.all_jobs_scheduled, msg

    if schedule_a.all_jobs_scheduled is True:
        _check_feasibility(schedule_a, job_pool, max_concurrency)
        _check_feasibility(schedule_b, job_pool, max_concurrency)

        duration_sum_a = sum(js.duration for js in schedule_a.job_schedules)
        duration_sum_b = sum(js.duration for js in schedule_b.job_schedules)

        assert 1 / approximation_constant <= duration_sum_a / duration_sum_b <= approximation_constant


def check_equality(
        schedule_a: Schedule,
        schedule_b: Schedule,
        job_pool: AbstractJobPool,
        max_concurrency: int,
) -> None:
    _check_approximation(schedule_a, schedule_b, job_pool, max_concurrency, 1)


def check_2_approximation(
        schedule_a: Schedule,
        schedule_b: Schedule,
        job_pool: AbstractJobPool,
        max_concurrency: int,
) -> None:
    _check_approximation(schedule_a, schedule_b, job_pool, max_concurrency, 2)
