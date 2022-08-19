#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import traceback
import logging
import os
import uuid
import json
from datetime import datetime
from jsonschema import validate
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest
from sqlalchemy import desc
from georeference.models.georef_maps import GeorefMap
from georeference.models.metadata import Metadata
from georeference.models.jobs import Job, EnumJobType, EnumJobState
from georeference.models.transformations import Transformation, EnumValidationValue
from georeference.models.raw_maps import RawMap
from georeference.schema.transformation import transformation_schema, id_only_transformation_schema
from georeference.settings import GLOBAL_ERROR_MESSAGE, PATH_MAPFILE_TEMPLATES, PATH_TMP_TRANSFORMATION_ROOT, \
    PATH_TMP_ROOT, PATH_TMP_TRANSFORMATION_DATA_ROOT, TEMPLATE_TRANSFORMATION_WMS_URL
from georeference.utils.api import to_transformation_response
from georeference.utils.georeference import get_image_extent, rectify_image
from georeference.utils.mapfile import write_mapfile
from georeference.utils.parser import from_public_map_id, to_int, to_gdal_gcps, to_public_map_id
from georeference.utils.proj import get_crs_for_transformation_params, transform_to_params_to_target_crs

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

# Initialize the logger
LOGGER = logging.getLogger(__name__)


@view_config(route_name='transformations', renderer='json', request_method='GET')
def GET_transformations_for_map_id(request):
    """ Endpoint for getting transformations. This endpoints currently supports the query parameter "user_id",
    "validation", "map_id" and "additional_properties".

    The parameter "user_id", "validation" and "map_id" are pure filter parameters. The parameter "additional_properties"
    allows the further displaying of information (currently only support in combination with "map_id").

    :result: JSON object describing the map object
    :rtype: {{
      "additional_properties": {
        active_transformation_id: number,
        default_crs: number,
        extent: [number, number, number, number],
        metadata: {
          time_publish: str,
          title: str,
        },
        pending_processes: boolean,
      } | None,
      "transformations": Transformation[],
    }}
    """
    try:
        user_id = request.params['user_id'] if 'user_id' in request.params else None
        validation = request.params['validation'] if 'validation' in request.params else None
        map_id = to_int(from_public_map_id(request.params['map_id'])) if 'map_id' in request.params else None
        additional_properties = str(request.params[
                                        'additional_properties']).lower() == "true" if 'additional_properties' in request.params else False

        if validation != None and str(validation).lower() not in EnumValidationValue:
            return HTTPBadRequest('Missing or wrong validation value.')

        # Create default response
        response_obj = {
            'transformations': []
        }

        # Return process for the georeference endpoint
        query_transformations = request.dbsession.query(Transformation, RawMap, Metadata, GeorefMap) \
            .join(RawMap, Transformation.raw_map_id == RawMap.id) \
            .join(Metadata, Transformation.raw_map_id == Metadata.raw_map_id) \
            .join(GeorefMap, Transformation.id == GeorefMap.transformation_id, isouter=True) \
            .filter(Transformation.validation == str(validation).lower() if validation is not None else 1 == 1) \
            .filter(Transformation.user_id == user_id if user_id is not None else 1 == 1) \
            .filter(Transformation.raw_map_id == map_id if map_id is not None else 1 == 1) \
            .order_by(desc(Transformation.submitted))

        for record in query_transformations:
            response_obj['transformations'].append(
                to_transformation_response(
                    transformation_obj=record[0],
                    map_obj=record[1],
                    metadata_obj=record[2],
                    dbsession=request.dbsession,
                    is_active=True if record[3] != None else False,
                )
            )

        if additional_properties and map_id != None:
            response_obj['additional_properties'] = _create_additional_properties(
                map_id,
                request.dbsession
            )

        return response_obj
    except Exception as e:
        _log_error(e, 'Error while trying to process GET transformations request')
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)


@view_config(route_name='transformations', renderer='json', request_method='POST', accept='application/json')
def POST_transformation(request):
    """ Basic endpoint for POST transformations. Supports the `dry_run` and `transformation_id` parameters, which allows to process
        temporary transformations results and if `transformation_id` if set, also for old transformations.

        The POST endpoint expects a JSON object matching the TransformationSchema. As a response it returns one of the
        following JSON objects:

        # dry_run == False
        {
            "transformation_id": number,
            "job_id": number,
            "points" : number,
        }

        # dry_run == True
        {
            "extent": [number, number, number, number],
            "layer_name": str,
            "wms_url": str,
        }


    :param json_body: Json object containing the transformation parameters
    :type json_body: TransformationSchema
    :result: JSON object describing the map object
    :rtype: {{
        "extent": [number, number, number, number],
        "layer_name": str,
        "wms_url": str,
    }|{
        "transformation_id": number,
        "job_id": number,
        "points" : number,
    }}
    """
    try:
        # Check if the endpoint should run a dry_run
        dry_run = str(request.params['dry_run']).lower() == 'true' if 'dry_run' in request.params else False

        # Check if an transformation_id has been passed. Only works in combination with dry_run
        transformation_id = int(
            request.json_body['transformation_id']) if 'transformation_id' in request.json_body else None

        # Validate json content
        try:
            if dry_run and transformation_id is not None:
                validate(request.json_body, id_only_transformation_schema)
            else:
                validate(request.json_body, transformation_schema)
        except Exception as e:
            _log_error(e, "Could not validate POST data for transformations endpoint")
            return HTTPBadRequest("Invalid request object for transformations POST request. %s" % e.message)

        # Parse the transformation obj
        transformation_obj = None
        if transformation_id is not None:
            transformation_obj = Transformation.by_id(transformation_id, request.dbsession)

        # Make sure the reference map_obj exists
        map_obj_id = transformation_obj.raw_map_id if transformation_obj is not None else to_int(
            from_public_map_id(request.json_body['map_id']))
        map_obj = RawMap.by_id(map_obj_id, request.dbsession)
        if map_obj is None:
            return HTTPBadRequest('Could not find original map for passed map id.')

        if transformation_obj is not None:
            if dry_run:
                return _handle_transformation_dry_run(
                    map_obj,
                    transformation_obj.get_params_as_dict(),
                    transformation_obj.get_target_crs_as_string(),
                    # On dry_runs we never use clip, because we want to allow the user in the client to draw
                    # clip polygons based on the full georeference image.
                    clip=None
                )
            else:
                return HTTPBadRequest('Requests with transformation_id are only allowed with the dry_run flag.')
        else:
            return _handle_request_with_transformation_payload(request, map_obj, dry_run)


    except Exception as e:
        _log_error(e, 'Error while trying to process transformations POST request')
        raise HTTPInternalServerError(GLOBAL_ERROR_MESSAGE)


def _handle_request_with_transformation_payload(request, map_obj, dry_run):
    """ Handles a request which supplies a transformation object in its json body.

    :param request: Request object
    :type request: pyramid.Request
    :param map_obj: RawMap
    :type map_obj: georeference.models.raw_maps.RawMap
    :param dry_run: Flag indicating whether the changes should be written to the db.
    :type dry_run: bool
    """
    transformation_params = request.json_body['params']
    clip = request.json_body['clip'] if 'clip' in request.json_body else None

    # inject legacy settings - static values, but required by the job runners
    transformation_params['target'] = 'EPSG:4326'
    transformation_params['source'] = 'pixel'

    if clip is not None:
        clip['crs'] = {
            'type': 'name',
            'properties': {'name': 'EPSG:4326'}
        }

    if dry_run:
        # Parse correct transformation data
        target_crs = get_crs_for_transformation_params(
            transformation_params,
            map_obj,
            target_crs=None
        )

        return _handle_transformation_dry_run(
            map_obj,
            transformation_params,
            target_crs,
            clip=None
        )
    else:
        return _handle_transformation_write(
            map_obj,
            request.json_body,
            clip=clip,
            transformation_params=transformation_params,
            dbsession=request.dbsession
        )


def _handle_transformation_dry_run(map_obj, transformation_params, target_crs, clip=None):
    """ Handles the dry_run for POST transformation requests.

    :param map_obj: RawMap
    :type map_obj: georeference.models.raw_maps.RawMap
    :param transformation_params: Dict describing the transformation_params
    :type transformation_params: Dict
    :param target_crs: ESPG code of the target crs
    :type target_crs: str
    :param clip: Clip geometry
    :type clip: dict
    :result: JSON object describing the map object
    :rtype: {{
        "extent": [number, number, number, number],
        "layer_name": str,
        "wms_url": str,
    }}
    """
    correct_transformation_params = transform_to_params_to_target_crs(
        transformation_params,
        target_crs
    )

    # Create temporary georeference file
    trg_file_name = '{}::{}.tif'.format(map_obj.file_name, uuid.uuid4())
    trg_file = _create_temporary_georeference_image(
        trg_file_name,
        map_obj.get_abs_path(),
        correct_transformation_params,
        clip
    )

    # Create temporary mapfile
    wms_url = _create_temporary_mapfile(
        map_obj,
        trg_file_name,
        correct_transformation_params
    )

    return {
        'extent': get_image_extent(trg_file),
        'layer_name': map_obj.file_name,
        'wms_url': wms_url,
    }


def _handle_transformation_write(raw_map_obj, json_body, clip, transformation_params, dbsession):
    """ Handles the permanent POST for transformation requests.

    :param raw_map_obj: RawMap
    :type raw_map_obj: georeference.models.raw_maps.RawMap
    :param json_body: Json object containing the transformation parameters
    :type json_body: TransformationSchema
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :result: JSON object describing the map object
    :rtype: {{
        "transformation_id": number,
        "job_id": number,
        "points" : number,
    }}
    """
    # Parse all relevant transformations params
    target_crs = get_crs_for_transformation_params(
        transformation_params,
        raw_map_obj,
        target_crs=None
    )
    overwrites = json_body['overwrites']
    user_id = json_body['user_id']
    submitted = datetime.now().isoformat()

    # If overwrites == 0, we check if there is already a valid transformation registered for the original map id.
    has_transformation = Transformation.has_transformation(raw_map_obj.id, dbsession)
    if overwrites == 0 and has_transformation:
        return HTTPBadRequest(
            'It is forbidden to register a new transformation for an original map, which already has a transformation registered.')

    # Save to transformations
    new_transformation = Transformation(
        submitted=submitted,
        user_id=user_id,
        params=json.dumps(transformation_params),
        target_crs=int(target_crs.split(':')[1]),
        clip=json.dumps(clip) if clip != None else None,
        validation=EnumValidationValue.MISSING.value,
        raw_map_id=raw_map_obj.id,
        overwrites=overwrites,
        comment=None
    )
    dbsession.add(new_transformation)
    dbsession.flush()

    # Save to jobs
    new_job = Job(
        description=json.dumps({
            'transformation_id': new_transformation.id
        }),
        type=EnumJobType.TRANSFORMATION_PROCESS.value,
        state=EnumJobState.NOT_STARTED.value,
        submitted=submitted,
        user_id=user_id,
        comment=None
    )
    dbsession.add(new_job)
    dbsession.flush()

    return {
        'transformation_id': new_transformation.id,
        'job_id': new_job.id,
        'points': int(len(transformation_params['gcps'])) * 5,
    }


def _create_additional_properties(map_id, dbsession):
    """ Function creates additional properties.

    :param map_id: Id of a RawMap
    :type map_id: number
    :param dbsession: Database session
    :type dbsession: sqlalchemy.orm.session.Session
    :result: Dict describing "additional_properties" for a "raw_map_id"
    :rtype: {{
        active_transformation_id: number,
        default_crs: number,
        extent: [number, number, number, number],
        metadata: {
          time_publish: str,
          title: str,
        },
        pending_processes: boolean,
    }}
    """
    # query map object and metadata
    raw_map_obj = RawMap.by_id(map_id, dbsession)
    if raw_map_obj is None:
        raise Exception('There is no map object for the passed map id.')

    georef_map_obj = GeorefMap.by_raw_map_id(raw_map_obj.id, dbsession)
    metadata_obj = Metadata.by_map_id(raw_map_obj.id, dbsession)

    return {
        'active_transformation_id': georef_map_obj.transformation_id if georef_map_obj != None else None,
        'default_crs': f'EPSG:{raw_map_obj.default_crs}',
        'extent': json.loads(
            georef_map_obj.extent) if georef_map_obj != None and georef_map_obj.extent != None else None,
        'metadata': {
            'time_publish': str(metadata_obj.time_of_publication),
            'title': metadata_obj.title,
        },
        'pending_jobs': Job.has_not_started_jobs_for_map_id(dbsession, raw_map_obj.id)
    }


def _create_temporary_georeference_image(trg_file_name, src_file, transformation_params, clip_geometry):
    """ Function creates a temporary georeference image.

    :param trg_file_name: Name of the target file
    :type trg_file_name: str
    :param src_file: Path to the source file
    :type src_file: str
    :param transformation_params: Transformation params
    :type transformation_params: dict
    :param clip_geometry: Clip geometry in GeoJSON syntax
    :type clip_geometry: dict
    :result: Path to the temporary georeference file
    :rtype: str
    """
    LOGGER.debug('Create temporary validation result ...')
    gdal_gcps = to_gdal_gcps(transformation_params['gcps'])
    trg_file = os.path.abspath(
        os.path.join(
            PATH_TMP_TRANSFORMATION_ROOT,
            trg_file_name
        )
    )

    if os.path.exists(src_file) == False:
        LOGGER.error('Could not found source file %s ...' % src_file)
        raise

    LOGGER.debug('Start processing source file %s ...' % src_file)

    # Create a rectify image
    return rectify_image(
        src_file,
        trg_file,
        transformation_params['algorithm'],
        gdal_gcps,
        transformation_params['target'].lower(),
        LOGGER,
        PATH_TMP_ROOT,
        None if clip_geometry is None else clip_geometry,
    )


def _create_temporary_mapfile(raw_map_obj, trg_file_name, transformation_params):
    """ Creates a temporary mapfile.

    :param raw_map_obj: RawMap
    :type raw_map_obj: georeference.models.raw_maps.RawMap
    :param trg_file_name: Name of the target file
    :type trg_file_name: str
    :param transformation_params: Transformation params
    :type transformation_params: dict
    :result: Link to the wms service
    :rtype: str
    """
    LOGGER.debug('Create temporary map service ...')
    LOGGER.debug(transformation_params)
    mapfile_name = f'wms_{str(uuid.uuid4()).replace("-", "_")}'
    wms_url = TEMPLATE_TRANSFORMATION_WMS_URL.format(mapfile_name)
    write_mapfile(
        os.path.join(PATH_TMP_TRANSFORMATION_ROOT, f'{mapfile_name}.map'),
        os.path.join(PATH_MAPFILE_TEMPLATES, './wms_dynamic.map'),
        {
            'wmsAbstract': f'This wms is a temporary wms for {raw_map_obj.file_name}',
            'wmsUrl': wms_url,
            'layerName': raw_map_obj.file_name,
            'layerDataPath': PATH_TMP_TRANSFORMATION_DATA_ROOT.format(trg_file_name),
            'layerProjection': transformation_params['target'].lower()
        }
    )
    return wms_url


def _get_corrected_transformations_params(raw_map_obj, json_body):
    """ Function makes sure that the correct transformation params are returns. Since newer version of the API, it expects
        that a "target_crs" for the transformation is set or tries to extract it from the database or guess it from the gcps.
        This behavior was necessary for supporting scenarios were there are no known "default_crs" in the database.

        This process can lead to scenarios where the defined "target" (old term for "target_crs") of the "gcsp" differs
        from the "target_crs" and the "gcps" therefore have to be casted to the "target_crs".

        For latter steps of the georeferencing of the image the "target" crs value of the "gcps" decides the default crs
        for the georeference image.

    :param raw_map_obj: RawMap
    :type raw_map_obj: georeference.models.raw_maps.RawMap
    :param json_body: Json object containing the transformation parameters
    :type json_body: Dict
    :result: JSON object describing the _BaseTransformationSchema
    :rtype: {_BaseTransformationSchema}
    """
    try:
        return get_crs_for_transformation_params(
            json_body['params'],
            raw_map_obj,
            target_crs=json_body['target_crs'] if 'target_crs' in json_body else None
        )
    except Exception as e:
        _log_error(e, 'Something went wrong while trying to correct the transformation params.')
        raise


def _log_error(e, message):
    """
    Forward an error to the logger

    :param: e - error that triggered the logger invocation
    :param: message - a custom message supplied to the logger
    """
    LOGGER.error(message)
    LOGGER.error(e)
    LOGGER.error(traceback.format_exc())
