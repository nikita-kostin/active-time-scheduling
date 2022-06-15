# -*- coding: utf-8 -*-
from scipy.optimize import linprog
from typing import Dict, List, Tuple

from models import JobWithMultipleIntervals, Schedule, TimeInterval
from schedulers import AbstractScheduler


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
    def process(cls, max_concurrency: int, jobs: List[JobWithMultipleIntervals]) -> Schedule:
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

        result = linprog(c, A_ub=A_ub, b_ub=b_ub)

        if result.status != 0:
            return Schedule(False, None, None)

        return Schedule(
            True,
            [TimeInterval(t, t + 1 - result.x[t_var]) for t, t_var in t_to_var.items()],
            None,
        )
