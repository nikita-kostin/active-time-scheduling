# -*- coding: utf-8 -*-
import math
import warnings
from enum import Enum
from networkx import maximum_flow
from scipy.linalg import LinAlgWarning
from scipy.optimize import OptimizeResult, OptimizeWarning, linprog
from typing import Dict, Iterable, List, Tuple, Union

from models import JobMI, JobPool, JobPoolMI, JobScheduleMI, Schedule, TimeInterval
from schedulers import AbstractScheduler, GreedyScheduler
from schedulers.greedy_scheduler import FlowMethod


class LinearProgrammingMethod(str, Enum):
    HIGHS_DS = 'highs-ds'
    HIGHS_IPM = 'highs-ipm'
    HIGHS = 'highs'
    INTERIOR_POINT = 'interior-point'
    REVISED_SIMPLEX = 'revised simplex'
    SIMPLEX = 'simplex'


class LinearProgrammingScheduler(AbstractScheduler):

    EPS = 1e-7

    def __init__(self, lp_method: LinearProgrammingMethod = LinearProgrammingMethod.HIGHS) -> None:
        self.lp_method = lp_method

    @staticmethod
    def _create_linear_program(
            max_concurrency: int,
            jobs: List[JobMI],
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
            jobs: List[JobMI],
            js_to_var: Dict[Tuple[int, int], int],
            optimize_result: OptimizeResult,
    ) -> Iterable[JobScheduleMI]:
        for job in jobs:
            job_schedule = JobScheduleMI(job, [])

            for interval in job.availability_intervals:
                for t in range(interval.start, interval.end + 1):
                    if (job.id, t) in js_to_var and optimize_result.x[js_to_var[(job.id, t)]] > self.EPS:
                        job_schedule.execution_intervals.append(
                            TimeInterval(t, t + optimize_result.x[js_to_var[(job.id, t)]])
                        )

            yield job_schedule

    def process(self, job_pool: Union[JobPoolMI, JobPool], max_concurrency: int) -> Schedule:
        if job_pool.size == 0:
            return Schedule(True, [], [])

        # Disable precision warnings from old SciPy solvers
        warnings.simplefilter('ignore', LinAlgWarning)
        warnings.simplefilter('ignore', OptimizeWarning)

        var_counter = 0

        t_to_var = {}
        js_to_var = {}

        for job in job_pool.jobs:
            for interval in job.availability_intervals:
                for t in range(interval.start, interval.end + 1):
                    if t not in t_to_var:
                        t_to_var[t] = var_counter
                        var_counter += 1
                    js_to_var[(job.id, t)] = var_counter
                    var_counter += 1

        c, A_ub, b_ub = self._create_linear_program(max_concurrency, job_pool.jobs, var_counter, t_to_var, js_to_var)

        result = linprog(c, A_ub=A_ub, b_ub=b_ub, method=self.lp_method)

        if result.status != 0:
            return Schedule(False, None, None)

        return Schedule(
            True,
            list(sorted(filter(
                lambda x: x.end - x.start > self.EPS,
                [TimeInterval(t, t + 1 - result.x[t_var]) for t, t_var in t_to_var.items()]
            ))),
            list(self._create_job_schedules(job_pool.jobs, js_to_var, result)),
        )


class LinearProgrammingRoundedScheduler(GreedyScheduler):

    def __init__(
            self,
            lp_method: LinearProgrammingMethod = LinearProgrammingMethod.HIGHS,
            flow_method: FlowMethod = FlowMethod.PREFLOW_PUSH,
    ) -> None:
        super(LinearProgrammingRoundedScheduler, self).__init__(flow_method)
        self.linear_programming_scheduler = LinearProgrammingScheduler(lp_method)

    def process(self, job_pool: JobPool, max_concurrency: int) -> Schedule:
        schedule = self.linear_programming_scheduler.process(job_pool, max_concurrency)

        if schedule.all_jobs_scheduled is False:
            return Schedule(False, None, None)

        deadlines = set([max([interval.end for interval in job.availability_intervals]) + 1 for job in job_pool.jobs])

        i = 0
        active_timestamps = set()

        for deadline in sorted(deadlines):
            duration_sum = 0

            while i < len(schedule.active_time_intervals) and schedule.active_time_intervals[i].end <= deadline:
                duration_sum += (schedule.active_time_intervals[i].end - schedule.active_time_intervals[i].start)
                i += 1

            for t in range(deadline - 1, deadline - 1 - math.ceil(duration_sum), -1):
                active_timestamps.add(t)

        if len(active_timestamps) == 0:
            return Schedule(True, [], [JobScheduleMI(job, []) for job in job_pool.jobs])

        max_t = max(active_timestamps) + 1
        graph = self._create_initial_graph(max_concurrency, max_t, job_pool.jobs)

        for t in range(max_t):
            if t in active_timestamps:
                self._open_time_slot(t, job_pool.jobs, graph)

        _, flow_dict = maximum_flow(graph, 0, 1 + len(job_pool.jobs) + max_t, flow_func=self.flow_func)  # noqa

        return Schedule(
            True,
            TimeInterval.merge_timestamps(active_timestamps),
            list(GreedyScheduler._create_job_schedules(job_pool.jobs, flow_dict)),
        )
