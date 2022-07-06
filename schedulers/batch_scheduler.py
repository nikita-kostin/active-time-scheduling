# -*- coding: utf-8 -*-
from numpy import argmax
from typing import Iterable, List, Optional

from models import Batch, BatchJob, Schedule
from schedulers import AbstractScheduler


class BatchScheduler(AbstractScheduler):

    @staticmethod
    def _construct_initial_schedule(
            jobs: List[BatchJob],
            batch_duration: int,
            max_concurrency: int,
    ) -> Iterable[Batch]:
        jobs = sorted(jobs)
        used = set()

        while len(used) != len(jobs):
            batch = None

            for job in reversed(jobs):
                if job in used:
                    continue

                if batch is None:
                    batch = Batch(set(), job.release_time, job.release_time + batch_duration - 1)

                if job.release_time <= batch.execution_start and batch.execution_end <= job.deadline:
                    batch.jobs.add(job)
                    used.add(job)

                if len(batch.jobs) == max_concurrency:
                    break

            yield batch

    @staticmethod
    def _push_forward(i: int, batches: List[Batch], batch_duration: int, number_of_machines: int) -> None:
        updated_execution_start = batches[i].execution_start

        for job in batches[i].jobs:
            updated_execution_start = max(updated_execution_start, job.release_time)

        if i >= 1:
            updated_execution_start = max(updated_execution_start, batches[i - 1].execution_start)
        if i >= number_of_machines:
            updated_execution_start = max(
                updated_execution_start,
                batches[i - number_of_machines].execution_start + batch_duration,
            )

        batches[i].execution_start = updated_execution_start
        batches[i].execution_end = updated_execution_start + batch_duration - 1

    @staticmethod
    def _move_back(i: int, batches: List[Batch], job: BatchJob, max_concurrency: int) -> Optional[int]:
        batches[i].jobs.remove(job)

        preceding_deadline_available_jobs = [
            (job, j) for j in range(i) for job in batches[j].jobs if batches[i].execution_end <= job.deadline
        ]

        if preceding_deadline_available_jobs:
            job_to_bring_forward, j = max(preceding_deadline_available_jobs)
            batches[j].jobs.remove(job_to_bring_forward)
            batches[i].jobs.add(job_to_bring_forward)

        for j in range(i - 1, -1, -1):
            if len(batches[j].jobs) != max_concurrency:
                batches[j].jobs.add(job)
                return j

            job_with_max_release_time = list(batches[j].jobs)[
                argmax([job.release_time for job in list(batches[j].jobs)])
            ]

            if job_with_max_release_time.release_time <= job.release_time:
                batches[j].jobs.remove(job_with_max_release_time)
                batches[j].jobs.add(job)
                job = job_with_max_release_time

        return None

    @staticmethod
    def _compute_for_multiple_machines(
            jobs: List[BatchJob],
            max_concurrency: int,
            batch_duration: int,
            number_of_machines: int,
    ) -> Optional[List[Batch]]:
        if min([job.deadline - job.release_time + 1 for job in jobs]) < batch_duration:
            return None

        batches = sorted(BatchScheduler._construct_initial_schedule(jobs, batch_duration, max_concurrency))

        i = 0

        while True:
            if i == len(batches):
                break

            BatchScheduler._push_forward(i, batches, batch_duration, number_of_machines)

            jobs_to_move_back = [
                job for job in batches[i].jobs if batches[i].execution_start + batch_duration - 1 > job.deadline
            ]

            if not jobs_to_move_back:
                i += 1
                continue

            next_i = BatchScheduler._move_back(i, batches, jobs_to_move_back[0], max_concurrency)

            if next_i is None:
                return None
            i = next_i

        return [batch for batch in batches if len(batch.jobs) != 0]

    @classmethod
    def process(cls, max_concurrency: int, jobs: List[BatchJob], batch_duration: int) -> Schedule:
        batches = cls._compute_for_multiple_machines(jobs, max_concurrency, batch_duration, 1)

        if batches is None:
            return Schedule(False, None, None)

        active_time_slots = [(batch.execution_start, batch.execution_end) for batch in batches]

        return Schedule(
            True,
            list(cls._merge_active_time_slots(active_time_slots)),
            batches,
        )
