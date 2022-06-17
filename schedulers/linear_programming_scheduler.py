# -*- coding: utf-8 -*-
import math
from enum import Enum
from scipy.optimize import linprog
from typing import Dict, List, Tuple

from models import JobWithMultipleIntervals, Schedule, TimeInterval
from schedulers import AbstractScheduler


class LinearProgrammingMethod(Enum):
    highs_ds = 'highs-ds'
    highs_ipm = 'highs-ipm'
    highs = 'highs'
    interior_point = 'interior-point'
    revised_simplex = 'revised simplex'
    simplex = 'simplex'


class LinearProgrammingArbitraryPreemptionScheduler(AbstractScheduler):

    @staticmethod
    def _create_linear_program(
            max_concurrency: int,
            jobs: List[JobWithMultipleIntervals],
            var_counter: int,
            t_to_var: Dict[int, int],
            js_to_var: Dict[Tuple[int, int], int],
    ) -> Tuple[List[int], List[List[int]], List[int]]:
        c = [0] * var_counter
        for t_var in t_to_var.values():
            c[t_var] = -1

        A_ub = []
        b_ub = []

        for job in jobs:
            A_ub.append([0] * var_counter)
            b_ub.append(-job.duration)

            for js, js_var in js_to_var.items():
                if job.id == js[0]:
                    A_ub[-1][js_var] = -1

        for t, t_var in t_to_var.items():
            A_ub.append([0] * var_counter)
            b_ub.append(max_concurrency)

            A_ub[-1][t_var] = max_concurrency

            for js, js_var in js_to_var.items():
                if t == js[1]:
                    A_ub[-1][js_var] = 1

        for js, js_var in js_to_var.items():
            A_ub.append([0] * var_counter)
            b_ub.append(1)

            A_ub[-1][js_var] = 1

            _, t = js

            A_ub[-1][t_to_var[t]] = 1

        return c, A_ub, b_ub

    @classmethod
    def process(
            cls,
            max_concurrency: int,
            jobs: List[JobWithMultipleIntervals],
            method: LinearProgrammingMethod = LinearProgrammingMethod.interior_point
    ) -> Schedule:
        var_counter = 0

        t_to_var = {}
        js_to_var = {}

        for job in jobs:
            for interval in job.intervals:
                for t in range(interval.start, interval.end + 1):
                    if t not in t_to_var:
                        t_to_var[t] = var_counter
                        var_counter += 1
                    js_to_var[(job.id, t)] = var_counter
                    var_counter += 1

        c, A_ub, b_ub = cls._create_linear_program(max_concurrency, jobs, var_counter, t_to_var, js_to_var)

        result = linprog(c, A_ub=A_ub, b_ub=b_ub, method=method.value)

        if result.status != 0:
            return Schedule(False, None, None)

        return Schedule(
            True,
            [TimeInterval(t, t + 1 - result.x[t_var]) for t, t_var in t_to_var.items()],
            None,
        )


class LinearProgrammingRoundedScheduler(LinearProgrammingArbitraryPreemptionScheduler):

    @classmethod
    def process(
            cls,
            max_concurrency: int,
            jobs: List[JobWithMultipleIntervals],
            method: LinearProgrammingMethod = LinearProgrammingMethod.interior_point
    ) -> Schedule:
        schedule = super().process(max_concurrency, jobs, method)

        if schedule.all_jobs_scheduled is False:
            return Schedule(False, None, None)

        deadlines = set([max([interval.end for interval in job.intervals]) + 1 for job in jobs])

        i = 0
        active_timestamps = set()

        for deadline in sorted(deadlines):
            duration_sum = 0

            while i < len(schedule.active_time_slots) and schedule.active_time_slots[i].end <= deadline:
                duration_sum += (schedule.active_time_slots[i].end - schedule.active_time_slots[i].start)
                i += 1

            for t in range(deadline - 1, deadline - 1 - math.ceil(duration_sum), -1):
                active_timestamps.add(t)

        return Schedule(
            True,
            list(cls._merge_active_timestamps(active_timestamps)),
            None,
        )
