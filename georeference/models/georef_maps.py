#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 05.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import json
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.types import UserDefinedType
from georeference.settings import PATH_GEOREF_ROOT
from georeference.models.meta import Base

class ExtentType(UserDefinedType):

    def get_col_spec(self):
        return "GEOMETRY"

    def bind_expression(self, bindvalue):
        return func.ST_GeomFromGeoJSON(bindvalue, type_=self)

    def column_expression(self, col):
        return func.ST_AsGeoJSON(func.ST_Envelope(col, type_=self))

class GeorefMap(Base):
    __tablename__ = 'georef_maps'
    __table_args__ = {'extend_existing':True}
    original_map_id = Column(Integer, primary_key=True)
    transformation_id = Column(Integer)
    rel_path = Column(String(255))
    extent = Column(ExtentType)
    last_processed = Column(DateTime(timezone=False))

    def getAbsPath(self):
        """ Returns the absolute path to the georeference image

        :result: Absolute path to georeference image
        :rtype: str
        """
        return os.path.abspath(os.path.join(PATH_GEOREF_ROOT, self.rel_path))

    @classmethod
    def byOriginalMapId(cls, mapId, dbsession):
        """ Returns the georef map for a given map id.

        :param mapId: Original map id
        :type mapId: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: None or reference on the georeference map associated to the original map
        :rtype: georeference.models.georef_maps.GeorefMap
        """
        return dbsession.query(GeorefMap).filter(GeorefMap.original_map_id == mapId).first()

    @classmethod
    def byTransformationId(cls, transformationId, dbsession):
        """ Returns the georef map for a given transformation id.

        :param transformationId: Transformation id
        :type transformationId: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: None or reference on the georeference map associated to the original map
        :rtype: georeference.models.georef_maps.GeorefMap
        """
        return dbsession.query(GeorefMap).filter(GeorefMap.transformation_id == transformationId).first()

    @classmethod
    def getExtentForMapId(cls, mapId, dbsession):
        """ Returns the extent for a given map id

        :param mapId: Original map id
        :type mapId: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: GeoJSON  in EPSG:4326
        :rtype: GeoJSON
        """
        query = "SELECT st_asgeojson(st_envelope(st_transform(extent, 4326))) FROM georef_maps WHERE original_map_id = %s" % mapId
        response = dbsession.execute(query).fetchone()
        if response != None:
            return json.loads(response[0])
        return None