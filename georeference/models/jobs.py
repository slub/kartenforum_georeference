#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package.
import enum
import json
from sqlalchemy import Column, Enum, Integer, String, DateTime, desc, or_, asc
from sqlalchemy.orm import declarative_mixin

from georeference.models.meta import Base
from georeference.models.transformations import Transformation
from georeference.utils import EnumMeta


class EnumJobType(enum.Enum, metaclass=EnumMeta):
    TRANSFORMATION_PROCESS = 'transformation_process'
    TRANSFORMATION_SET_VALID = 'transformation_set_valid'
    TRANSFORMATION_SET_INVALID = 'transformation_set_invalid'
    MAPS_CREATE = "maps_create"
    MAPS_DELETE = "maps_delete"
    MAPS_UPDATE = "maps_update"
    MOSAIC_MAP_CREATE = "mosaic_map_create"
    MOSAIC_MAP_DELETE = "mosaic_map_delete"


class EnumJobState(enum.Enum, metaclass=EnumMeta):
    COMPLETED = 'completed'
    FAILED = 'failed'
    NOT_STARTED = 'not_started'


@declarative_mixin
class JobMixin(object):
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    submitted = Column(DateTime(timezone=False))
    type = Column(String(255)) # EnumJobType
    description = Column(String)
    state = Column(String(255)) # EnumJobState
    user_id = Column(String(255))
    comment = Column(String(255))


class Job(JobMixin, Base):
    __tablename__ = 'jobs'

    @classmethod
    def all(cls, session):
        return session.query(Job).order_by(desc(Job.id))

    @classmethod
    def has_not_started_jobs_for_map_id(cls, session, map_id):
        """ Checks if there are pending jobs for a given map id.

        :param session: Database session
        :type session: sqlalchemy.orm.session.Session
        :param map_id: Id of the original map
        :type map_id: int
        :result: True | False
        :rtype: bool
        """
        has_pending_jobs = False
        for job in session.query(Job).filter(Job.type == EnumJobType.TRANSFORMATION_PROCESS.value):
            task = json.loads(job.description)
            transformation = Transformation.by_id(task['transformation_id'], session)
            if transformation is not None and transformation.raw_map_id == map_id:
                has_pending_jobs = True
        return has_pending_jobs

    @classmethod
    def query_not_started_jobs(cls, job_types, dbsession):
        """ Query unprocessed jobs for a given list of job types.

        :param job_types: List of job types
        :type job_types: EnumJobName[]
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :param logger: Logger
        :type logger: logging.Logger
        :result: List of jobs
        :rtype: georeference.models.jobs.Job[]
        """
        return dbsession.query(Job).filter(Job.state == EnumJobState.NOT_STARTED.value) \
            .filter(or_(Job.type == job_type for job_type in job_types)) \
            .order_by(asc(Job.id)) \
            .all()


class JobHistory(JobMixin, Base):
    __tablename__ = 'jobs_history'
