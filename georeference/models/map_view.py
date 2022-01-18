#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 18.01.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy import desc
from .meta import Base



class MapView(Base):
    __tablename__ = 'map_view'
    __table_args__ = {'extend_existing':True}
    id = Column(Integer, primary_key=True)
    map_view_json = Column(Text())
    submitted = Column(DateTime(timezone=False))
    request_count = Column(Integer)
    last_request = Column(DateTime(timezone=False))
    user_id = Column(Integer)

    
    @classmethod
    def byId(cls, id, session):
        return session.query(MapView).filter(MapView.id == id).first()

    @classmethod
    def all(cls, session):
        return session.query(MapView).order_by(desc(MapView.id))