# -*- coding: utf-8 -*-
from functools import total_ordering
from itertools import count
from typing import List


class TimeInterval(object):

    def __init__(self, start: int, end: int) -> None:
        self.start = start
        self.end = end

    def __str__(self) -> str:
        return "TimeInterval(start={0}, end={1})".format(self.start, self.end)

    __repr__ = __str__


class JobWithMultipleIntervals(object):
    _id_iter = count()

    def __init__(self, intervals: List[TimeInterval], duration: int) -> None:
        self.id = next(JobWithMultipleIntervals._id_iter)
        self.intervals = intervals
        self.duration = duration

    def __str__(self) -> str:
        return "JobWithMultipleIntervals(id={0}, intervals={1}, duration={2})".format(
            self.id,
            self.intervals,
            self.duration
        )


@total_ordering
class Job(JobWithMultipleIntervals):

    def __init__(
            self,
            release_time: int,
            deadline: int,
            duration: int,
    ) -> None:
        super(Job, self).__init__([TimeInterval(release_time, deadline)], duration)

    @property
    def release_time(self) -> int:
        return self.intervals[0].start

    @property
    def deadline(self) -> int:
        return self.intervals[0].end

    def __str__(self) -> str:
        return "Job(id={0}, release_time={1}, deadline={2}, duration={3})".format(
            self.id,
            self.release_time,
            self.deadline,
            self.duration,
        )

    __repr__ = __str__

    def __eq__(self, other: 'Job') -> bool:
        return (self.release_time, self.deadline) == (other.release_time, other.deadline)

    def __lt__(self, other: 'Job') -> bool:
        return (self.release_time, self.deadline) < (other.release_time, other.deadline)

    def __hash__(self) -> int:
        return hash((self.release_time, self.deadline))
