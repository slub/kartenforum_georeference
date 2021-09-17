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
    
class Georeferenzierungsprozess(Base):
    __tablename__ = 'georeferenzierungsprozess'
    __table_args__ = {'extend_existing':True}
    id = Column(Integer, primary_key=True)
    messtischblattid = Column(Integer)
    georefparams = Column(String)
    # clipparameter = Column(String(255))
    timestamp = Column(DateTime(timezone=False))
    type = Column(String(255))
    nutzerid = Column(String(255))
    processed = Column(Boolean)
    isactive = Column(Boolean)
    overwrites = Column(Integer)
    adminvalidation = Column(String(20))
    mapid = Column(Integer)
    comment = Column(String(255))
    algorithm = Column(String(255))
    # clippolygon = Column(JsonPickleType(pickler=json))
    # clip = Column(Geometry)
    
    @classmethod
    def all(cls, session):
        return session.query(Georeferenzierungsprozess).order_by(desc(Georeferenzierungsprozess.id))
    
    @classmethod
    def arePendingProcessForMapId(cls, mapId, session):
        """ Function should check if there exist parallel unprocessed process processes in the database.
         
        Case 1.) Multiple unprocessed process processes with type "new" and overwrites 0
        Case 2.) Multiple unprocessed process processes with type "update" and the same overwrite id
         
        :type cls: georeference.models.vkdb.georeferenzierungsprozess.Georeferenzierungsprozess
        :type mapId: str
        :type session: sqlalchemy.orm.session.Session
        :return: bool """
        # at first get the actual overwrite id
        actualOverwriteProcess = cls.getActualGeoreferenceProcessForMapId(mapId, session)
         
        # at first check if there are unprocessed process processes with type new
        if actualOverwriteProcess is None:

            # check if there exist unprocessed process process for this id with type new
            unprocssedProcessOfTypeNew = session.query(Georeferenzierungsprozess).filter(Georeferenzierungsprozess.mapid == mapId)\
                .filter(Georeferenzierungsprozess.processed == False)\
                .filter(Georeferenzierungsprozess.type == "new").all()
         
            # there are more than one unprocessed and new georeferences processes 
            if len(unprocssedProcessOfTypeNew) > 0:
                return True
            else:
                return False
         
        # now check if there exist concurrent update processes
        actualOverwriteId = actualOverwriteProcess.id
        georefProcesses = session.query(Georeferenzierungsprozess).filter(Georeferenzierungsprozess.mapid == mapId)\
            .filter(Georeferenzierungsprozess.overwrites == actualOverwriteId)\
            .filter(Georeferenzierungsprozess.isactive == False)\
            .filter(Georeferenzierungsprozess.processed == False).all()
        if len(georefProcesses) > 0:
            return True
        return False
    
    @classmethod
    def clearRaceConditions(cls, georefObj, dbsession):
        """ Function clears race condition for a given process process
        
        :type cls: georeference.models.vkdb.georeferenzierungsprozess.Georeferenzierungsprozess
        :type georefObj: georeference.models.vkdb.georeferenzierungsprozess.Georeferenzierungsprozess
        :type dbsession: sqlalchemy.orm.session.Session
        :return: georeference.models.vkdb.georeferenzierungsprozess.Georeferenzierungsprozess """
        concurrentObjs = dbsession.query(Georeferenzierungsprozess).filter(Georeferenzierungsprozess.mapid == georefObj.mapid)\
            .filter(Georeferenzierungsprozess.type == georefObj.type)\
            .filter(Georeferenzierungsprozess.overwrites == georefObj.overwrites)\
            .order_by(desc(Georeferenzierungsprozess.timestamp)).all()
            
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
        georefProcess = session.query(Georeferenzierungsprozess).filter(Georeferenzierungsprozess.mapid == mapId)\
            .filter(Georeferenzierungsprozess.isactive == True)\
            .order_by(desc(Georeferenzierungsprozess.timestamp)).first()
        if georefProcess is None:
            return False
        return True
     
    @classmethod
    def by_id(cls, id, session):
        return session.query(Georeferenzierungsprozess).filter(Georeferenzierungsprozess.id == id).first()

    @classmethod
    def getActualGeoreferenceProcessForMapId(cls, mapId, session):
        return session.query(Georeferenzierungsprozess).filter(Georeferenzierungsprozess.mapid == mapId)\
            .filter(Georeferenzierungsprozess.isactive == True).first()

    def getClipAsString(self, dbsession, srid=4326):
        """ Function returns the clip as a string.

        :type sqlalchemy.orm.session.Session: dbsession
        :type int: srid (Default: 4326)
        :return: string """
        query = 'SELECT st_astext(st_transform(clip, :srid)) FROM georeferenzierungsprozess WHERE id = :id;'
        return dbsession.execute(query,{'id':self.id, 'srid':srid}).fetchone()[0]

    def getSRIDClip(self, dbsession):
        """ queries srid code for the georeferenzierungsprozess object
        :type sqlalchemy.orm.session.Session: dbsession
        :return:_ int|None """
        query = "SELECT st_srid(clip) FROM georeferenzierungsprozess WHERE id = %s"%self.id
        response = dbsession.execute(query).fetchone()
        if response is not None:
            return response[0]
        return None

    @classmethod
    def getUnprocessedObjectsOfTypeNew(cls, session):
        """ Gives back all process process of type "new" which are unprocessed. Important is the distinct operatore, which
        ignore race conflicts and gives in this case only one process back.

        :type cls: georeference.models.vkdb.georeferenzierungsprozess.Georeferenzierungsprozess
        :type dbsession: sqlalchemy.orm.session.Session
        :return: List.<georeference.models.vkdb.georeferenzierungsprozess.Georeferenzierungsprozess> """
        return session.query(Georeferenzierungsprozess).filter(Georeferenzierungsprozess.processed == False)\
            .filter(Georeferenzierungsprozess.adminvalidation != 'invalide')\
            .filter(Georeferenzierungsprozess.type == 'new')\
            .filter(Georeferenzierungsprozess.overwrites == 0)\
            .distinct(Georeferenzierungsprozess.mapid)

    @classmethod
    def getUnprocessedObjectsOfTypeUpdate(cls, session):
        """ Gives back all process process of type "Update" which are unprocessed. Important is the distinct operatore, which
        ignore race conflicts and gives in this case only one process back.

        :type cls: georeference.models.vkdb.georeferenzierungsprozess.Georeferenzierungsprozess
        :type dbsession: sqlalchemy.orm.session.Session
        :return: List.<georeference.models.vkdb.georeferenzierungsprozess.Georeferenzierungsprozess> """
        return session.query(Georeferenzierungsprozess).filter(Georeferenzierungsprozess.processed == False)\
            .filter(Georeferenzierungsprozess.adminvalidation != 'invalide')\
            .filter(Georeferenzierungsprozess.type == 'update')\
            .filter(Georeferenzierungsprozess.overwrites != 0)\
            .distinct(Georeferenzierungsprozess.mapid)

    def getClipAsGeoJSON(self, dbsession):
        """ Returns the clip geometry as geojson.

        :param dbsession: Database session object.
        :type dbsession: sqlalchemy.orm.session.Session
        :return: GeoJSON Geometry | None
        """
        query = "SELECT st_asgeojson(clip) FROM georeferenzierungsprozess WHERE id = %s" % self.id
        response = dbsession.execute(query).fetchone()
        if response is not None:
            return response[0]
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
            "UPDATE georeferenzierungsprozess SET clip = ST_GeomFromGeoJSON('%s') WHERE id = %s" % (
                json.dumps(geojsonGeom),
                self.id
            )
        )

    def getGeorefParamsAsDict(self):
        """ Returns the georef parameters as a dict object.

        :result: Georef Params
        :rtype: dict
        """
        return json.loads(self.georefparams)

    def setActive(self):
        """ Sets the georeference process to active. If - isactive - is set to True - processed - has also to be set
            to True, in any cases.
        :return:
        """
        self.processed = True
        self.isactive = True

    def setDeactive(self):
        """ Sets the georeference process to deactive.

        :return:
        """
        self.isactive = False