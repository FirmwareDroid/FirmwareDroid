# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

from api.v1.common.rq_chunk_creator import split_list_into_sublists


def enqueue_jobs(queue, job_method, document_list, *args,
                 job_timeout=60 * 60 * 24 * 10,
                 max_job_size=100):
    """
    Enqueue a job to the given queue with a standard timeout. Creates several jobs if the number of
    elements is large and enqueues them all to the same queue.
    :param max_job_size: int - maximal number of items per job.
    :param queue: class:'rq.Queue'
    :param job_method: function - the function that the worker will execute.
    :param document_list: list(documents) - the list which will be added as method arguments.
    :param job_timeout: int - maximal time of the worker to finish the job before timeout.
    """
    if len(document_list) > 100:
        sublist_list = split_list_into_sublists(document_list, max_job_size)
        for sublist in sublist_list:
            queue.enqueue(job_method, sublist, *args, job_timeout=job_timeout, failure_ttl=604800)
    else:
        queue.enqueue(job_method, document_list, *args, job_timeout=job_timeout, failure_ttl=604800)
