# -*- coding: utf-8 -*-
from typing import List, Optional

from models import JobScheduleSI, TimeInterval


class Schedule(object):

    def __init__(
            self,
            all_jobs_scheduled: bool,
            active_time_slots: Optional[List[TimeInterval]],
            job_schedules: Optional[List[JobScheduleSI]],
    ) -> None:
        self.all_jobs_scheduled = all_jobs_scheduled
        self.active_time_slots = active_time_slots
        self.job_schedules = job_schedules

    def __str__(self) -> str:
        return "Schedule(all_jobs_scheduled={0}, active_time_slots={1}, job_schedules={2})".format(
            self.all_jobs_scheduled,
            self.active_time_slots,
            self.job_schedules,
        )

    __repr__ = __str__

