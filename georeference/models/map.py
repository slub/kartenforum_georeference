#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import json
from sqlalchemy import Column, Integer, Boolean, String
from sqlalchemy import desc
from ..settings import PATH_IMAGE_ROOT
from ..settings import PATH_GEOREF_ROOT
from .meta import Base
from .geometry import Geometry

class Map(Base):
    __tablename__ = 'map'
    __table_args__ = {'extend_existing':True}
    id = Column(Integer, primary_key=True)
    file_name = Column(String(255))
    enabled = Column(Boolean)
    map_type = Column(String(255))
    boundingbox = Column(Geometry)
    default_srs = Column(Integer)
    image_rel_path = Column(String(255))
    georef_rel_path = Column(String(255))
    map_scale = Column(Integer)

    def getAbsImagePath(self):
        """ Returns the absolute path to the raw image

        :return: Absolute path to raw image
        :rtype: str
        """
        return os.path.abspath(os.path.join(PATH_IMAGE_ROOT, self.image_rel_path))

    def getAbsGeorefPath(self):
        """ Returns the absolute path to the georef image.

        :return: Absolute path to georef image
        :rtype: str | None
        """
        return os.path.abspath(os.path.join(PATH_GEOREF_ROOT, self.georef_rel_path)) if self.georef_rel_path != None else None

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

    def getExtentAsGeoJSON(self, dbsession, srid=4326):
        """ Function returns the extent as a GeoJSON polygon.

        :param dbsession: Database conncetion
        :type dbsession: sqlalchemy.orm.session.Session
        :param srid: EPSG:Code for the output geometry
        :type srid: int
        :return: GeoJSON """
        query = 'SELECT st_asgeojson(st_transform(boundingbox, :srid)) FROM map WHERE id = :id;'
        response = dbsession.execute(query, {'id': self.id, 'srid': srid}).fetchone()[0]
        if response is not None:
            return json.loads(response)
        return None

    def getSRID(self, dbsession):
        """ queries srid code for the map object
        :type sqlalchemy.orm.session.Session: dbsession
        :return:_ int|None """
        query = "SELECT st_srid(boundingbox) FROM map WHERE id = %s"%self.id
        response = dbsession.execute(query).fetchone()
        if response is not None:
            return response[0]
        return None

    def setExtent(self, extent, srs, dbsession):
        """ Set the bounding box

        :param extent: Boundingbox coordinates
        :type extent: number[]
        :param srs: EPSG code of the coordinate system of the boundingbox
        :type srs: str
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :return: """
        if len(extent) != 4:
            raise Exception('The given extent array has more or less then 4 numbers.')

        dbsession.execute(
            "UPDATE map SET boundingbox = ST_GeomFromText('%s', %s) WHERE id = %s" % (
                'POLYGON((%(lx)s %(ly)s, %(lx)s %(uy)s, %(ux)s %(uy)s, %(ux)s %(ly)s, %(lx)s %(ly)s))' % {
                    'lx': extent[0], 'ly': extent[1], 'ux': extent[2], 'uy': extent[3]},
                int(srs.split(':')[1]),
                self.id
            )
        )

    def setActive(self, path):
        """ Methode sets the map object to active.

        :type str: path New path to the georeference image
        :return:
        """
        self.is_georeferenced = True

    def setDeactive(self):
        """ Methode sets the map object to deactive.

        :return:
        """
        self.is_georeferenced = False

    @classmethod
    def all(cls, dbsession):
        """ Equivalent to an 'SELECT * FROM map;'

        :type sqlalchemy.orm.session.Session: dbsession
        :return: List.<georeference.models.vkdb.map.Map>
        """
        return dbsession.query(Map).order_by(desc(Map.id))

    @classmethod
    def allActive(cls, dbsession):
        """ Equivalent to an 'SELECT * FROM map WHERE enabled=True;'

        :type sqlalchemy.orm.session.Session: dbsession
        :return: List.<georeference.models.vkdb.map.Map>
        """
        return dbsession.query(Map).filter(Map.enabled == True).order_by(desc(Map.id))

    @classmethod
    def byId(cls, id, dbsession):
        """
        :type str: id
        :type sqlalchemy.orm.session.Session: dbsession
        :return: georeference.models.vkdb.map.Map
        """
        return dbsession.query(Map).filter(Map.id == id).first()

