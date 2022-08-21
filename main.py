# -*- coding: utf-8 -*-
import json
import os
from argparse import ArgumentParser, Namespace
from enum import Enum
from typing import List

from create_image import create_image_from_schedule
from models import Job, Schedule
from schedulers import (
    BruteForceScheduler,
    GreedyScheduler,
    LinearProgrammingScheduler,
    MatchingScheduler,
    LazyActivationScheduler,
)


class Scheduler(Enum):
    brute_force_scheduler = 'BruteForceScheduler'
    flow_scheduler = 'FlowScheduler'
    linear_programming_arbitrary_preemption_scheduler = 'LinearProgrammingArbitraryPreemptionScheduler'
    matching_scheduler = 'MatchingScheduler'
    unit_jobs_scheduler = 'UnitJobsScheduler'


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument(
        '--input',
        type=str,
        dest='input',
        help='Path to the input file.',
        required=False,
        default='input.txt',
    )
    parser.add_argument(
        '--output',
        type=str,
        dest='output',
        help='Path to the output file.',
        required=False,
        default='output.txt',
    )
    parser.add_argument(
        '--solver',
        type=Scheduler,
        dest='solver',
        help='Solver that should process the input. Available solvers: %s.' % ', '.join([e.value for e in Scheduler]),
        required=True,
    )
    parser.add_argument(
        '--create-images',
        type=bool,
        dest='create_images',
        help='Create images with visualised output schedules.',
        required=False,
        default=False,
    )
    parser.add_argument(
        '--output-images-folder',
        type=str,
        dest='output_images_folder',
        help='Path to the output images folder',
        required=False,
        default='output-images',
    )

    return parser.parse_args()


def process_case(solver: Scheduler, max_concurrency: int, jobs: List[Job]) -> Schedule:
    return {
        Scheduler.brute_force_scheduler: BruteForceScheduler,
        Scheduler.flow_scheduler: GreedyScheduler,
        Scheduler.linear_programming_arbitrary_preemption_scheduler: LinearProgrammingScheduler,
        Scheduler.matching_scheduler: MatchingScheduler,
        Scheduler.unit_jobs_scheduler: LazyActivationScheduler,
    }[solver]().process(max_concurrency, jobs)


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

        if args.create_images is True:
            if os.path.isdir(args.output_images_folder) is False:
                os.mkdir(args.output_images_folder)

            create_image_from_schedule(
                max_concurrency,
                jobs,
                schedule,
                "%s/case_%d.png" % (args.output_images_folder, i)
            )

        print("Case #%d is processed" % i)

    with open(args.output, 'w') as file:
        file.write(json.dumps(output_data, indent=4))


if __name__ == '__main__':
    main()
