#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 21.06.2022
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from sqlalchemy import Column, Integer, String, DateTime, desc
from sqlalchemy.dialects.postgresql import ARRAY
from .meta import Base


class MosaicMap(Base):
    __tablename__ = 'mosaic_maps'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    name = Column(String)
    raw_map_ids = Column(ARRAY(Integer))
    title = Column(String)
    title_short = Column(String)
    time_of_publication = Column(DateTime(timezone=False))
    link_thumb = Column(String)
    map_scale = Column(Integer)
    last_change = Column(DateTime(timezone=False))
    last_service_update = Column(DateTime(timezone=False))
    last_overview_update = Column(DateTime(timezone=False))

    @classmethod
    def by_id(cls, id, dbsession):
        return dbsession.query(MosaicMap).filter(MosaicMap.id == id).first()

    @classmethod
    def all(cls, dbsession):
        return dbsession.query(MosaicMap).order_by(desc(MosaicMap.id))
