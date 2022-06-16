# -*- coding: utf-8 -*-
import json
from argparse import ArgumentParser, Namespace
from random import randint


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument(
        '--output',
        type=str,
        dest='output',
        help='Path to the output file.',
        required=True,
    )
    parser.add_argument(
        '--count',
        type=int,
        dest='count',
        help='Number of cases to generate.',
        required=True,
    )
    parser.add_argument(
        '--max-jobs',
        type=int,
        dest='max_jobs',
        help='Maximum number of jobs allowed.'
    )
    parser.add_argument(
        '--max-concurrency',
        type=int,
        dest='max_concurrency',
        help='Upper limit for concurrent jobs.',
        required=True,
    )
    parser.add_argument(
        '--max-time',
        type=int,
        dest='max_time',
        help='Upper limit for release times and deadlines.',
        required=True,
    )
    parser.add_argument(
        '--max-duration',
        type=int,
        dest='max_duration',
        help='Upper limit for the duration of jobs.',
        required=True,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    output_data = dict()

    output_data['count'] = args.count
    output_data['max_concurrency'] = args.max_concurrency
    output_data['cases'] = []

    for _ in range(args.count):
        job_count = randint(1, args.max_jobs)

        output_data['cases'].append({
            'count': job_count,
            'jobs': [],
        })

        for _ in range(job_count):
            duration = randint(1, args.max_duration)
            release_time = randint(0, args.max_time - duration + 1)
            deadline = randint(release_time + duration - 1, args.max_time)

            output_data['cases'][-1]['jobs'].append({
                'release_time': release_time,
                'deadline': deadline,
                'duration': duration,
            })

    with open(args.output, 'w') as file:
        file.write(json.dumps(output_data, indent=4))


if __name__ == '__main__':
    main()
