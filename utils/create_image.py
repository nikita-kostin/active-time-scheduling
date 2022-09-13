# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt

from models import AbstractJobPool, Schedule


def _create_image_in_plt(
        max_concurrency: int,
        job_pool: AbstractJobPool,
        schedule: Schedule,
) -> None:
    max_n = job_pool.size
    max_t = max([interval.end for job in job_pool.jobs for interval in job.availability_intervals])

    fig, gnt = plt.subplots()

    gnt.title.set_text("Schedule for max_concurrency=%d" % max_concurrency)

    gnt.set_xlim(0, (max_t + 1) * 10 + 20)
    gnt.set_ylim(0, max_n * 10 + 20)

    gnt.set_xlabel('Time')
    gnt.set_ylabel('Job')

    gnt.set_xticks([10 * t + 15 for t in range(max_t + 1)])
    gnt.set_xticklabels(range(max_t + 1))

    gnt.set_yticks([10 * i + 15 for i in range(max_n)])
    gnt.set_yticklabels(["$j_{%d}$" % job.id for job in job_pool.jobs])
    id_to_ymin = {job.id: i * 10 + 11 for i, job in enumerate(job_pool.jobs)}

    gnt.grid(True, linestyle='dashed')

    for job in job_pool.jobs:
        gnt.broken_barh(
            [(interval.start * 10 + 15, (interval.end - interval.start + 1) * 10) for interval in
             job.availability_intervals],
            (id_to_ymin[job.id], 8),
            facecolors='tab:red',
            alpha=0.2,
        )

    if schedule.active_time_intervals is not None:
        for time_interval in schedule.active_time_intervals:
            gnt.axvspan(
                time_interval.start * 10 + 15,
                (time_interval.end + 1) * 10 + 15,
                facecolor='tab:grey',
                alpha=0.2,
            )

    if schedule.job_schedules is not None:
        for js in schedule.job_schedules:
            for interval in js.execution_intervals:
                gnt.broken_barh(
                    [(interval.start * 10 + 15, (interval.end - interval.start + 1) * 10)],
                    (id_to_ymin[js.job.id], 8),
                    facecolors='tab:red',
                )


def save_image_from_schedule(
        max_concurrency: int,
        job_pool: AbstractJobPool,
        schedule: Schedule,
        output_images_path: str,
) -> None:
    """
    Creates a visualization of the schedule using boxplots from the matplotlib package and saves it under a given path.
    :param max_concurrency: Maximum number of jobs allowed to run concurrently.
    :param job_pool: Processed job pool.
    :param schedule: Resulting schedule.
    :param output_images_path: Path to save the resulting image to.
    :return: None
    """
    _create_image_in_plt(max_concurrency, job_pool, schedule)
    return plt.savefig(output_images_path, bbox_inches='tight')


def show_image_from_schedule(
        max_concurrency: int,
        job_pool: AbstractJobPool,
        schedule: Schedule,
) -> None:
    """
    Creates a visualization of the schedule using boxplots from the matplotlib package and shows it using plt.show().
    :param max_concurrency: Maximum number of jobs allowed to run concurrently.
    :param job_pool: Processed job pool.
    :param schedule: Resulting schedule.
    :return: None
    """
    _create_image_in_plt(max_concurrency, job_pool, schedule)
    return plt.show()
