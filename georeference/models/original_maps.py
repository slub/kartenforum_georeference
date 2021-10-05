#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
from sqlalchemy import Column, Integer, Boolean, String, DateTime
from sqlalchemy import desc
from georeference.settings import PATH_IMAGE_ROOT
from georeference.models.meta import Base

class OriginalMap(Base):
    __tablename__ = 'original_maps'
    __table_args__ = {'extend_existing':True}
    id = Column(Integer, primary_key=True)
    file_name = Column(String(255))
    enabled = Column(Boolean)
    map_type = Column(String(255))
    default_srs = Column(Integer)
    rel_path = Column(String(255))
    map_scale = Column(Integer)

    def getAbsPath(self):
        """ Returns the absolute path to the raw image

        :return: Absolute path to raw image
        :rtype: str
        """
        return os.path.abspath(os.path.join(PATH_IMAGE_ROOT, self.rel_path))

    @classmethod
    def all(cls, dbsession):
        """ Equivalent to an 'SELECT * FROM map;'

        :param dbsession: Session object
        :type dbsession: sqlalchemy.orm.session.Session
        :return: georeference.models.original_maps.OriginalMap[]
        """
        return dbsession.query(OriginalMap).order_by(desc(OriginalMap.id))

    @classmethod
    def allEnabled(cls, dbsession):
        """ Equivalent to an 'SELECT * FROM map WHERE enabled=True;'

        :param dbsession: Session object
        :type dbsession: sqlalchemy.orm.session.Session
        :return: georeference.models.original_maps.OriginalMap[]
        """
        return dbsession.query(OriginalMap).filter(OriginalMap.enabled == True).order_by(desc(OriginalMap.id))

    @classmethod
    def byId(cls, id, dbsession):
        """

        :param id: Id of the original map
        :type id: int
        :param dbsession: Session object
        :type dbsession: sqlalchemy.orm.session.Session
        :return: georeference.models.original_maps.OriginalMap[]
        """
        return dbsession.query(OriginalMap).filter(OriginalMap.id == id).first()

