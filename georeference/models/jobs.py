#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package.
import json
from sqlalchemy import Column, Integer, Boolean, String, DateTime, desc
from georeference.models.meta import Base
from georeference.utils import EnumMeta
from enum import Enum

class TaskValues(Enum, metaclass=EnumMeta):
    """ Enum for valid task names. """
    TRANSFORMATION_PROCESS = 'transformation_process'
    TRANSFORMATION_SET_VALID = 'transformation_set_valid'
    TRANSFORMATION_SET_INVALID = 'transformation_invalid'

class Job(Base):
    __tablename__ = 'jobs'
    __table_args__ = {'extend_existing':True}
    id = Column(Integer, primary_key=True)
    submitted = Column(DateTime(timezone=False))
    task_name = Column(String(20))
    task = Column(String)
    user_id = Column(String(255))
    processed = Column(Boolean)
    comment = Column(String(255))
    
    @classmethod
    def all(cls, session):
        return session.query(Job).order_by(desc(Job.id))

    @classmethod
    def hasPendingJobsForMapId(cls, session, mapId):
        """ Checks if there are pending jobs for a given map id.

        :param session: Database session
        :type session: sqlalchemy.orm.session.Session
        :param mapId: Id of the original map
        :type mapId: int
        :result: True | False
        :rtype: bool
        """
        hasPendingJobs = False
        for job in session.query(Job).filter(Job.task_name == TaskValues.TRANSFORMATION_PROCESS.value):
            task = json.loads(job.task)
            if task['original_map_id'] == mapId:
                hasPendingJobs = True
        return hasPendingJobs


    # @classmethod
    # def allForGeoreferenceId(cls, id, session):
    #     return session.query(AdminJobs).filter(AdminJobs.georef_id == id)
    #
    # @classmethod
    # def by_id(cls, id, session):
    #     return session.query(AdminJobs).filter(AdminJobs.id == id).first()
    #
    # @classmethod
    # def getUnprocessedJobs(cls, session):
    #     return session.query(AdminJobs).filter(AdminJobs.processed == False).order_by(desc(AdminJobs.id))

    
