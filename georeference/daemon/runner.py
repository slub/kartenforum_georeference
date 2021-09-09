#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 07.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
# import os
# import logging
# import time
# from daemon import runner
# from logging.handlers import TimedRotatingFileHandler
# from ..settings import GEOREFERENCE_DAEMON_LOGGER
# from ..settings import GEOREFERENCE_DAEMON_SETTINGS
# from ..utils.logging import createLogger
#
# def initializeLogger():
#     """ Function loads and create the logger for the daemon
#
#     :result: Logger
#     :rtype: `logging.Logger`
#     """
#
#     # Check if the file exists and if not create it
#     if not os.path.exists(GEOREFERENCE_DAEMON_LOGGER['file']):
#         open(GEOREFERENCE_DAEMON_LOGGER['file'], 'a').close()
#
#     # Configure the handler as a TimeRotatingFileHander
#     formatter = logging.Formatter(GEOREFERENCE_DAEMON_LOGGER['formatter'])
#     handler = TimedRotatingFileHandler(GEOREFERENCE_DAEMON_LOGGER['file'], when='d', interval=1, backupCount=14)
#     handler.setFormatter(formatter)
#
#     # Create and initialize the logger
#     return createLogger(
#         GEOREFERENCE_DAEMON_LOGGER['name'],
#         GEOREFERENCE_DAEMON_LOGGER['level'],
#         handler = handler,
#     )
#
# # Initialize the logger
# LOGGER = initializeLogger()
#
# class GeoreferenceDaemonApp():
#     """ The GeoreferenceDaemonApp is used to run the update of the georeference
#         basis in a regulary time. It could be programmed by the options parameter
#         in the settings.py
#     """
#
#     def __init__(self):
#         # Make sure that the stdin_path exists and if not produce
#         self.stdin_path = GEOREFERENCE_DAEMON_SETTINGS['stdin']
#         if not os.path.exists(self.stdin_path):
#             open(self.stdin_path, 'a').close()
#
#         self.stdout_path = GEOREFERENCE_DAEMON_SETTINGS['stdout']
#         self.stderr_path = GEOREFERENCE_DAEMON_SETTINGS['stderr']
#         self.pidfile_path = GEOREFERENCE_DAEMON_SETTINGS['pidfile_path']
#         self.pidfile_timeout = GEOREFERENCE_DAEMON_SETTINGS['pidfile_timeout']
#
#     def run(self):
#         LOGGER.info('Georeference daeomon is started.')
#         LOGGER.info('################################')
#
#         # @TODO Perform initial sync.
#         #   * Full create of a new index
#         #   * Make sure that the georeferenced files exists
#         LOGGER.info('Perform initial sync ...')
#         LOGGER.info('Initial sync done.')
#
#         while True:
#             LOGGER.info('Looking for Looking for pending georeference processes ...')
#
#
#             LOGGER.info('Go to sleep ...')
#             time.sleep(GEOREFERENCE_DAEMON_SETTINGS['sleep_time'])
#
#
# # Initialize DaemonRunner
# daemon_runner = runner.DaemonRunner(GeoreferenceDaemonApp())
#
# # This ensures that the logger file handle does not get closed during daemonization
# daemon_runner.daemon_context.files_preserve = [handler.stream]
# daemon_runner.do_action()