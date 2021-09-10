#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
from sqlalchemy import Column, Integer, Boolean, String
from sqlalchemy import desc
from ..settings import PATH_IMAGE_ROOT
from .meta import Base
from .geometry import Geometry

class Map(Base):
    __tablename__ = 'map'
    __table_args__ = {'extend_existing':True}
    id = Column(Integer, primary_key=True)
    apsobjectid = Column(Integer)
    apsdateiname = Column(String(255))
    originalimage = Column(String(255))
    georefimage = Column(String(255))
    isttransformiert = Column(Boolean)
    istaktiv = Column(Boolean)
    maptype = Column(String(255))
    hasgeorefparams = Column(Integer)
    boundingbox = Column(Geometry)
    recommendedsrid = Column(Integer)
    image_rel_path = Column(String(255))

    def getAbsPath(self):
        """ Returns the absolute path.

        :return: Absolute path to image
        :rtype: str
        """
        return os.path.abspath(os.path.join(PATH_IMAGE_ROOT, self.image_rel_path))

    def getExtent(self, dbsession, srid):
        """ Function returns the parsed extent.

        :type sqlalchemy.orm.session.Session: dbsession
        :type int: srid
        :return: list """
        extent = self.getExtentAsString(dbsession, srid).split(',')
        extentAsList = []
        for i in range(0,len(extent)):
            extentAsList.append(float(extent[i]))
        return extentAsList

    def getExtentAsString(self, dbsession, srid):
        """ Function returns the extent as a string.

        :type sqlalchemy.orm.session.Session: dbsession
        :type int: srid
        :return: string """
        mapObjSrid = self.getSRID(dbsession)
        if srid == -1 or mapObjSrid == -1:
            # It is not possible to transform a geometry with missing coordinate information
            query = 'SELECT st_extent(boundingbox) FROM map WHERE id = :id;'
        else:
            query = 'SELECT st_extent(st_transform(boundingbox, :srid)) FROM map WHERE id = :id;'
        pg_extent = dbsession.execute(query,{'id':self.id, 'srid':srid}).fetchone()[0]
        return pg_extent.replace(' ',',')[4:-1]

    def getSRID(self, dbsession):
        """ queries srid code for the map object
        :type sqlalchemy.orm.session.Session: dbsession
        :return:_ int|None """
        query = "SELECT st_srid(boundingbox) FROM map WHERE id = %s"%self.id
        response = dbsession.execute(query).fetchone()
        if response is not None:
            return response[0]
        return None

    def setBoundingBox(self, geomAsText, srid, dbsession):
        """ Set the bounding box
        :type str: geomAsText
        :type int: srid
        :type sqlalchemy.orm.session.Session: dbsession
        :return: """
        query = "UPDATE map SET boundingbox = ST_GeomFromText('%s', %s) WHERE id = %s"%(geomAsText, srid, self.id)
        dbsession.execute(query)

    def setActive(self, path):
        """ Methode sets the map object to active.

        :type str: path New path to the georeference image
        :return:
        """
        self.georefimage = path
        self.isttransformiert = True

    def setDeactive(self):
        """ Methode sets the map object to deactive.

        :return:
        """
        self.georefimage = ""
        self.isttransformiert = False

    @classmethod
    def all(cls, dbsession):
        """ Equivalent to an 'SELECT * FROM map;'

        :type sqlalchemy.orm.session.Session: dbsession
        :return: List.<georeference.models.vkdb.map.Map>
        """
        return dbsession.query(Map).order_by(desc(Map.id))

    @classmethod
    def allForType(cls, type, dbsession):
        """
        :type str: type
        :type sqlalchemy.orm.session.Session: dbsession
        :return: List.<georeference.models.vkdb.map.Map>
         """
        return dbsession.query(Map).filter(Map.maptype == str(type).upper())

    @classmethod
    def byId(cls, id, dbsession):
        """
        :type str: id
        :type sqlalchemy.orm.session.Session: dbsession
        :return: georeference.models.vkdb.map.Map
        """
        return dbsession.query(Map).filter(Map.id == id).first()

