# -*- coding: utf-8 -*-
import json
from argparse import ArgumentParser, Namespace
from enum import Enum
from typing import List

from models import Job, Schedule
from schedulers import FlowScheduler, UnitJobsScheduler


class Scheduler(Enum):
    unit_jobs_scheduler = 'UnitJobsScheduler'
    flow_scheduler = 'FlowScheduler'


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument(
        '--input',
        type=str,
        dest='input',
        help='Path to the input file.',
        required=True,
    )
    parser.add_argument(
        '--output',
        type=str,
        dest='output',
        help='Path to the output file.',
        required=True,
    )
    parser.add_argument(
        '--solver',
        type=Scheduler,
        dest='solver',
        help='Solver that should process the input. Available solvers: %s.' % ', '.join([e.value for e in Scheduler]),
        required=True,
    )

    return parser.parse_args()


def process_case(solver: Scheduler, max_concurrency: int, jobs: List[Job]) -> Schedule:
    return {
        Scheduler.flow_scheduler: FlowScheduler,
        Scheduler.unit_jobs_scheduler: UnitJobsScheduler,
    }[solver].process(max_concurrency, jobs)


def main() -> None:
    args = parse_args()

    with open(args.input, 'r') as file:
        input_data = json.load(file)

    max_concurrency = input_data['max_concurrency']

    output_data = {
        'count': input_data['count'],
        'max_concurrency': input_data['max_concurrency'],
        'schedules': [],
    }

    for i, case in enumerate(input_data['cases']):
        jobs = [
            Job(job['release_time'], job['deadline'], job['duration'])
            for job in case['jobs']
        ]

        schedule = process_case(args.solver, max_concurrency, jobs)

        output_data['schedules'].append(
            json.loads(
                json.dumps(schedule, default=lambda obj: obj.__dict__)
            )
        )

        print("Case #%d is processed" % i)

    with open(args.output, 'w') as file:
        file.write(json.dumps(output_data, indent=4))


if __name__ == '__main__':
    main()
