#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package.
from sqlalchemy import Column, Integer, Boolean, String, DateTime, desc
from .meta import Base

class AdminJobs(Base):
    __tablename__ = 'admin_jobs'
    __table_args__ = {'extend_existing':True}
    id = Column(Integer, primary_key=True)
    georef_id = Column(Integer)
    timestamp = Column(DateTime(timezone=False))
    user_id = Column(String(255))
    processed = Column(Boolean)
    state = Column(String(255))
    comment = Column(String(255))
    
    @classmethod
    def all(cls, session):
        return session.query(AdminJobs).order_by(desc(AdminJobs.id))

    @classmethod
    def allForGeoreferenceId(cls, id, session):
        return session.query(AdminJobs).filter(AdminJobs.georef_id == id)

    @classmethod
    def by_id(cls, id, session):
        return session.query(AdminJobs).filter(AdminJobs.id == id).first()

    @classmethod
    def getUnprocessedJobs(cls, session):
        return session.query(AdminJobs).filter(AdminJobs.processed == False).order_by(desc(AdminJobs.id))

    