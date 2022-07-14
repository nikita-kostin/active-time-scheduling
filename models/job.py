# -*- coding: utf-8 -*-
from abc import ABC
from functools import total_ordering
from itertools import count
from typing import List, Optional


@total_ordering
class TimeInterval(object):

    def __init__(self, start: int, end: int) -> None:
        self.start = start
        self.end = end

    def __str__(self) -> str:
        return "TimeInterval(start={0}, end={1})".format(self.start, self.end)

    __repr__ = __str__

    def __eq__(self, other: 'TimeInterval') -> bool:
        return (self.start, self.end) == (other.start, other.end)

    def __lt__(self, other: 'TimeInterval') -> bool:
        return (self.start, self.end) < (other.start, other.end)


class AbstractJob(ABC):
    _id_iter = count()

    def __init__(self, availability_intervals: List[TimeInterval], duration: Optional[int]) -> None:
        self.id = next(self.__class__._id_iter)
        self.availability_intervals = availability_intervals
        self.duration = duration

    def __hash__(self) -> int:
        return self.id


@total_ordering
class JobSI(AbstractJob, ABC):

    def __init__(self, release_time: int, deadline: int, duration: Optional[int]) -> None:
        super(JobSI, self).__init__([TimeInterval(release_time, deadline)], duration)

    def __str__(self) -> str:
        return "JobSI(release_time={0}, deadline={1}, duration={2})".format(
            self.release_time,
            self.deadline,
            self.duration
        )

    __repr__ = __str__

    @property
    def release_time(self) -> int:
        return self.availability_intervals[0].start

    @release_time.setter
    def release_time(self, release_time: int) -> None:
        self.availability_intervals[0].start = release_time

    @property
    def deadline(self) -> int:
        return self.availability_intervals[0].end

    @deadline.setter
    def deadline(self, deadline: int) -> None:
        self.availability_intervals[0].end = deadline

    def __eq__(self, other: 'Job') -> bool:
        return (self.release_time, self.deadline, self.id) == (other.release_time, other.deadline, other.id)

    def __lt__(self, other: 'Job') -> bool:
        return (self.release_time, self.deadline, self.id) < (other.release_time, other.deadline, other.id)

    def __hash__(self) -> int:
        return hash((self.release_time, self.deadline, self.id))


class JobMI(AbstractJob):

    def __init__(self, availability_intervals: List[TimeInterval], duration: int) -> None:
        super(JobMI, self).__init__(availability_intervals, duration)

    def __str__(self) -> str:
        return "JobWithMultipleIntervals(intervals={0}, duration={1})".format(
            self.availability_intervals,
            self.duration
        )

    __repr__ = __str__


class Job(JobSI):

    def __init__(self, release_time: int, deadline: int, duration: int) -> None:
        super(Job, self).__init__(release_time, deadline, duration)

    def __str__(self) -> str:
        return "Job(release_time={0}, deadline={1}, duration={2})".format(
            self.release_time,
            self.deadline,
            self.duration,
        )

    __repr__ = __str__


class UnitJob(JobSI):

    def __init__(self, release_time: int, deadline: int) -> None:
        super(UnitJob, self).__init__(release_time, deadline, 1)

    def __str__(self) -> str:
        return "UnitJob(release_time={0}, deadline={1})".format(self.release_time, self.deadline)

    __repr__ = __str__


class BatchJob(JobSI):

    def __init__(self, release_time: int, deadline: int) -> None:
        super(BatchJob, self).__init__(release_time, deadline, None)

    def __str__(self) -> str:
        return "BatchJob(release_time={0}, deadline={1})".format(self.release_time, self.deadline)

    __repr__ = __str__
