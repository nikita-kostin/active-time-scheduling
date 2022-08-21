# -*- coding: utf-8 -*-
from abc import ABC

from models import AbstractJobPool, Schedule


class AbstractScheduler(ABC):

    def process(self, job_pool: AbstractJobPool, **kwargs) -> Schedule:
        pass
