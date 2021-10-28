#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package.
import logging
import traceback
import sys
import os
from pyramid.config import Configurator
from georeference.settings import PATH_TMP_ROOT
from georeference.settings import PATH_GEOREF_ROOT
from georeference.settings import PATH_IMAGE_ROOT
from georeference.settings import PATH_TMS_ROOT
from georeference.settings import PATH_MAPFILE_ROOT
from georeference.utils import createPathIfNotExists

# set path for finding correct project scripts and modules
sys.path.insert(0,os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "python"))

LOGGER = logging.getLogger(__name__)

# Make sure that necessary directory exists
createPathIfNotExists(PATH_TMP_ROOT)
createPathIfNotExists(PATH_GEOREF_ROOT)
createPathIfNotExists(PATH_TMS_ROOT)
createPathIfNotExists(PATH_IMAGE_ROOT)
createPathIfNotExists(PATH_MAPFILE_ROOT)

def onError(e):
    LOGGER.error(e)

def createApplication(debug_mode=False, **settings):
    """ Creates the georeference applications.

    :param global_config: Global configuration of the application
    :type global_config: dict

    :param debug_mode: Signal if the application is loaded within debug mode
    :type debug_mode: bool

    :result: `Pyramid` WSGI application representing the committed configuration state.
    :rtype: `Pyramid` WSGI application
    """
    LOGGER.info('Start initializing the application.')
    LOGGER.debug('Use settings:')
    LOGGER.debug(settings)

    # In case debug mode is true we extend / overwrite the settings
    if debug_mode:
        settings['reload_all'] = True
        settings['debug_all'] = True

    # Initialize configurator
    config = Configurator(settings=settings)

    # Initialize database and models
    config.include('.models')

    # Initialize routes
    config.include('.routes')

    # Debug code
    config.scan('views', onerror=onError)

    return config.make_wsgi_app()

def main(global_config, **settings):
    """ Main initialization function. Should be used for starting the application
        via Setuptools.

    :param global_config: Global configuration of the application
    :type global_config: dict
    """
    try:
        LOGGER.debug("Global configuration of the application:")
        LOGGER.debug(global_config)
        app = createApplication(debug_mode=False, **settings)
        return app
    except Exception as e:
        print(e)
        print(traceback.format_exc())



if __name__ == '__main__':
    print("Currently the starting of the application via __main__ is not supported. Have a look at the README for starting the application via pserve.")
    # app = createApplication(debug_mode=True)
    #
    # # Serve the app via development service
    # server = make_server('0.0.0.0', 8080, app)
    # server.serve_forever()

