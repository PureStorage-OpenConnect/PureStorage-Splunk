"""
Description: Logger for purestorage splunk app
"""

# Imports
import os
import logging
import logging.handlers as handlers

# Get common logging format from log configs
formatter = "%(asctime)s [%(module)s]:[%(funcName)s]:%(lineno)d [%(levelname)s] | %(message)s"


def setUpLogger(logger_name, base_dir, filename, propagate=False, maxBytes=1048576, backupCount=5, level="INFO"):
    """
    Description: Generic method to setup any logger accross the framework.
    Parameters:
            logger_name: name of logger
            base_dir: log files directory
            filename: log file name
            propagate: tells whether to propagate this logger's logger to root logger.
            maxBytes: max size of log file
            backupCount: max number of file maintain as backup
            level: logger level
    Returns: logger object setup by this method.
    """
    logger = logging.getLogger(logger_name)
    if not os.path.isdir(base_dir):
        os.mkdir(base_dir)
    filepath = os.path.join(base_dir, filename)
    logger.setLevel(level)
    logger.propagate = propagate
    maxBytes = maxBytes
    backupCount = backupCount
    handler = handlers.RotatingFileHandler(filepath, maxBytes=maxBytes, backupCount=backupCount)
    handler.setFormatter(logging.Formatter(formatter))
    logger.addHandler(handler)
    return logger


def getLogger(name):
    """
    Description: get reference to framework's common logger.
    """
    return logging.getLogger(name)
