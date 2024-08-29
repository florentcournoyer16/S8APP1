from cocotb.log import SimLog
from logging import Logger


class LoggerSingleton:
    """
    Singleton class to provide a single instance of a logger.

    This ensures that only one logger instance is created and used
    throughout the application, avoiding redundant instances.
    """

    _instance: Logger = None

    @classmethod
    def get_logger(cls) -> Logger:
        """
        Returns the single instance of the logger.
        If the logger doesn't exist yet, it creates one.

        Returns:
            Logger: The single instance of the logger.
        """
        if cls._instance is None:
            cls._instance = SimLog("cocotb.Test")
        return cls._instance


# Usage
logger = LoggerSingleton.get_logger()
