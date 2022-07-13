#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 06.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import uuid
import os
import subprocess
import json
import sys
import pyproj
from osgeo import gdal
from osgeo import osr
from osgeo.gdalconst import GA_ReadOnly
from georeference.settings import GDAL_CACHEMAX, GDAL_WARP_MEMORY, GDAL_NUM_THREADS, GLOBAL_PATH_GDALWARP, \
    GLOBAL_PATH_GDALADDO

# For a full list of all supported config options have a look at https://gdal.org/user/configoptions.html
GC_PARAMTER = [
    ("GDAL_CACHEMAX", GDAL_CACHEMAX),
    ("GDAL_NUM_THREADS", GDAL_NUM_THREADS)
]

# For a full list of all supported CO (creation opions) have a lock at https://gdal.org/drivers/raster/gtiff.html
CO_PARAMETER = [
    ("TILED", "YES"),
]


def _add_overviews(dst_file, overview_levels, logger):
    """ Function adds overview to given geotiff.

    :param dst_file: Path of the destination image to which overviews should be added
    :type dst_file: str
    :param overview_levels: String describing the adding of overview levels
    :type overview_levels: str
    :param logger: Logger
    :type logger: logging.Logger
    :return: str
    :raise: Exception """
    try:
        logger.debug('Adding overviews to raster %s' % dst_file)
        command = '%s --config GDAL_CACHEMAX 500 -r average %s %s' % (GLOBAL_PATH_GDALADDO, dst_file, overview_levels)
        subprocess.check_call(command, shell=True)
        return dst_file
    except Exception:
        logger.error("%s - Unexpected error while trying add overviews to the raster: %s - with command - %s" % (
            sys.stderr, sys.exc_info()[0], command))
        raise Exception("Error while running subprocess via commandline!")


def _create_vrt(src_dataset, dst_file):
    """ This functions creates a vrt for a corresponding, from gdal supported, source dataset.

    :type src_dataset: osgeo.gdal.Dataset
    :type dst_file: str
    :result: Path of the VRT
    :rtype: str """
    output_format = 'VRT'
    dst_driver = gdal.GetDriverByName(output_format)
    dst_dataset = dst_driver.CreateCopy(dst_file, src_dataset, 0)
    return dst_dataset


def _get_extent_from_dataset(dataset):
    """ Returns the extent of a given gdal dataset.

    :type gdal.Dataset: dataset
    :return: Boundingbox of the image
    :rtype: [number]
    """
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize

    geotransform = dataset.GetGeoTransform()
    bb1 = origin_x = geotransform[0]
    bb4 = origin_y = geotransform[3]

    pixel_width = geotransform[1]
    pixel_height = geotransform[5]
    width = cols * pixel_width
    height = rows * pixel_height

    bb3 = origin_x + width
    bb2 = origin_y + height
    return [bb1, bb2, bb3, bb4]


def get_extent_from_geotiff(file_path):
    """ Parses the boundingbox from a georeference image

    :param file_path: Path the GeoTIFF
    :type file_path: str
    :result: Extent
    :rtype: number[]
    """
    try:
        dataset = gdal.Open(file_path, GA_ReadOnly)
        return _get_extent_from_dataset(dataset)
    finally:
        del dataset


def get_epsg_code_from_geotiff(path):
    """ Returns the pure epsg code for a given GeoTIFF.

    :param path: Path to the geotiff
    :type path: str
    :result: EPSG code in the form "epsg:4324"
    :rtype: str
    """
    try:
        dataset = gdal.Open(path, GA_ReadOnly)
        proj = dataset.GetProjection()
        srs = osr.SpatialReference()
        srs.SetFromUserInput(proj)
        return srs.GetAttrValue('AUTHORITY', 0) + ':' + srs.GetAttrValue('AUTHORITY', 1)
    finally:
        del dataset


def get_image_extent(file_path):
    """ Returns the extent for a given georeference image.

    :param file_path: Path to the georeferenced image
    :type file_path: str
    :return: Extent of the georeference image
    :rtype: [number]
    """
    try:
        dataset = gdal.Open(file_path, GA_ReadOnly)
        return _get_extent_from_dataset(dataset)
    except Exception:
        raise
    finally:
        del dataset


def get_image_size(file_path):
    """ Functions looks for the image size of an given path

    :param file_path: Path to the image
    :type file_path: str
    :return: dict|None ({x:..., y: ....})
    :rtype: dict
    """
    if not os.path.exists(file_path):
        return None
    try:
        datafile = gdal.Open(file_path)
        if datafile:
            return {'x': datafile.RasterXSize, 'y': datafile.RasterYSize}
        return None
    except Exception:
        pass
    finally:
        if datafile:
            del datafile


def rectify_image(src_file, dst_file, algorithm, gcps, srs, logger, tmp_dir, clip_geo_json=None):
    """ Functions generates and clips a georeferenced image based on a polynom transformation. This function heavily
    relies on the usage of [gdalwarp](https://gdal.org/programs/gdalwarp.html).

    :param src_file: Source image path
    :type src_file: str
    :param dst_file: Target image path
    :type dst_file: str
    :param algorithm: Transformation algorithm for the rectification
    :type algorithm: 'polynom', 'affine', 'tps'
    :param gcps: List of ground control points for rectifing the image
    :type gcps: List.<gdal.GCP>
    :param srs: EPSG code of the spatial reference system. Currently only EPSG:4314 is supported
    :type srs: str
    :param logger: Logger
    :type logger: logging.logger
    :param tmp_dir: Path for temporary working directory
    :type tmp_dir: str
    :param clip_geo_json: Path to the GeoJSON which is used for clipping
    :type clip_geo_json: str (Default: None)
    :raise: ValueError
    :result: Path to the target image
    :rtype: str
    """
    tmp_file = None
    try:
        # define tmp file path
        tmp_data_name = uuid.uuid4()

        # get projection
        geo_proj = pyproj.CRS.from_string(srs.upper()).to_wkt()

        # Is algorithm supported
        if algorithm not in ['polynom', 'tps', 'affine']:
            raise ValueError('The given algorithm "%s" is not supported.' % algorithm)

        # Create a virtual raster dataset and add the GCP with the target geoprojection to it
        tmp_file = os.path.abspath(
            os.path.join(tmp_dir, '%s.vrt' % tmp_data_name)
        )
        logger.debug('Create temporary file - %s' % tmp_file)
        new_dataset = _create_vrt(gdal.Open(src_file, GA_ReadOnly), tmp_file)
        new_dataset.SetGCPs(gcps, geo_proj)
        new_dataset.FlushCache()

        if os.path.exists(tmp_file):
            logger.info('Rectify image with a %s transformation ...' % (algorithm))

            # For a full understanding of the warp command, have a look at the documentation: https://gdal.org/programs/gdalwarp.html
            warp_command = "{gdalwarp_path} -overwrite {config_options} {creation_options} {resampling_method} {warp_memory} {algorithm} {cutline} -dstalpha -overwrite {source_file} {target_file}".format(
                # In case no algorithm is set, the gdalwarp command tries to detect the correct order of a polynom by using
                # the count of gcps attached to the image
                algorithm="-tps" if algorithm == "tps" else "-order 1" if algorithm == "affine" else "",
                config_options=" ".join(['--config %s %s' % (el[0], el[1]) for el in GC_PARAMTER]),
                # If a shapefile with a clip polygon is defined it is used.
                cutline="-crop_to_cutline -cutline '{geojson}'".format(
                    geojson=str(clip_geo_json).replace("'", '"')) if clip_geo_json is not None else "",
                creation_options=" ".join(['-co "%s=%s"' % (el[0], el[1]) for el in CO_PARAMETER]),
                gdalwarp_path=GLOBAL_PATH_GDALWARP,
                resampling_method="-r near",
                source_file=tmp_file,
                target_file=dst_file,
                warp_memory=f"-wm {GDAL_WARP_MEMORY}",
            )

            # run the command
            logger.debug(warp_command)
            subprocess.check_output(
                warp_command,
                shell=True,
                stderr=subprocess.STDOUT
            )
        return dst_file
    except subprocess.CalledProcessError as e:
        logger.error(e.output)
        raise
    except pyproj.exceptions.CRSError as e:
        logger.error(e)
        raise
    except Exception as e:
        logger.error(e)
        raise
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        del new_dataset


def rectify_image_with_clip_and_overviews(src_file, dst_file, algorithm, gcps, gcps_srs, logger, tmp_dir, clip=None):
    """ Function rectifies a image, clips it and adds overviews to it.

    :param src_file: Source image path
    :type src_file: str
    :param dst_file: Target image path
    :type dst_file: str
    :param algorithm: Transformation algorithm for the rectification
    :type algorithm: 'polynom', 'affine', 'tps'
    :param gcps: List of ground control points for rectifing the image
    :type gcps: List.<gdal.GCP>
    :param gcps_srs: EPSG code of the spatial reference system of the gcps. Currently only EPSG:4314 is supported
    :type gcps_srs: str
    :param logger: Logger
    :type logger: logging.logger
    :param tmp_dir: Path for temporary working directory
    :type tmp_dir: str
    :param clip: Clip as a GeoJSON geometry
    :type clip: dict
    :raise: ValueError
    :result: Path to the target image
    :rtype: str """
    try:
        # Check if the target directory exists and if not create it
        if not os.path.exists(os.path.dirname(dst_file)):
            os.makedirs(os.path.dirname(dst_file))

        # Create the clip shapefile
        clip_file = None
        if clip is not None:
            clip_file = os.path.abspath(os.path.join(tmp_dir, '%s.geojson' % uuid.uuid4()))
            with open(clip_file, "w") as jsonFile:
                json.dump(clip, jsonFile, indent=2)
                jsonFile.close()

        rectify_image(
            src_file,
            dst_file,
            algorithm,
            gcps,
            gcps_srs,
            logger,
            tmp_dir,
            clip_geo_json=clip_file,
        )

        if not os.path.exists(dst_file):
            raise Exception('Could not find result of rectifyImage.')
        else:
            logger.info('Add overviews to the image ...')
            _add_overviews(dst_file, '2 4 8 16 32', logger)

        return dst_file
    except Exception as e:
        logger.error('Something went wrong while trying to generate a permanent georeference result')
        logger.error(e)
        raise
