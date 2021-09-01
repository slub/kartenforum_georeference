#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 01.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package.
import logging
from pyramid.config import Configurator
from pyramid.response import Response
from sqlalchemy import engine_from_config

LOGGER = logging.getLogger(__name__)

def hello_world(request):
    LOGGER.info("test")
    return Response('Hello World!')

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

    # Initialize database
    engine = engine_from_config(settings, prefix='sqlalchemy.')

    # Debug code
    config.add_route('hello', '/')
    config.add_view(hello_world, route_name='hello')

    return config.make_wsgi_app()

def main(global_config, **settings):
    """ Main initialization function. Should be used for starting the application
        via Setuptools.

    :param global_config: Global configuration of the application
    :type global_config: dict
    """
    LOGGER.debug("Global configuration of the application:")
    LOGGER.debug(global_config)

    return createApplication(debug_mode=False, **settings)

if __name__ == '__main__':
    print("Currently the starting of the application via __main__ is not supported. Have a look at the README for starting the application via pserve.")
    # app = createApplication(debug_mode=True)
    #
    # # Serve the app via development service
    # server = make_server('0.0.0.0', 8080, app)
    # server.serve_forever()

