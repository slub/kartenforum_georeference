#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 05.10.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, func, desc
from sqlalchemy.types import UserDefinedType
from georeference.settings import PATH_GEOREF_ROOT
from georeference.models.meta import Base


class ExtentType(UserDefinedType):
    # Always make sure that only EPSG:4326 is saved into the database.
    def get_col_spec(self):
        return "GEOMETRY"

    def bind_expression(self, bindvalue):
        return func.ST_Transform(func.ST_GeomFromGeoJSON(bindvalue, type_=self), 4326, type_=self)

    def column_expression(self, col):
        return func.ST_AsGeoJSON(func.ST_Transform(col, 4326, type_=self), type_=self)


class GeorefMap(Base):
    __tablename__ = 'georef_maps'
    __table_args__ = {'extend_existing': True}
    raw_map_id = Column(Integer, primary_key=True)
    transformation_id = Column(Integer)
    rel_path = Column(String(255))
    extent = Column(ExtentType)
    last_processed = Column(DateTime(timezone=False))

    @classmethod
    def all(cls, dbsession):
        """ Equivalent to an 'SELECT * FROM georef_maps;'

        :param dbsession: Session object
        :type dbsession: sqlalchemy.orm.session.Session
        :result: All georeference maps.
        :rtype: georeference.models.georef_maps.GeorefMap[]
        """
        return dbsession.query(GeorefMap).order_by(desc(GeorefMap.raw_map_id))

    def get_abs_path(self):
        """ Returns the absolute path to the georeference image

        :result: Absolute path to georeference image
        :rtype: str
        """
        return os.path.abspath(os.path.join(PATH_GEOREF_ROOT, self.rel_path))

    @classmethod
    def by_raw_map_id(cls, map_id, dbsession):
        """ Returns the georef map for a given map id.

        :param map_id: Original map id
        :type map_id: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: None or reference on the georeference map associated to the original map
        :rtype: georeference.models.georef_maps.GeorefMap
        """
        return dbsession.query(GeorefMap).filter(GeorefMap.raw_map_id == map_id).first()

    @classmethod
    def by_transformation_id(cls, transformation_id, dbsession):
        """ Returns the georef map for a given transformation id.

        :param transformation_id: Transformation id
        :type transformation_id: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: None or reference on the georeference map associated to the original map
        :rtype: georeference.models.georef_maps.GeorefMap
        """
        return dbsession.query(GeorefMap).filter(GeorefMap.transformation_id == transformation_id).first()

    @classmethod
    def get_extent_for_raw_map_id(cls, map_id, dbsession):
        """ Returns the extent for a given map id

        :param map_id: Original map id
        :type map_id: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: GeoJSON  in EPSG:4326
        :rtype: GeoJSON
        """
        query = f"SELECT st_asgeojson(st_envelope(st_transform(extent, 4326))) FROM georef_maps WHERE raw_map_id = {map_id}"
        response = dbsession.execute(query).fetchone()
        if response is not None:
            return json.loads(response[0])
        return None

    @classmethod
    def from_raw_map_and_transformation(cls, raw_map_obj, transformation_obj):
        """ Creates a GeorefMap object from a given RawMap and Transformation.

        :param raw_map_obj: RawMap
        :type raw_map_obj: georeference.models.raw_maps.RawMap
        :param transformation_obj: Transformation
        :type transformation_obj: georeference.models.transformations.Transformation
        :result: GeorefMap
        :rtype: georeference.models.georef_maps.GeorefMap
        """
        return GeorefMap(
            raw_map_id=raw_map_obj.id,
            rel_path='./%s/%s.tif' % (raw_map_obj.map_type.lower(), raw_map_obj.file_name),
            transformation_id=transformation_obj.id,
            last_processed=datetime.now().isoformat()
        )
