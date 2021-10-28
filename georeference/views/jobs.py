#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
import json
from datetime import datetime
from sqlalchemy import desc
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest
from georeference.models.jobs import Job, TaskValues
from georeference.settings import GLOBAL_ERROR_MESSAGE

LOGGER = logging.getLogger(__name__)

@view_config(route_name='jobs', renderer='json', request_method='GET')
def GET_Jobs(request):
    """ Endpoint for accessing jobs. Can be filtered via query parameter "pending" and "limit".

    :param pending: Filter processed / unprocessed
    :type pending: bool
    :param limit: Max number of response jobs
    :type limit: int
    :result: JSON object describing the map object
    :rtype: {{
      id: int,
      processed: bool,
      task: JSON,
      submitted: str,
      user_id: str,
      comment: str | null,
      task_name: str
    }[]}
    """
    try:
        if request.method != 'GET':
            return HTTPBadRequest('Endpoint does only support GET requests.')

        # Extrac parameters
        pending = bool(str(request.params['pending']).lower()) if 'pending' in request.params else None
        limit = int(request.params['limit']) if 'limit' in request.params else 100

        # Query jobs
        jobs = request.dbsession.query(Job)\
            .filter(Job.processed == pending if pending != None else 1 == 1)\
            .order_by(desc(Job.submitted)) \
            .limit(limit)\
            .all()

        # Build response
        responseObj = []
        for job in jobs:
            responseObj.append({
                'id': job.id,
                'processed': job.processed,
                'task': json.loads(job.task),
                'task_name': job.task_name,
                'comment': job.comment,
                'user_id': job.user_id,
                'submitted': str(job.submitted)
            })


        return responseObj
    except Exception as e:
        LOGGER.error('Error while trying to return a GET maps request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)

@view_config(route_name='jobs', renderer='json', request_method='POST', accept='application/json')
def POST_Jobs(request):
    """ Endpoint for posting new jobs.

    :param json_body: JSON object describing the new job
    :type json_body: {{
        user_id: str,
        task: {
            transformation_id: int,
            comment: str
        },
        task_name: str (TaskValues)
    }}
    :result: JSON object containing the job_id
    :rtype: {{
      job_id: int
    }[]}
    """
    try:
        if request.method != 'POST':
            return HTTPBadRequest('Endpoint does only support POST requests.')

        # Extract parameters
        user_id = request.json_body['user_id']
        task = request.json_body['task']
        task_name = request.json_body['task_name']

        # Check parameters
        if user_id == None or task == None or task['transformation_id'] == None or task_name == None or str(task_name).lower() not in TaskValues:
            raise HTTPBadRequest('The passed parameters are not valid.')

        # Create and save job
        newJob = Job(
            processed=False,
            task=json.dumps(task),
            task_name=task_name,
            submitted=datetime.now().isoformat(),
            user_id=user_id
        )
        request.dbsession.add(newJob)
        request.dbsession.flush()

        return {
            'job_id': newJob.id
        }
    except Exception as e:
        LOGGER.error('Error while trying to return a GET maps request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)