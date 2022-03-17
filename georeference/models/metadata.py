#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import desc
from .meta import Base



class Metadata(Base):
    __tablename__ = 'metadata'
    __table_args__ = {'extend_existing':True}
    original_map_id = Column(Integer, primary_key=True)
    title = Column(String(255))
    title_short = Column(String(70))
    title_serie = Column(String(255))
    description = Column(String(255))
    measures = Column(String(255))
    scale = Column(String(255))
    type = Column(String(255))
    technic = Column(String(255))
    ppn = Column(String(255))
    permalink = Column(String(255))
    license = Column(String(255))
    owner = Column(String(255))
    link_jpg = Column(String(255))
    link_zoomify = Column(String(255))
    time_of_publication = Column(DateTime(timezone=False))
    link_thumb_small = Column(String(255))
    link_thumb_mid = Column(String(255))
    
    @classmethod
    def byId(cls, id, session):
        return session.query(Metadata).filter(Metadata.original_map_id == id).first()

    @classmethod
    def all(cls, session):
        return session.query(Metadata).order_by(desc(Metadata.original_map_id))