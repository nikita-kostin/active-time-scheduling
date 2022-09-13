# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List, Tuple

from models import JobMI, Job, TimeInterval


class AbstractJobPool(ABC):
    """
    An abstract entity that represents a job pool.
    """

    def __init__(self) -> None:
        """
        Initialize the class with parameters.
        """
        self.jobs = set()

    @property
    def size(self) -> int:
        return len(self.jobs)

    @abstractmethod
    def add_job(self, *args) -> int:
        """
        An abstract method that defines the interface of adding a job to a job pool.
        :param args: Arguments used to create a job.
        :return: The ID of the job.
        """
        pass


class JobPoolMI(AbstractJobPool):
    """
    Job pool of jobs with multiple execution windows. MI stands for multiple intervals.
    """

    def add_job(self, availability_intervals: List[Tuple[int, int]], duration: int) -> None:
        """
        Add a job to the job pool.
        :param availability_intervals: Execution windows of the job to add.
        :param duration: Duration of the job to add.
        :return: The ID of the job.
        """
        job = JobMI(
            availability_intervals=[TimeInterval(start, end) for start, end in availability_intervals],
            duration=duration,
        )
        self.jobs.add(job)
        return job.id


class JobPool(AbstractJobPool):
    """
    Job pool of jobs with a single execution window.
    """

    def add_job(self, release_time: int, deadline: int, duration: int) -> None:
        """
        Add a job to the job pool.
        :param release_time: Release time of the job to add.
        :param deadline: Deadline of the job to add.
        :param duration: Duration of the job to add.
        :return: The ID of the job.
        """
        job = Job(
            release_time=release_time,
            deadline=deadline,
            duration=duration,
        )
        self.jobs.add(job)
        return job.id


class FixedLengthJobPoolMI(AbstractJobPool):
    """
    A job pool of jobs with fixed lengths and multiple execution windows. Used for batch scheduling.
    """

    def __init__(self, duration: int) -> None:
        """
        Initialize the class with parameters.
        :param duration: Predefined duration of the jobs.
        """
        super(FixedLengthJobPoolMI, self).__init__()
        self.duration = duration

    def add_job(self, availability_intervals: List[Tuple[int, int]]) -> None:
        """
        Add a job to the job pool.
        :param availability_intervals: Execution windows of the job to add.
        :return: The ID of the job.
        """
        job = JobMI(
            availability_intervals=[TimeInterval(start, end) for start, end in availability_intervals],
            duration=self.duration,
        )
        self.jobs.add(job)
        return job.id


class FixedLengthJobPool(AbstractJobPool):
    """
    A job pool of jobs with fixed lengths and a single execution window. Used for batch scheduling.
    """

    def __init__(self, duration: int) -> None:
        """
        Initialize the class with parameters.
        :param duration: Predefined duration of the jobs.
        """
        super(FixedLengthJobPool, self).__init__()
        self.duration = duration

    def add_job(self, release_time: int, deadline: int) -> None:
        """
        Add a job to the job pool.
        :param release_time: Release time of the job to add.
        :param deadline: Deadline of the job to add.
        :return: The ID of the job.
        """
        job = Job(
            release_time=release_time,
            deadline=deadline,
            duration=self.duration,
        )
        self.jobs.add(job)
        return job.id


class UnitJobPoolMI(FixedLengthJobPoolMI):
    """
    Job pool with jobs having unit length and multiple execution windows.
    """

    def __init__(self) -> None:
        """
        Initialize the class with parameters.
        """
        super(UnitJobPoolMI, self).__init__(duration=1)


class UnitJobPool(FixedLengthJobPool):
    """
    Job pool with jobs having unit length and a single execution window.
    """

    def __init__(self) -> None:
        """
        Initialize the class with parameters.
        """
        super(UnitJobPool, self).__init__(duration=1)
