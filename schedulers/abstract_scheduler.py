# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod

from models import Schedule


class AbstractScheduler(ABC):

    @abstractmethod
    def process(self, *args) -> Schedule:
        pass
