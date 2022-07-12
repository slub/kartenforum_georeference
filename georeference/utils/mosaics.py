#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 22.06.22
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import subprocess
from georeference.settings import GDAL_CACHEMAX, GDAL_WARP_MEMORY, GDAL_NUM_THREADS
from georeference.utils.georeference import get_epsg_code_from_geotiff

# For a full list of all supported config options have a look at https://gdal.org/user/configoptions.html
GC_PARAMTER = [
    ('GDAL_CACHEMAX', GDAL_CACHEMAX),
    ('GDAL_NUM_THREADS', GDAL_NUM_THREADS)
]

# For a full list of all supported CO (creation opions) have a lock at https://gdal.org/drivers/raster/gtiff.html
CO_PARAMETER = [
    ('TILED', 'YES'),
]

# Parameters for gdaladdo
ADDO_PARAMETER = [
    ('COMPRESS_OVERVIEW', 'JPEG'),
    ('PHOTOMETRIC_OVERVIEW', 'RGB'),
    ('INTERLEAVE_OVERVIEW', 'PIXEL')
]


def create_mosaic_overviews(target_dataset, logger, overview_levels='2 4 8 16'):
    """ Creates the mosaic overviews for the target dataset.

    :param target_dataset: Path of the target dataset
    :type target_dataset: str
    :param logger: Logger
    :type logger: logging.Logger
    :param overview_levels: Overview levels to compute. The setting of the overview_levels is the central point for optimizing
                            performance. For large mosaic maps overview_levels like "2 4 8 16 32 64 128 256 512 1024 2048" or
                            larger should be used.
    :type overview_levels: str
    :results: Path of the overviews
    :rtype:
    """
    try:
        logger.debug(f'Start computing overview file for {target_dataset} ...')

        overview_file = f'{target_dataset}.ovr'
        if os.path.exists(overview_file):
            logger.debug('Clean old overview file.')
            os.remove(overview_file)

        build_overviews_command = 'gdaladdo {config_options} {target_dataset} {overview_levels}'.format(
            config_options=" ".join(['--config %s %s' % (el[0], el[1]) for el in GC_PARAMTER]),
            target_dataset=target_dataset,
            overview_levels=overview_levels
        )

        logger.debug(build_overviews_command)
        subprocess.check_output(
            build_overviews_command,
            shell=True,
            stderr=subprocess.STDOUT
        )

        return overview_file
    except subprocess.CalledProcessError as e:
        logger.error(e.output)
        raise

def create_mosaic_dataset(dataset_name, target_dir, geo_images, target_crs, logger):
    """ This function creates a mosaic dataset. A mosaic dataset is a VRT referencing different geotiffs. The function
        make sures that the geotiffs are all within the same coordinate system.

    :param dataset_name: Name of the dataset.
    :type dataset_name: str
    :param target_dir: Directory where to place the dataset
    :type target_dir: str
    :param geo_images: List of paths to geo_images referenced by the mosaic dataset.
    :type geo_images: [str]
    :param target_crs: EPSG code of the target_crs
    :type target_crs: int
    :param logger: Logger
    :type logger: logging.Logger
    :result: Path of the mosaic dataset
    :rtype: str
    """
    logger.debug('Start creating of mosaic dataset.')

    # Create the root directory for the dataset as well as the images directory
    target_dataset = get_mosaic_dataset_path(target_dir, dataset_name)
    root_dir = os.path.dirname(target_dataset)
    image_dir = os.path.join(root_dir, 'images')
    os.makedirs(image_dir, exist_ok=True)

    logger.debug(f'Copy and warp (target_crs={target_crs}) geo images to image directory {image_dir}')
    dataset_images = []
    for geo_img in geo_images:
        dataset_images.append(
            _warp_geo_images(
                source_file=geo_img,
                target_file=os.path.join(
                    image_dir,
                    os.path.basename(geo_img)
                ),
                target_crs=target_crs,
                logger=logger
            )
        )

    logger.debug(f'Build VRT file {target_dataset} for {len(dataset_images)} images ...')

    # The VRT is build with the command gdalbuildvrt
    _build_vrt(
        target_dataset=target_dataset,
        image_dir=image_dir,
        logger=logger
    )

    return os.path.abspath(target_dataset)

def get_mosaic_dataset_path(target_dir, dataset_name):
    """ Function for creating a mosaic dataset path.


    :param target_dir: Directory where to place the dataset
    :type target_dir: str
    :param dataset_name: Name of the dataset.
    :type dataset_name: str
    :result: Path of the mosaic dataset
    :rtype: str
    """
    return os.path.abspath(
        os.path.join(
            target_dir,
            dataset_name,
            f'{dataset_name}.vrt'
        )
    )

def get_mosaic_mapfile_path(target_dir, service_name):
    """ Function for creating a mosaic mapfile path.

    :param target_dir: Directory where to place the mapfile
    :type target_dir: str
    :param service_name: Name of the service.
    :type service_name: str
    :result: Path of the mosaic mapfile
    :rtype: str
    """
    return os.path.abspath(
        os.path.join(
            target_dir,
            f'{service_name}.map'
        )
    )

def _build_vrt(target_dataset, image_dir, logger):
    """ Creates a virtual raster dataset.

    :param target_dataset: Path of the target dataset.
    :type target_dataset: str
    :param image_dir: Directory where all images are placed
    :type image_dir: str
    :param logger: Logger
    :type logger: logging.Logger
    :result: VRT file
    :rtype: str
    """
    try:
        build_vrt_command = 'gdalbuildvrt -overwrite -srcnodata 0 {target_dataset} {input_files}'.format(
            target_dataset=target_dataset,
            input_files=f'{image_dir}/*.tif'
        )

        logger.debug(build_vrt_command)
        subprocess.check_output(
            build_vrt_command,
            shell=True,
            stderr=subprocess.STDOUT
        )

        return target_dataset
    except subprocess.CalledProcessError as e:
        logger.error(e.output)
        raise


def _warp_geo_images(source_file, target_file, target_crs, logger):
    """ Copy and reprojects a given georeference image.

    :param source_file: Path to the source georeference image
    :type source_file: str
    :param target_file: Path to the target georeference image
    :type target_file: str
    :param target_crs: EPSG code of the target_crs
    :type target_crs: int
    :param logger: Logger
    :type logger: logging.Logger
    :result: Returns the reprojected and copied georeference image
    :rtype: str
    """
    try:
        # gdal warping fails, if we want to warp to the same crs as the src image. Therefor we have to check the coordinate system first
        source_crs = get_epsg_code_from_geotiff(source_file)
        target_crs = f'EPSG:{target_crs}'

        copy_warp_command = None
        if source_crs.lower() == target_crs.lower():
            # For a full understanding of the warp command, have a look at the documentation: https://gdal.org/programs/gdalwarp.html
            copy_warp_command = "gdal_translate {config_options} {creation_options} {resampling_method} {source_file} {target_file}".format(
                config_options=" ".join(['--config %s %s' % (el[0], el[1]) for el in GC_PARAMTER]),
                creation_options=" ".join(['-co "%s=%s"' % (el[0], el[1]) for el in CO_PARAMETER]),
                resampling_method="-r near",
                source_file=source_file,
                target_file=target_file,
            )
        else:
            # For a full understanding of the warp command, have a look at the documentation: https://gdal.org/programs/gdalwarp.html
            copy_warp_command = "gdalwarp -overwrite {config_options} {creation_options} {resampling_method} {warp_memory} -t_srs {target_crs} {source_file} {target_file}".format(
                config_options=" ".join(['--config %s %s' % (el[0], el[1]) for el in GC_PARAMTER]),
                creation_options=" ".join(['-co "%s=%s"' % (el[0], el[1]) for el in CO_PARAMETER]),
                resampling_method="-r near",
                source_file=source_file,
                target_file=target_file,
                target_crs=target_crs,
                warp_memory=f"-wm {GDAL_WARP_MEMORY}",
            )

        # run the command
        logger.debug(copy_warp_command)
        subprocess.check_output(
            copy_warp_command,
            shell=True,
            stderr=subprocess.STDOUT
        )

        return target_file
    except subprocess.CalledProcessError as e:
        logger.error(e.output)
        raise