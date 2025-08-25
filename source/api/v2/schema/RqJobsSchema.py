# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
import django_rq
from datetime import datetime
from graphene import String, ObjectType, List, Field, Boolean, DateTime
from graphql_jwt.decorators import superuser_required
from rq.job import Job
from rq.registry import FinishedJobRegistry, FailedJobRegistry, StartedJobRegistry, ScheduledJobRegistry, DeferredJobRegistry
from webserver.settings import RQ_QUEUES

ONE_WEEK_TIMEOUT = 60 * 60 * 24 * 7
ONE_DAY_TIMEOUT = 60 * 60 * 24
ONE_HOUR_TIMEOUT = 60 * 60 * 24
MAX_OBJECT_ID_LIST_SIZE = 1000


class RqJobType(ObjectType):
    """GraphQL type representing an RQ job"""
    id = String(description="Unique job identifier")
    status = String(description="Job status (queued, started, finished, failed, etc.)")
    created_at = DateTime(description="When the job was created")
    started_at = DateTime(description="When the job started executing")
    ended_at = DateTime(description="When the job finished")
    description = String(description="Description of the job function")
    func_name = String(description="Name of the function being executed")
    timeout = graphene.Int(description="Job timeout in seconds")
    queue_name = String(description="Name of the queue the job belongs to")
    is_finished = Boolean(description="Whether the job has finished")
    is_failed = Boolean(description="Whether the job has failed")
    result = String(description="String representation of job result")
    exc_info = String(description="Exception information if job failed")


class RqQueueQuery(graphene.ObjectType):
    rq_queue_name_list = graphene.List(String,
                                       name="rq_queue_name_list"
                                       )
    rq_job_list = graphene.List(RqJobType,
                                queue_name=String(description="Filter jobs by queue name"),
                                job_ids=graphene.List(String, description="List of specific job IDs to retrieve"),
                                status=String(description="Filter jobs by status (queued, started, finished, failed, scheduled, deferred)"),
                                name="rq_job_list"
                                )
    rq_job = Field(RqJobType,
                   job_id=String(required=True, description="Job ID to retrieve"),
                   queue_name=String(description="Queue name (optional, will search all queues if not provided)"),
                   name="rq_job"
                   )

    @superuser_required
    def resolve_rq_queue_name_list(self, info):
        return RQ_QUEUES.keys()
    
    @superuser_required
    def resolve_rq_job_list(self, info, queue_name=None, job_ids=None, status=None):
        """Retrieve a list of RQ jobs with optional filtering"""
        jobs = []
        
        # Determine which queues to search
        queue_names = [queue_name] if queue_name else RQ_QUEUES.keys()
        
        for qname in queue_names:
            try:
                queue = django_rq.get_queue(qname)
                
                # If specific job IDs are provided, fetch only those
                if job_ids:
                    for job_id in job_ids:
                        try:
                            job = Job.fetch(job_id, connection=queue.connection)
                            job_data = self._create_job_data(job, qname)
                            if not status or job_data.get('status') == status:
                                jobs.append(job_data)
                        except Exception:
                            # Job not found or error fetching, skip
                            continue
                else:
                    # Get jobs from different registries based on status filter
                    if not status or status == 'queued':
                        # Get queued jobs
                        queued_jobs = queue.get_jobs()
                        for job in queued_jobs:
                            jobs.append(self._create_job_data(job, qname))
                    
                    if not status or status == 'finished':
                        # Get finished jobs
                        finished_registry = FinishedJobRegistry(queue=queue)
                        for job_id in finished_registry.get_job_ids():
                            try:
                                job = Job.fetch(job_id, connection=queue.connection)
                                jobs.append(self._create_job_data(job, qname))
                            except Exception:
                                continue
                    
                    if not status or status == 'failed':
                        # Get failed jobs
                        failed_registry = FailedJobRegistry(queue=queue)
                        for job_id in failed_registry.get_job_ids():
                            try:
                                job = Job.fetch(job_id, connection=queue.connection)
                                jobs.append(self._create_job_data(job, qname))
                            except Exception:
                                continue
                    
                    if not status or status == 'started':
                        # Get started jobs
                        started_registry = StartedJobRegistry(queue=queue)
                        for job_id in started_registry.get_job_ids():
                            try:
                                job = Job.fetch(job_id, connection=queue.connection)
                                jobs.append(self._create_job_data(job, qname))
                            except Exception:
                                continue
                    
                    if not status or status == 'scheduled':
                        # Get scheduled jobs
                        scheduled_registry = ScheduledJobRegistry(queue=queue)
                        for job_id in scheduled_registry.get_job_ids():
                            try:
                                job = Job.fetch(job_id, connection=queue.connection)
                                jobs.append(self._create_job_data(job, qname))
                            except Exception:
                                continue
                    
                    if not status or status == 'deferred':
                        # Get deferred jobs
                        deferred_registry = DeferredJobRegistry(queue=queue)
                        for job_id in deferred_registry.get_job_ids():
                            try:
                                job = Job.fetch(job_id, connection=queue.connection)
                                jobs.append(self._create_job_data(job, qname))
                            except Exception:
                                continue
                        
            except Exception as e:
                # Queue connection error, skip this queue
                continue
        
        return [RqJobType(**job_data) for job_data in jobs]
    
    @superuser_required
    def resolve_rq_job(self, info, job_id, queue_name=None):
        """Retrieve a specific RQ job by ID"""
        # Determine which queues to search
        queue_names = [queue_name] if queue_name else RQ_QUEUES.keys()
        
        for qname in queue_names:
            try:
                queue = django_rq.get_queue(qname)
                job = Job.fetch(job_id, connection=queue.connection)
                job_data = self._create_job_data(job, qname)
                return RqJobType(**job_data)
            except Exception:
                # Job not found in this queue, continue searching
                continue
        
        # Job not found in any queue
        return None
    
    def _create_job_data(self, job, queue_name):
        """Create job data dictionary from RQ Job object"""
        try:
            # Safely get datetime fields
            created_at = job.created_at if hasattr(job, 'created_at') else None
            started_at = job.started_at if hasattr(job, 'started_at') else None
            ended_at = job.ended_at if hasattr(job, 'ended_at') else None
            
            # Get result as string representation
            result = None
            if hasattr(job, 'result') and job.result is not None:
                result = str(job.result)
            
            # Get exception info as string
            exc_info = None
            if hasattr(job, 'exc_info') and job.exc_info:
                exc_info = str(job.exc_info)
            
            return {
                'id': job.id,
                'status': job.get_status() if hasattr(job, 'get_status') else 'unknown',
                'created_at': created_at,
                'started_at': started_at,
                'ended_at': ended_at,
                'description': job.description if hasattr(job, 'description') else None,
                'func_name': job.func_name if hasattr(job, 'func_name') else None,
                'timeout': job.timeout if hasattr(job, 'timeout') else None,
                'queue_name': queue_name,
                'is_finished': job.is_finished if hasattr(job, 'is_finished') else False,
                'is_failed': job.is_failed if hasattr(job, 'is_failed') else False,
                'result': result,
                'exc_info': exc_info,
            }
        except Exception as e:
            # Return minimal job data if there's an error
            return {
                'id': getattr(job, 'id', 'unknown'),
                'status': 'unknown',
                'queue_name': queue_name,
                'created_at': None,
                'started_at': None,
                'ended_at': None,
                'description': None,
                'func_name': None,
                'timeout': None,
                'is_finished': False,
                'is_failed': False,
                'result': None,
                'exc_info': None,
            }
