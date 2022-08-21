# -*- coding: utf-8 -*-

from models import FixedLengthJobPool, TimeInterval
from schedulers import BatchScheduler


class TestBatchScheduler(object):

    def test_simple_examples(self) -> None:
        job_pool = FixedLengthJobPool(2)
        job_pool.add_job(1, 4)
        job_pool.add_job(3, 7)
        job_pool.add_job(6, 8)
        job_pool.add_job(7, 9)

        schedule = BatchScheduler().process(job_pool, 2)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == [
            TimeInterval(3, 4),
            TimeInterval(7, 8),
        ]
        assert len(schedule.job_schedules) == 2

        job_pool = FixedLengthJobPool(2)
        job_pool.add_job(1, 2)
        job_pool.add_job(1, 2)

        schedule = BatchScheduler().process(job_pool, 1)

        assert schedule.all_jobs_scheduled is False
        assert schedule.active_time_intervals is None
        assert schedule.job_schedules is None

    def test_empty(self) -> None:
        job_pool = FixedLengthJobPool(2)

        schedule = BatchScheduler().process(job_pool, 2)

        assert schedule.all_jobs_scheduled is True
        assert schedule.active_time_intervals == []
        assert len(schedule.job_schedules) == 0
