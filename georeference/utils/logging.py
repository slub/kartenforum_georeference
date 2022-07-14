#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 07.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import logging
import traceback


def create_logger(name, level, file=None, formatter=None, handler=None):
    """ Creates a logger for the passed parameters.

    :param name: Name of the logger
    :type name: string
    :param level: See supported log level (https://docs.python.org/3/library/logging.html#levels)
    :type level: int
    :param file: Path to the log_file. Default is `None`
    :type file: string
    :param formatter: See supported formatter (https://docs.python.org/3/library/logging.html#logging.Formatter).
    :type formatter: logging.Formatter
    :param handler: Log handler. Default is `None`
    :type handler: logging.Handler

    :result: Logger
    :rtype: `logging.Logger`
    """
    if handler is None:
        logging.basicConfig()
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if file and formatter:
        log_handler = logging.FileHandler(file)
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)
    elif handler:
        logger.addHandler(handler)

    return logger

def log_error(e, message):
    """
    Forward an error to the logger

    :param: e - error that triggered the logger invocation
    :param: message - a custom message supplied to the logger
    """
    log = logging.getLogger(__name__)
    log.error(message)
    log.error(e)
    log.error(traceback.format_exc())

