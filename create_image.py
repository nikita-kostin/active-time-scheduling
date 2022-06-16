# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
from typing import List

from models import JobWithMultipleIntervals, Schedule


def create_image_from_schedule(
        max_concurrency: int,
        jobs: List[JobWithMultipleIntervals],
        schedule: Schedule,
        output_images_path: str
) -> None:
    max_n = len(jobs)
    max_t = max([interval.end for job in jobs for interval in job.intervals]) + 1

    fig, gnt = plt.subplots()

    gnt.title.set_text("Schedule for max_concurrency=%d" % max_concurrency)

    gnt.set_xlim(0, (max_t + 1) * 10 + 20)
    gnt.set_ylim(0, max_n * 10 + 20)

    gnt.set_xlabel('Time')
    gnt.set_ylabel('Job')

    gnt.set_xticks([10 * t + 15 for t in range(max_t + 1)])
    gnt.set_xticklabels(range(max_t + 1))

    gnt.set_yticks([10 * i + 15 for i in range(max_n)])
    gnt.set_yticklabels(["$j_{%d}$" % job.id for job in jobs])
    id_to_ymin = {job.id: i * 10 + 11 for i, job in enumerate(jobs)}

    gnt.grid(True, linestyle='dashed')

    for job in jobs:
        gnt.broken_barh(
            [(interval.start * 10 + 15, (interval.end - interval.start + 1) * 10) for interval in job.intervals],
            (id_to_ymin[job.id], 8),
            facecolors='tab:red',
            alpha=0.2,
        )

    if schedule.active_time_slots is not None:
        for time_interval in schedule.active_time_slots:
            gnt.axvspan(
                time_interval.start * 10 + 15,
                (time_interval.end + 1) * 10 + 15,
                facecolor='tab:grey',
                alpha=0.2,
            )

    if schedule.job_schedules is not None:
        for js in schedule.job_schedules:
            gnt.broken_barh(
                [(js.execution_start * 10 + 15, (js.execution_end - js.execution_start + 1) * 10)],
                (id_to_ymin[js.job.id], 8),
                facecolors='tab:red',
            )

    return plt.savefig(output_images_path)
