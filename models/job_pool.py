# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List, Tuple

from models import JobMI, JobSI, TimeInterval


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


class JobPoolSI(AbstractJobPool):

    def add_job(self, release_time: int, deadline: int, duration: int) -> None:
        job = JobSI(
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


class FixedLengthJobPoolSI(AbstractJobPool):

    def __init__(self, duration: int) -> None:
        super(FixedLengthJobPoolSI, self).__init__()
        self.duration = duration

    def add_job(self, release_time: int, deadline: int) -> None:
        job = JobSI(
            release_time=release_time,
            deadline=deadline,
            duration=self.duration,
        )
        self.jobs.add(job)
        return job.id


class UnitJobPoolMI(FixedLengthJobPoolMI):

    def __init__(self) -> None:
        super(UnitJobPoolMI, self).__init__(duration=1)


class UnitJobPoolSI(FixedLengthJobPoolSI):

    def __init__(self) -> None:
        super(UnitJobPoolSI, self).__init__(duration=1)
