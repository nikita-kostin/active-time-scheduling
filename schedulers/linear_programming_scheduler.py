# -*- coding: utf-8 -*-
import math
from enum import Enum
from networkx import maximum_flow
from scipy.optimize import OptimizeResult, linprog
from typing import Dict, Iterable, List, Tuple

from models import Job, JobScheduleMI, JobWithMultipleIntervals, Schedule, TimeInterval
from schedulers import AbstractScheduler, FlowScheduler
from schedulers.flow_scheduler import FlowMethod


class LinearProgrammingMethod(str, Enum):
    highs_ds = 'highs-ds'
    highs_ipm = 'highs-ipm'
    highs = 'highs'
    interior_point = 'interior-point'
    revised_simplex = 'revised simplex'
    simplex = 'simplex'


class LinearProgrammingArbitraryPreemptionScheduler(AbstractScheduler):

    EPS = 1e-7

    def __init__(self, method: LinearProgrammingMethod = LinearProgrammingMethod.revised_simplex) -> None:
        self.method = method

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

    def _create_job_schedules(
            self,
            jobs: List[JobWithMultipleIntervals],
            js_to_var: Dict[Tuple[int, int], int],
            optimize_result: OptimizeResult,
    ) -> Iterable[JobScheduleMI]:
        for job in jobs:
            job_schedule = JobScheduleMI(job, [])

            for interval in job.intervals:
                for t in range(interval.start, interval.end + 1):
                    if (job.id, t) in js_to_var and optimize_result.x[js_to_var[(job.id, t)]] > self.EPS:
                        job_schedule.execution_intervals.append(
                            TimeInterval(t, t + optimize_result.x[js_to_var[(job.id, t)]])
                        )

            yield job_schedule


    def process(
            self,
            max_concurrency: int,
            jobs: List[JobWithMultipleIntervals],
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

        c, A_ub, b_ub = self._create_linear_program(max_concurrency, jobs, var_counter, t_to_var, js_to_var)

        result = linprog(c, A_ub=A_ub, b_ub=b_ub, method=self.method)

        if result.status != 0:
            return Schedule(False, None, None)

        return Schedule(
            True,
            list(sorted(filter(
                lambda x: x.end - x.start > self.EPS,
                [TimeInterval(t, t + 1 - result.x[t_var]) for t, t_var in t_to_var.items()]
            ))),
            list(self._create_job_schedules(jobs, js_to_var, result)),
        )


class LinearProgrammingRoundedScheduler(LinearProgrammingArbitraryPreemptionScheduler, FlowScheduler):

    def process(
            self,
            max_concurrency: int,
            jobs: List[Job],
            lp_method: LinearProgrammingMethod = LinearProgrammingMethod.interior_point
    ) -> Schedule:
        schedule = super(LinearProgrammingRoundedScheduler, self).process(max_concurrency, jobs)

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

        max_t = max(active_timestamps) + 1
        graph = self._create_initial_graph(max_concurrency, max_t, jobs)

        for t in range(max_t):
            if t in active_timestamps:
                self._open_time_slot(t, jobs, graph)

        _, flow_dict = maximum_flow(graph, 0, 1 + len(jobs) + max_t, flow_func=FlowMethod.preflow_push)

        return Schedule(
            True,
            list(self._merge_active_timestamps(active_timestamps)),
            list(FlowScheduler._create_job_schedules(jobs, flow_dict)),
        )
