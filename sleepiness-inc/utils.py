import os

from datetime import datetime
from pytz import timezone

LOGGING_LEVEL_DEBUG = 'DEBUG'
LOGGING_LEVEL_INFO  = 'INFO'
LOGGING_LEVEL_ERROR = 'ERROR'
LOGGING_LEVEL_FATAL = 'FATAL'
LOGGING_LEVEL_NONE  = 'NONE'

TZ = os.getenv('TZ')

"""
logging class on discord.
"""
class Logger():
    log_level_list = {
        LOGGING_LEVEL_DEBUG,
        LOGGING_LEVEL_INFO,
        LOGGING_LEVEL_ERROR,
        LOGGING_LEVEL_FATAL,
        LOGGING_LEVEL_NONE
    }

    """
    constructor.

    @param log_level string (required)logging level(DEBUG, INFO, ERROR, FATAL, NONE).
    """
    def __init__(self, log_level = LOGGING_LEVEL_INFO):

        if (log_level not in self.__class__.log_level_list):
            raise Exception('invalid log level.')

        self.log_level = log_level

    """
    output log on DEBUG level.
    """
    def debug(self, text):
        if (not self.can_logging_debug()):
            return

        print('[DEBUG]%s' % (text))

    """
    output log on INFO level.
    """
    def info(self, text):
        if (not self.can_logging_info()):
            return

        print('[INFO]%s' % (text))

    """
    output log on ERROR level.
    """
    def error(self, text):
        if (not self.can_logging_error()):
            return

        print('[ERROR]%s' % (text))

    """
    output log on FATAL level.
    """
    def fatal(self, text):
        if (not self.can_logging_fatal()):
            return

        print('[FATAL]%s' % (text))
    
    """
    return can logging debug level message.

    @return bool
    """
    def can_logging_debug(self):
        return self.can_logging({
            LOGGING_LEVEL_DEBUG
        })
    
    """
    return can logging info level message.

    @return bool
    """
    def can_logging_info(self):
        return self.can_logging({
            LOGGING_LEVEL_DEBUG,
            LOGGING_LEVEL_INFO
        })
    
    """
    return can logging error level message.

    @return bool
    """
    def can_logging_error(self):
        return self.can_logging({
            LOGGING_LEVEL_DEBUG,
            LOGGING_LEVEL_INFO,
            LOGGING_LEVEL_ERROR
        })
    
    """
    return can logging fatal level message.

    @return bool
    """
    def can_logging_fatal(self):
        return self.can_logging({
            LOGGING_LEVEL_DEBUG,
            LOGGING_LEVEL_INFO,
            LOGGING_LEVEL_ERROR,
            LOGGING_LEVEL_FATAL
        })
    
    """
    return can logging none level message.

    @return bool
    """
    def can_logging_none(self):
        return self.can_logging({})

    """
    return can logging message from level list.

    @param can_logging_log_level_list array[string] approve logging log level list.
    @return bool
    """
    def can_logging(self, can_logging_log_level_list):
        if (self.log_level in can_logging_log_level_list):
            return True
        
        return False

"""
datetime warrper class.
"""
class DateTime():
    """
    return now datetime.

    @return datetime.datetime
    """
    @classmethod
    def now(cls):
        return datetime.now(tz=timezone(TZ)).replace(microsecond=0)
