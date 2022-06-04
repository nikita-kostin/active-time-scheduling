# -*- coding: utf-8 -*-
from functools import total_ordering
from itertools import count


@total_ordering
class Job(object):
    _id_iter = count()

    def __init__(
            self,
            release_time: int,
            deadline: int,
            duration: int,
    ) -> None:
        self.id = next(Job._id_iter)
        self.release_time = release_time
        self.deadline = deadline
        self.duration = duration

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
