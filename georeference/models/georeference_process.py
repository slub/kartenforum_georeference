#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package.
import json
import ast
from .meta import Base
from .geometry import Geometry
from .adminjobs import AdminJobs
from sqlalchemy import Column, Integer, Boolean, String, DateTime, desc, PickleType, JSON
    
class GeoreferenceProcess(Base):
    __tablename__ = 'georeference_process'
    __table_args__ = {'extend_existing':True}
    id = Column(Integer, primary_key=True)
    georef_params = Column(String)
    timestamp = Column(DateTime(timezone=False))
    type = Column(String(255))
    user_id = Column(String(255))
    processed = Column(Boolean)
    enabled = Column(Boolean)
    overwrites = Column(Integer)
    validation = Column(String(20))
    map_id = Column(Integer)
    comment = Column(String(255))
    
    @classmethod
    def all(cls, session):
        return session.query(GeoreferenceProcess).order_by(desc(GeoreferenceProcess.id))
    
    @classmethod
    def arePendingProcessForMapId(cls, mapId, session):
        """ Function should check if there exist parallel unprocessed process processes in the database.
         
        Case 1.) Multiple unprocessed process processes with type "new" and overwrites 0
        Case 2.) Multiple unprocessed process processes with type "update" and the same overwrite id
         
        :type cls: georeference.models.vkdb.georeference_process.georeference_process
        :type mapId: str
        :type session: sqlalchemy.orm.session.Session
        :return: bool """
        # at first get the actual overwrite id
        actualOverwriteProcess = cls.getActualGeoreferenceProcessForMapId(mapId, session)
         
        # at first check if there are unprocessed process processes with type new
        if actualOverwriteProcess is None:

            # check if there exist unprocessed process process for this id with type new
            unprocssedProcessOfTypeNew = session.query(GeoreferenceProcess).filter(GeoreferenceProcess.map_id == mapId)\
                .filter(GeoreferenceProcess.processed == False)\
                .filter(GeoreferenceProcess.type == "new").all()
         
            # there are more than one unprocessed and new georeferences processes 
            if len(unprocssedProcessOfTypeNew) > 0:
                return True
            else:
                return False
         
        # now check if there exist concurrent update processes
        actualOverwriteId = actualOverwriteProcess.id
        georefProcesses = session.query(GeoreferenceProcess).filter(GeoreferenceProcess.map_id == mapId)\
            .filter(GeoreferenceProcess.overwrites == actualOverwriteId)\
            .filter(GeoreferenceProcess.enabled == False)\
            .filter(GeoreferenceProcess.processed == False).all()
        if len(georefProcesses) > 0:
            return True
        return False
    
    @classmethod
    def clearRaceConditions(cls, georefObj, dbsession):
        """ Function clears race condition for a given process process
        
        :type cls: georeference.models.vkdb.georeference_process.georeference_process
        :type georefObj: georeference.models.vkdb.georeference_process.georeference_process
        :type dbsession: sqlalchemy.orm.session.Session
        :return: georeference.models.vkdb.georeference_process.georeference_process """
        concurrentObjs = dbsession.query(GeoreferenceProcess).filter(GeoreferenceProcess.map_id == georefObj.map_id)\
            .filter(GeoreferenceProcess.type == georefObj.type)\
            .filter(GeoreferenceProcess.overwrites == georefObj.overwrites)\
            .order_by(desc(GeoreferenceProcess.timestamp)).all()
            
        # there are no race conflicts
        if len(concurrentObjs) == 1:
            return georefObj
        
        # there are race conflicts
        for i in range(1, len(concurrentObjs)):
            # check if there is a adminjob for this process and delete it first
            adminjobs = AdminJobs.allForGeoreferenceid(concurrentObjs[i].id, dbsession)
            for adminjob in adminjobs:
                dbsession.delete(adminjob)
            dbsession.flush()
            dbsession.delete(concurrentObjs[i])
        return concurrentObjs[0]
    
    @classmethod
    def isGeoreferenced(cls, mapId, session):
        georefProcess = session.query(GeoreferenceProcess).filter(GeoreferenceProcess.map_id == mapId)\
            .filter(GeoreferenceProcess.enabled == True)\
            .order_by(desc(GeoreferenceProcess.timestamp)).first()
        if georefProcess is None:
            return False
        return True
     
    @classmethod
    def byId(cls, id, session):
        return session.query(GeoreferenceProcess).filter(GeoreferenceProcess.id == id).first()

    @classmethod
    def getActualGeoreferenceProcessForMapId(cls, mapId, session):
        return session.query(GeoreferenceProcess).filter(GeoreferenceProcess.map_id == mapId)\
            .filter(GeoreferenceProcess.enabled == True).first()

    @classmethod
    def getUnprocessedObjectsOfTypeNew(cls, session):
        """ Gives back all process process of type "new" which are unprocessed. Important is the distinct operatore, which
        ignore race conflicts and gives in this case only one process back.

        :type cls: georeference.models.vkdb.georeference_process.georeference_process
        :type dbsession: sqlalchemy.orm.session.Session
        :return: List.<georeference.models.vkdb.georeference_process.georeference_process> """
        return session.query(GeoreferenceProcess).filter(GeoreferenceProcess.processed == False)\
            .filter(GeoreferenceProcess.validation != 'invalide')\
            .filter(GeoreferenceProcess.type == 'new')\
            .filter(GeoreferenceProcess.overwrites == 0)\
            .distinct(GeoreferenceProcess.map_id)

    @classmethod
    def getUnprocessedObjectsOfTypeUpdate(cls, session):
        """ Gives back all process process of type "Update" which are unprocessed. Important is the distinct operatore, which
        ignore race conflicts and gives in this case only one process back.

        :type cls: georeference.models.vkdb.georeference_process.georeference_process
        :type dbsession: sqlalchemy.orm.session.Session
        :return: List.<georeference.models.vkdb.georeference_process.georeference_process> """
        return session.query(GeoreferenceProcess).filter(GeoreferenceProcess.processed == False)\
            .filter(GeoreferenceProcess.validation != 'invalide')\
            .filter(GeoreferenceProcess.type == 'update')\
            .filter(GeoreferenceProcess.overwrites != 0)\
            .distinct(GeoreferenceProcess.map_id)

    def getClipAsGeoJSON(self, dbsession):
        """ Returns the clip geometry as geojson.

        :param dbsession: Database session object.
        :type dbsession: sqlalchemy.orm.session.Session
        :return: GeoJSON Geometry | None
        """
        query = "SELECT st_asgeojson(clip) FROM georeference_process WHERE id = %s" % self.id
        response = dbsession.execute(query).fetchone()
        if response is not None:
            return json.loads(response[0])
        return None

    def setClipFromGeoJSON(self, geojsonGeom, dbsession):
        """ Set the clip property via a GeoJSON dict. It is important the the GeoJSON object contains a crs reference.

        :param geojsonGeom: GeoJSON Geometry
        :type geojsonGeom: dict
        :param dbsession: Database session
        :type dbsession: sqlalchemy.orm.session.Session
        :return: """

        # Validate the passed input
        if geojsonGeom['type'] != 'Polygon':
            raise TypeError('Only polygons are allowed for a clip polygon')
        if geojsonGeom['crs'] == None:
            raise TypeError('Missing crs information for the clip polygon')
        if geojsonGeom['coordinates'] == None:
            raise TypeError('Missing coordinates for the clip polygon')

        # Execute the insert process
        dbsession.execute(
            "UPDATE georeference_process SET clip = ST_GeomFromGeoJSON('%s') WHERE id = %s" % (
                json.dumps(geojsonGeom),
                self.id
            )
        )

    def getGeorefParamsAsDict(self):
        """ Returns the georef parameters as a dict object.

        :result: Georef Params
        :rtype: dict
        """
        return json.loads(self.georef_params)

    def setActive(self):
        """ Sets the georeference process to active. If - enabled - is set to True - processed - has also to be set
            to True, in any cases.
        :return:
        """
        self.processed = True
        self.enabled = True

    def setDeactive(self):
        """ Sets the georeference process to deactive.

        :return:
        """
        self.enabled = False