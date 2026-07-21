"""This module serves to initialize the backend application and set up any necessary
configurations and logging.
"""

# Package Library
from kgfegmcp.config import load_settings
from kgfegmcp.utils.logging_ import initialize_logger

Settings = load_settings()

# Only need to initialize loguru once for the entire backend!
logger = initialize_logger(logging_level=Settings.LOGGING_LOG_LEVEL)
