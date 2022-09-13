# Description

This code is developed as a part of B.Sc. thesis in Informatics "Implementation and Analysis of Algorithms
for the Active Time Problem", supervisor: Prof. Dr. Susanne Albers.

The repository comprises various algorithms for solving the Active Time Problem developed to this date. The following
table provides a list of the implemented algorithms available in the package `schedulers` and the corresponding
articles where these algorithms were developed.

| Scheduler                            | Reference                                                                                            |
|--------------------------------------|------------------------------------------------------------------------------------------------------|
| `LazyActivationSchedulerNLogN`       | "A model for minimizing active processor time" (Chang et al., 2012)                                  |
| `LazyActivationSchedulerT`           | "A model for minimizing active processor time" (Chang et al., 2012)                                  |
| `MatchingScheduler`                  | "A model for minimizing active processor time" (Chang et al., 2012)                                  |
| `DegreeConstrainedSubgraphScheduler` | "A model for minimizing active processor time" (Chang et al., 2012)                                  |
| `GreedyScheduler`                    | "Brief announcement: A greedy 2 approximation for the active time problem" (Kumar and Khuller, 2018) |
| `GreedyIntervalsScheduler`           | Was developed over the course of this thesis                                                         |
| `MinFeasScheduler`                   | "LP rounding and combinatorial algorithms for minimizing active and busy time" (Chang et al., 2017)  |
| `GreedyLocalSearchScheduler`         | "Brief announcement: A greedy 2 approximation for the active time problem" (Kumar and Khuller, 2018) |
| `GreedyLowestDensityFirstScheduler`  | Was developed over the course of this thesis                                                         |
| `BruteForceScheduler`                | Used for testing                                                                                     |
| `LinearProgrammingScheduler`         | "A model for minimizing active processor time" (Chang et al., 2012)                                  |
| `LinearProgrammingRoundedScheduler`  | "LP rounding and combinatorial algorithms for minimizing active and busy time" (Chang et al., 2017)  |
| `BatchScheduler`                     | "Optimal batch schedules for parallel machines" (Koehler and Khuller, 2013)                          |

# Usage Examples

To create a job set, the subclasses of `AbstractJobPool` from the package `models` are used. Different subclasses can be
to represent different properties for the jobs in them, for example `FixedLengthJobPool` demands a fixed length from its
jobs. The following example demonstrates the process of creating a job pool and adding a job to it:

```python
from models import JobPool

job_pool = JobPool()
job_pool.add_job(release_time=5, deadline=8, duration=2)
```

To process the job pool, the subclasses of `AbstractScheduler` from the package `schedulers` are used. To perform the
processing, the job pool should be passed into the `process` function. The result of the function is the computed job
schedule, which, if the problem instane is feasible, contains the information regarding the active time slots as well as
individual schedules:

```python
from schedulers import (
    FlowMethod,
    GreedyScheduler,
)

scheduler = GreedyScheduler(FlowMethod.PREFLOW_PUSH)
schedule = scheduler.process(job_pool, max_concurrency=2)
```
