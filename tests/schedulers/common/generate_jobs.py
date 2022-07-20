# -*- coding: utf-8 -*-
from numpy import arange
from numpy.random import choice, randint, random
from scipy.stats import norm

from models import JobPoolMI, JobPoolSI, TimeInterval


def generate_jobs_uniform_distribution(number_of_jobs: int, max_t: int, min_length: int, max_length: int) -> JobPoolSI:
    job_pool = JobPoolSI()

    for _ in range(number_of_jobs):
        length = randint(min_length, max_length + 1)

        release_time = randint(0, max_t - (length - 1) + 1)
        deadline = release_time + (length - 1)
        duration = randint(1, length + 1)

        job_pool.add_job(release_time, deadline, duration)

    return job_pool


def generate_jobs_normal_distribution(number_of_jobs: int, max_t: int, mu: int, sigma: int) -> JobPoolSI:
    job_pool = JobPoolSI()

    possible_length = arange(1, max_t + 1)
    p = norm.cdf(possible_length + 0.5, loc=mu, scale=sigma) - norm.cdf(possible_length - 0.5, loc=mu, scale=sigma)
    p /= p.sum()

    for _ in range(number_of_jobs):
        length = choice(possible_length, p=p)

        release_time = randint(0, max_t - (length - 1) + 1)
        deadline = release_time + (length - 1)
        duration = randint(1, length + 1)

        job_pool.add_job(release_time, deadline, duration)

    return job_pool


def generate_mi_jobs(number_of_jobs: int, max_t: int, min_p: float, max_p: float) -> JobPoolMI:
    job_pool = JobPoolMI()

    for _ in range(number_of_jobs):
        p = min_p + random() * (max_p - min_p)

        selected_timestamps = set()

        for t in range(max_t + 1):
            if random() < p:
                selected_timestamps.add(t)

        availability_intervals = TimeInterval.merge_timestamps(selected_timestamps)
        duration = randint(0, len(selected_timestamps) + 1)

        job_pool.add_job(
            [(time_interval.start, time_interval.end) for time_interval in availability_intervals],
            duration,
        )

    return job_pool
