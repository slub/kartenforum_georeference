#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 07.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import logging
import signal
import daemon
import lockfile
import sys

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PATH_PARENT = os.path.abspath(os.path.join(BASE_PATH, '../../'))
sys.path.insert(0, BASE_PATH)
sys.path.append(BASE_PATH_PARENT)

from georeference.settings import DAEMON_SETTINGS
from georeference.daemon.runner_lifecycle import main

#
# Initialize the daemon
#

# Initialize the daemon context
pidFile = lockfile.FileLock(DAEMON_SETTINGS['pidfile_path'])
context = daemon.DaemonContext(
    pidfile=pidFile,
)

# Define shutdown behavior
def onEnd(a,b):
    pidFile.release()
    logging.shutdown()

context.signal_map = {
    signal.SIGTERM: onEnd,
    signal.SIGHUP: 'terminate',
}

# Starts the daemon
try:
    pidFile.acquire(timeout=1)
    with context:
        main(
            ini_file=os.path.join(BASE_PATH, '../../production.ini'),
            wait_on_start= DAEMON_SETTINGS['wait_on_startup'] if DAEMON_SETTINGS['wait_on_startup'] > 0 else 1,
            wait_on_loop= DAEMON_SETTINGS['sleep_time'],
        )
except lockfile.LockTimeout:
    print("There seems to be already a process running")
finally:
    pidFile.release()