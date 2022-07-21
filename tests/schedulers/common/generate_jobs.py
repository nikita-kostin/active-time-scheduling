# -*- coding: utf-8 -*-
from numpy import arange
from numpy.random import choice, randint, random
from scipy.stats import norm
from typing import Tuple

from models import JobPoolMI, JobPoolSI, TimeInterval


def _generate_job_attributes(max_t: int, length: int, duration_range: Tuple[int, int]) -> Tuple[int, int, int]:
    release_time = randint(0, max_t - (length - 1) + 1)
    deadline = release_time + (length - 1)
    duration = randint(duration_range[0], min(length + 1, duration_range[1] + 1))

    return release_time, deadline, duration


def generate_jobs_uniform_distribution(
        number_of_jobs: int,
        max_t: int,
        length_range: Tuple[int, int],
        duration_range: Tuple[int, int],
) -> JobPoolSI:
    job_pool = JobPoolSI()

    for _ in range(number_of_jobs):
        length = randint(length_range[0], length_range[1] + 1)
        release_time, deadline, duration = _generate_job_attributes(max_t, length, duration_range)

        job_pool.add_job(release_time, deadline, duration)

    return job_pool


def generate_jobs_normal_distribution(
        number_of_jobs: int,
        max_t: int,
        length_mu: int,
        length_sigma: int,
        duration_range: Tuple[int, int],
) -> JobPoolSI:
    job_pool = JobPoolSI()

    possible_length = arange(1, max_t + 1)
    p = norm.cdf(
        possible_length + 0.5, loc=length_mu, scale=length_sigma
    ) - norm.cdf(
        possible_length - 0.5, loc=length_mu, scale=length_sigma
    )
    p /= p.sum()

    for _ in range(number_of_jobs):
        length = choice(possible_length, p=p)
        release_time, deadline, duration = _generate_job_attributes(max_t, length, duration_range)

        job_pool.add_job(release_time, deadline, duration)

    return job_pool


def generate_mi_jobs(
        number_of_jobs: int,
        max_t: int,
        p_range: Tuple[float, float],
        max_duration: int,
) -> JobPoolMI:
    job_pool = JobPoolMI()

    for _ in range(number_of_jobs):
        p = p_range[0] + random() * (p_range[1] - p_range[0])

        selected_timestamps = set()

        for t in range(max_t + 1):
            if random() < p:
                selected_timestamps.add(t)

        availability_intervals = TimeInterval.merge_timestamps(selected_timestamps)
        duration = randint(0, min(len(selected_timestamps) + 1, max_duration + 1))

        job_pool.add_job(
            [(time_interval.start, time_interval.end) for time_interval in availability_intervals],
            duration,
        )

    return job_pool
