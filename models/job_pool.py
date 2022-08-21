# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List, Tuple

from models import JobMI, Job, TimeInterval


class AbstractJobPool(ABC):

    def __init__(self) -> None:
        self.jobs = set()

    @property
    def size(self) -> int:
        return len(self.jobs)

    @abstractmethod
    def add_job(self, *args) -> int:
        pass


class JobPoolMI(AbstractJobPool):

    def add_job(self, availability_intervals: List[Tuple[int, int]], duration: int) -> None:
        job = JobMI(
            availability_intervals=[TimeInterval(start, end) for start, end in availability_intervals],
            duration=duration,
        )
        self.jobs.add(job)
        return job.id


class JobPool(AbstractJobPool):

    def add_job(self, release_time: int, deadline: int, duration: int) -> None:
        job = Job(
            release_time=release_time,
            deadline=deadline,
            duration=duration,
        )
        self.jobs.add(job)
        return job.id


class FixedLengthJobPoolMI(AbstractJobPool):

    def __init__(self, duration: int) -> None:
        super(FixedLengthJobPoolMI, self).__init__()
        self.duration = duration

    def add_job(self, availability_intervals: List[Tuple[int, int]]) -> None:
        job = JobMI(
            availability_intervals=[TimeInterval(start, end) for start, end in availability_intervals],
            duration=self.duration,
        )
        self.jobs.add(job)
        return job.id


class FixedLengthJobPool(AbstractJobPool):

    def __init__(self, duration: int) -> None:
        super(FixedLengthJobPool, self).__init__()
        self.duration = duration

    def add_job(self, release_time: int, deadline: int) -> None:
        job = Job(
            release_time=release_time,
            deadline=deadline,
            duration=self.duration,
        )
        self.jobs.add(job)
        return job.id


class UnitJobPoolMI(FixedLengthJobPoolMI):

    def __init__(self) -> None:
        super(UnitJobPoolMI, self).__init__(duration=1)


class UnitJobPool(FixedLengthJobPool):

    def __init__(self) -> None:
        super(UnitJobPool, self).__init__(duration=1)
