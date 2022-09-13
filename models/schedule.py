# -*- coding: utf-8 -*-
from typing import List, Optional, Union

from models import AbstractJobSchedule, BatchJobSchedule, TimeInterval


class Schedule(object):
    """
    An object that represents the resulting schedule for the whole problem instance. The schedule comprises 3 parts:
    1. Binary variable all_jobs_scheduled that indicates whether a feasible schedule was found.
    2. Field active_time_intervals containing the list of active time intervals. This field might be None if the
       variable all_jobs_scheduled is set to False.
    3. Field job_schedules containing the list of individual job (batch) schedules. This field is allowed to be None if
       the variable all_jobs_scheduled is set to False.
    """

    def __init__(
            self,
            all_jobs_scheduled: bool,
            active_time_intervals: Optional[List[TimeInterval]],
            job_schedules: Union[Optional[List[AbstractJobSchedule]], Optional[List[BatchJobSchedule]]],
    ) -> None:
        self.all_jobs_scheduled = all_jobs_scheduled
        self.active_time_intervals = active_time_intervals
        self.job_schedules = job_schedules

    def __str__(self) -> str:
        return "Schedule(all_jobs_scheduled={0}, active_time_intervals={1}, job_schedules={2})".format(
            self.all_jobs_scheduled,
            self.active_time_intervals,
            self.job_schedules,
        )

    __repr__ = __str__

