#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 07.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import logging
import time
import signal
import daemon
import lockfile
import traceback
from logging.handlers import TimedRotatingFileHandler
from georeference.settings import GEOREFERENCE_DAEMON_LOGGER
from georeference.settings import GEOREFERENCE_DAEMON_SETTINGS
from georeference.utils.logging import createLogger

def initializeLogger(handler):
    """ Function loads and create the logger for the daemon

    :param handler: Handler which should be used by the logger
    :type handler: TimedRotatingFileHandler
    :result: Logger
    :rtype: `logging.Logger`
    """
    # Configure the handler as a TimeRotatingFileHander
    handler.setFormatter(
        logging.Formatter(GEOREFERENCE_DAEMON_LOGGER['formatter'])
    )

    # Create and initialize the logger
    return createLogger(
        GEOREFERENCE_DAEMON_LOGGER['name'],
        GEOREFERENCE_DAEMON_LOGGER['level'],
        handler = handler,
    )

#
# Initialize TimedRotatingFileHandler and LOGGER
#

# Check if the file exists and if not create it
if not os.path.exists(GEOREFERENCE_DAEMON_LOGGER['file']):
    open(GEOREFERENCE_DAEMON_LOGGER['file'], 'a').close()

HANDLER = TimedRotatingFileHandler(GEOREFERENCE_DAEMON_LOGGER['file'], when='d', interval=1, backupCount=14)
LOGGER = initializeLogger(HANDLER)

# Make sure that the stdin/stdout/stderr paths exists and if not produce
if not os.path.exists(GEOREFERENCE_DAEMON_SETTINGS['stderr']):
    open(GEOREFERENCE_DAEMON_SETTINGS['stderr'], 'a').close()
if not os.path.exists(GEOREFERENCE_DAEMON_SETTINGS['stdout']):
    open(GEOREFERENCE_DAEMON_SETTINGS['stdout'], 'a').close()
if not os.path.exists(GEOREFERENCE_DAEMON_SETTINGS['stdin']):
    open(GEOREFERENCE_DAEMON_SETTINGS['stdin'], 'a').close()

def onStartUp():
    try:
        LOGGER.info("On Startup")
    except Exception as e:
        LOGGER.error('Error while starting the daemon')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())

def main():
    try:
        LOGGER.info('Georeference daeomon is started.')
        LOGGER.info('################################')

        # @TODO Perform initial sync.
        # @TODO Initial creation / resetting of the search index on startup
        # @TODO Check if all georeferenced files are exists
        LOGGER.info('Perform initial sync ...')
        LOGGER.info('Initial sync done.')

        while True:
            LOGGER.info('Looking for Looking for pending georeference processes ...')
            LOGGER.info('Go to sleep ...')
            time.sleep(GEOREFERENCE_DAEMON_SETTINGS['sleep_time'])
    except Exception as e:
        LOGGER.error('Error while running the daemon')
        LOGGER.error(e)
        LOGGER.error(traceback.format_exc())

def onCleanUp(a, b):
    LOGGER.info("Clean up")

# Initialize the daemon context
context = daemon.DaemonContext(
    # stderr=open(GEOREFERENCE_DAEMON_SETTINGS['stderr'], 'a'),
    # stdin=open(GEOREFERENCE_DAEMON_SETTINGS['stdin'], 'a'),
    # stdout=open(GEOREFERENCE_DAEMON_SETTINGS['stdout'], 'a'),
    pidfile=lockfile.FileLock(GEOREFERENCE_DAEMON_SETTINGS['pidfile_path']),
    files_preserve=[HANDLER.stream],
)

# Define shutdown behavior
context.signal_map = {
    signal.SIGTERM: onCleanUp,
    signal.SIGHUP: 'terminate',
}

# Start the daemon
onStartUp()

with context:
    main()