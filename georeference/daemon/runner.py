#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Created by jacob.mendt@pikobytes.de on 07.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
import os
import signal
import subprocess
import sys

import daemon
import lockfile
from loguru import logger

from georeference.config.settings import get_settings
from georeference.daemon.runner_lifecycle import main

# For correct resolving of the paths we use derive the base_path of the file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PATH_PARENT = os.path.abspath(os.path.join(BASE_PATH, "../../"))
sys.path.insert(0, BASE_PATH)
sys.path.append(BASE_PATH_PARENT)


#
# Initialize the daemon
#


def runner():
    # Initialize the daemon context
    settings = get_settings()
    pid_file = lockfile.FileLock(settings.DAEMON_PIDFILE_PATH)
    logger.debug(f"PID file: {pid_file}")
    context = daemon.DaemonContext(
        pidfile=pid_file,
        working_directory=BASE_PATH,
        stderr=sys.stderr,
        stdout=sys.stdout,
    )

    # Define shutdown behavior
    def on_end(a, b):
        pid_file.release()

    context.signal_map = {
        signal.SIGTERM: on_end,
        signal.SIGHUP: "terminate",
    }

    # Starts the daemon
    try:
        pid_file.acquire(timeout=settings.DAEMON_PIDFILE_TIMEOUT)
        with context:
            wait_on_start = settings.DAEMON_WAIT_ON_STARTUP
            main(
                wait_on_start=wait_on_start if wait_on_start else 1,
                wait_on_loop=settings.DAEMON_SLEEP_TIME,
            )

    except lockfile.LockTimeout:
        logger.debug("There seems to be already a process running")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        logger.debug("Releasing pid ...")
        pid_file.release()


def kill():
    subprocess.run(os.path.join(BASE_PATH, "./kill-daemon.sh"), shell=True)


if __name__ == "__main__":
    runner()
