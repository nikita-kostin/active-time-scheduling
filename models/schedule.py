# -*- coding: utf-8 -*-
from typing import List, Optional

from models import JobSchedule


class ActiveTimeSlot(object):

    def __init__(self, start: int, end: int) -> None:
        self.start = start
        self.end = end

    def __str__(self) -> str:
        return "ActiveTimeSlot(start={0}, end={1})".format(self.start, self.end)

    __repr__ = __str__


class Schedule(object):

    def __init__(
            self,
            all_jobs_scheduled: bool,
            active_time_slots: Optional[List[ActiveTimeSlot]],
            job_schedules: Optional[List[JobSchedule]],
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

