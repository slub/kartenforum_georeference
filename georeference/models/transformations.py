#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package.
import json
from georeference.models.meta import Base
from .jobs import Job
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, desc, func
from sqlalchemy.types import UserDefinedType

class ValidationValues(Enum):
    """ Enum for valid validations values. """
    MISSING = 'missing'
    VALID = 'valid'
    INVALID = 'invalid'

class ClipType(UserDefinedType):

    def get_col_spec(self):
        return "GEOMETRY"

    def bind_expression(self, bindvalue):
        return func.ST_GeomFromGeoJSON(bindvalue, type_=self)

    def column_expression(self, col):
        return func.ST_AsGeoJSON(col, type_=self)

class Transformation(Base):
    __tablename__ = 'transformations'
    __table_args__ = {'extend_existing':True}
    id = Column(Integer, primary_key=True)
    submitted = Column(DateTime(timezone=False))
    user_id = Column(String(255))
    validation = Column(String(20))
    params = Column(String)
    overwrites = Column(Integer)
    original_map_id = Column(Integer)
    comment = Column(String(255))
    clip = Column(ClipType)

    def getParamsAsDict(self):
        """ Returns the transformations parameters as a dict object.

        :result: Transformation parameters
        :rtype: dict
        """
        return json.loads(self.params)

    @classmethod
    def all(cls, session):
        """ Queries all transformations.

        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: Transformations
        :rtype: georeference.models.transformations.Transformation[]
        """
        return session.query(Transformation).order_by(desc(Transformation.id))

    @classmethod
    def hasTransformation(cls, mapId, session):
        """ Queries all transformations.

        :param mapId: Id of the original map
        :type mapId: int
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :result: True or False signaling if there exist a valid transformation for the given original map id.
        :rtype: bool
        """
        transformation = session.query(Transformation).filter(Transformation.original_map_id == mapId)\
            .filter(Transformation.validation != ValidationValues.INVALID.value)\
            .order_by(desc(Transformation.submitted)).first()
        if transformation is None:
            return False
        return True

    # @classmethod
    # def arePendingProcessForMapId(cls, mapId, session):
    #     """ Function should check if there exist parallel unprocessed process processes in the database.
    #
    #     Case 1.) Multiple unprocessed process processes with type "new" and overwrites 0
    #     Case 2.) Multiple unprocessed process processes with type "update" and the same overwrite id
    #
    #     :type cls: georeference.models.vkdb.georeference_process.georeference_process
    #     :type mapId: str
    #     :type session: sqlalchemy.orm.session.Session
    #     :return: bool """
    #     # at first get the actual overwrite id
    #     actualOverwriteProcess = cls.getActualGeoreferenceProcessForMapId(mapId, session)
    #
    #     # at first check if there are unprocessed process processes with type new
    #     if actualOverwriteProcess is None:
    #
    #         # check if there exist unprocessed process process for this id with type new
    #         unprocssedProcessOfTypeNew = session.query(Transformation).filter(Transformation.map_id == mapId)\
    #             .filter(Transformation.processed == False)\
    #             .filter(Transformation.type == "new").all()
    #
    #         # there are more than one unprocessed and new georeferences processes
    #         if len(unprocssedProcessOfTypeNew) > 0:
    #             return True
    #         else:
    #             return False
    #
    #     # now check if there exist concurrent update processes
    #     actualOverwriteId = actualOverwriteProcess.id
    #     georefProcesses = session.query(Transformation).filter(Transformation.map_id == mapId)\
    #         .filter(Transformation.overwrites == actualOverwriteId)\
    #         .filter(Transformation.enabled == False)\
    #         .filter(Transformation.processed == False).all()
    #     if len(georefProcesses) > 0:
    #         return True
    #     return False
    
    # @classmethod
    # def clearRaceConditions(cls, georefObj, dbsession):
    #     """ Function clears race condition for a given process process
    #
    #     :type cls: georeference.models.vkdb.georeference_process.georeference_process
    #     :type georefObj: georeference.models.vkdb.georeference_process.georeference_process
    #     :type dbsession: sqlalchemy.orm.session.Session
    #     :return: georeference.models.vkdb.georeference_process.georeference_process """
    #     concurrentObjs = dbsession.query(GeoreferenceProcess).filter(GeoreferenceProcess.map_id == georefObj.map_id)\
    #         .filter(GeoreferenceProcess.type == georefObj.type)\
    #         .filter(GeoreferenceProcess.overwrites == georefObj.overwrites)\
    #         .order_by(desc(GeoreferenceProcess.timestamp)).all()
    #
    #     # there are no race conflicts
    #     if len(concurrentObjs) == 1:
    #         return georefObj
    #
    #     # there are race conflicts
    #     for i in range(1, len(concurrentObjs)):
    #         # check if there is a adminjob for this process and delete it first
    #         adminjobs = AdminJobs.allForGeoreferenceid(concurrentObjs[i].id, dbsession)
    #         for adminjob in adminjobs:
    #             dbsession.delete(adminjob)
    #         dbsession.flush()
    #         dbsession.delete(concurrentObjs[i])
    #     return concurrentObjs[0]
    
    # @classmethod
    # def isGeoreferenced(cls, mapId, session):
    #     georefProcess = session.query(GeoreferenceProcess).filter(GeoreferenceProcess.map_id == mapId)\
    #         .filter(GeoreferenceProcess.enabled == True)\
    #         .order_by(desc(GeoreferenceProcess.timestamp)).first()
    #     if georefProcess is None:
    #         return False
    #     return True
    #
    # @classmethod
    # def byId(cls, id, session):
    #     return session.query(GeoreferenceProcess).filter(GeoreferenceProcess.id == id).first()
    #
    # @classmethod
    # def getActualGeoreferenceProcessForMapId(cls, mapId, session):
    #     return session.query(GeoreferenceProcess).filter(GeoreferenceProcess.map_id == mapId)\
    #         .filter(GeoreferenceProcess.enabled == True).first()
    #
    # @classmethod
    # def getUnprocessedObjectsOfTypeNew(cls, session):
    #     """ Gives back all process process of type "new" which are unprocessed. Important is the distinct operatore, which
    #     ignore race conflicts and gives in this case only one process back.
    #
    #     :type cls: georeference.models.vkdb.georeference_process.georeference_process
    #     :type dbsession: sqlalchemy.orm.session.Session
    #     :return: List.<georeference.models.vkdb.georeference_process.georeference_process> """
    #     return session.query(GeoreferenceProcess).filter(GeoreferenceProcess.processed == False)\
    #         .filter(GeoreferenceProcess.validation != 'invalide')\
    #         .filter(GeoreferenceProcess.type == 'new')\
    #         .filter(GeoreferenceProcess.overwrites == 0)\
    #         .distinct(GeoreferenceProcess.map_id)
    #
    # @classmethod
    # def getUnprocessedObjectsOfTypeUpdate(cls, session):
    #     """ Gives back all process process of type "Update" which are unprocessed. Important is the distinct operatore, which
    #     ignore race conflicts and gives in this case only one process back.
    #
    #     :type cls: georeference.models.vkdb.georeference_process.georeference_process
    #     :type dbsession: sqlalchemy.orm.session.Session
    #     :return: List.<georeference.models.vkdb.georeference_process.georeference_process> """
    #     return session.query(GeoreferenceProcess).filter(GeoreferenceProcess.processed == False)\
    #         .filter(GeoreferenceProcess.validation != 'invalide')\
    #         .filter(GeoreferenceProcess.type == 'update')\
    #         .filter(GeoreferenceProcess.overwrites != 0)\
    #         .distinct(GeoreferenceProcess.map_id)
    #
    # def getClipAsGeoJSON(self, dbsession):
    #     """ Returns the clip geometry as geojson.
    #
    #     :param dbsession: Database session object.
    #     :type dbsession: sqlalchemy.orm.session.Session
    #     :return: GeoJSON Geometry | None
    #     """
    #     query = "SELECT st_asgeojson(clip) FROM georeference_process WHERE id = %s" % self.id
    #     response = dbsession.execute(query).fetchone()
    #     if response is not None:
    #         return json.loads(response[0])
    #     return None
    #
    # def setClipFromGeoJSON(self, geojsonGeom, dbsession):
    #     """ Set the clip property via a GeoJSON dict. It is important the the GeoJSON object contains a crs reference.
    #
    #     :param geojsonGeom: GeoJSON Geometry
    #     :type geojsonGeom: dict
    #     :param dbsession: Database session
    #     :type dbsession: sqlalchemy.orm.session.Session
    #     :return: """
    #
    #     # Validate the passed input
    #     if geojsonGeom['type'] != 'Polygon':
    #         raise TypeError('Only polygons are allowed for a clip polygon')
    #     if geojsonGeom['crs'] == None:
    #         raise TypeError('Missing crs information for the clip polygon')
    #     if geojsonGeom['coordinates'] == None:
    #         raise TypeError('Missing coordinates for the clip polygon')
    #
    #     # Execute the insert process
    #     dbsession.execute(
    #         "UPDATE georeference_process SET clip = ST_GeomFromGeoJSON('%s') WHERE id = %s" % (
    #             json.dumps(geojsonGeom),
    #             self.id
    #         )
    #     )
    #

    #
    # def setActive(self):
    #     """ Sets the georeference process to active. If - enabled - is set to True - processed - has also to be set
    #         to True, in any cases.
    #     :return:
    #     """
    #     self.processed = True
    #     self.enabled = True
    #
    # def disableGeorefProcess(self):
    #     """ Sets the georeference process to deactive.
    #
    #     :return:
    #     """
    #     self.enabled = False