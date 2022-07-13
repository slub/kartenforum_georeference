#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by nicolas.looschen@pikobytes.de on 18.01.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from sqlalchemy import Column, Integer, Text, DateTime, desc
from .meta import Base


class MapView(Base):
    __tablename__ = 'map_view'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    public_id = Column(Text())
    map_view_json = Column(Text())
    submitted = Column(DateTime(timezone=False))
    request_count = Column(Integer)
    last_request = Column(DateTime(timezone=False))
    user_id = Column(Integer)

    @classmethod
    def by_id(cls, id, dbsession):
        return dbsession.query(MapView).filter(MapView.id == id).first()

    @classmethod
    def by_public_id(cls, public_id, dbsession):
        return cls.query_by_public_id(public_id, dbsession).first()

    @classmethod
    def query_by_public_id(cls, public_id, dbsession):
        return dbsession.query(MapView).filter(MapView.public_id == public_id)

    @classmethod
    def all(cls, dbsession):
        return dbsession.query(MapView).order_by(desc(MapView.id))
