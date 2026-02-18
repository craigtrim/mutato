#!/usr/bin/env python
# -*- coding: UTF-8 -*-


import logging
from logging import Logger

from .env_io import EnvIO
from .file_io import FileIO
from .enforcer import Enforcer
from .stopwatch import Stopwatch
from .text_utils import TextUtils


def isEnabledForDebug(logger: Logger) -> bool:
    return logger.isEnabledFor(logging.DEBUG)


def isEnabledForInfo(logger: Logger) -> bool:
    return logger.isEnabledFor(logging.INFO)


def configure_logging(function_name: str) -> Logger:
    root_logger = logging.getLogger()
    if len(root_logger.handlers) > 0:
        root_logger.setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)
    return logging.getLogger(function_name)
