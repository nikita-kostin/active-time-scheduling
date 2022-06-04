# -*- coding: utf-8 -*-
from functools import total_ordering
from models import Job


@total_ordering
class JobSchedule(object):

    def __init__(
            self,
            job: Job,
            execution_start: int,
            execution_end: int,
    ) -> None:
        self.job = job
        self.execution_start = execution_start
        self.execution_end = execution_end

    def __str__(self) -> str:
        return "JobSchedule(job={0}, execution_start={1}, execution_end={2})".format(
            self.job,
            self.execution_start,
            self.execution_end,
        )

    __repr__ = __str__

    def __eq__(self, other: 'JobSchedule') -> bool:
        return (self.execution_start, self.execution_end) == (other.execution_start, other.execution_end)

    def __lt__(self, other: 'JobSchedule') -> bool:
        return (self.execution_start, self.execution_end) < (other.execution_start, other.execution_end)

    def __hash__(self) -> int:
        return hash((self.execution_start, self.execution_end))
