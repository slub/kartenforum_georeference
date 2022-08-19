#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
import json
from jsonschema import validate
from datetime import datetime
from sqlalchemy import desc
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest
from georeference.models.jobs import Job, EnumJobState
from georeference.settings import GLOBAL_ERROR_MESSAGE
from georeference.schema.job import job_schema

LOGGER = logging.getLogger(__name__)

@view_config(route_name='jobs', renderer='json', request_method='GET')
def GET_jobs(request):
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
        # Extrac parameters
        pending = str(request.params['pending']).lower() == 'true' if 'pending' in request.params else None
        limit = int(request.params['limit']) if 'limit' in request.params else 100

        # Query jobs
        filter_state = EnumJobState.NOT_STARTED.value if pending != None and pending == False \
            else EnumJobState.COMPLETED.value if pending != None and pending == True else None
        jobs = request.dbsession.query(Job)\
            .filter(Job.state == filter_state if filter_state != None and pending else 1 == 1)\
            .order_by(desc(Job.submitted)) \
            .limit(limit)\
            .all()

        # Build response
        response_obj = []
        for job in jobs:
            response_obj.append({
                'id': job.id,
                'description': json.loads(job.description),
                'type': job.type,
                'state': job.state,
                'comment': job.comment,
                'user_id': job.user_id,
                'submitted': str(job.submitted)
            })

        return response_obj

    except Exception as e:
        LOGGER.error('Error while trying to return a GET maps request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)

@view_config(route_name='jobs', renderer='json', request_method='POST', accept='application/json')
def POST_jobs(request):
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
        try:
            validate(request.json_body, job_schema)
        except Exception as e:
            LOGGER.error(e)
            LOGGER.error(traceback.format_exc())
            return HTTPBadRequest("Invalid request object at POST request. %s" % e.message)

        # Create and save job
        new_job = Job(
            description=json.dumps(request.json_body['description']),
            type=request.json_body['name'],
            state=EnumJobState.NOT_STARTED.value,
            submitted=datetime.now().isoformat(),
            user_id=request.json_body['user_id']
        )
        request.dbsession.add(new_job)
        request.dbsession.flush()

        return {
            'job_id': new_job.id
        }

    except Exception as e:
        LOGGER.error('Error while trying to return a GET maps request')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)