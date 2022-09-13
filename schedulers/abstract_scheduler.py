# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod

from models import Schedule


class AbstractScheduler(ABC):
    """
    An abstract class that defines the interface for all the other schedules.
    """

    @abstractmethod
    def process(self, *args) -> Schedule:
        """
        Abstract process function to be implemented in the subclasses.
        :param args: Scheduling parameters accepted by the function.
        :return: Processed schedule.
        """
        pass
