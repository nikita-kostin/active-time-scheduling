# -*- coding: utf-8 -*-
from random import randint
from typing import Iterator

from models import Job


class JobsGenerator(object):

    def __init__(self, max_duration: int, max_time: int) -> None:
        self.max_duration = max_duration
        self.max_time = max_time

    def __iter__(self) -> Iterator[Job]:
        return self

    def __next__(self) -> Job:
        duration = randint(1, self.max_duration)
        release_time = randint(0, self.max_time - duration + 1)
        deadline = randint(release_time + duration - 1, self.max_time)

        return Job(release_time, deadline, duration)
