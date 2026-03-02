from os.path import join, dirname, exists
import os
import logging
from logging.handlers import RotatingFileHandler

from bp_chat.logic.common.app_common import get_app_dir_path, with_uid_suf


def get_logger():
    logger = getattr(get_logger, '_logger', None)
    if not logger:
        filename = join(get_app_dir_path(), with_uid_suf('.chat') + '/log/chat.log')
        print('[ LOG ]', filename)
        dir_name = dirname(filename)
        if not exists(dir_name):
            os.makedirs(dir_name)

        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        my_handler = RotatingFileHandler(filename, mode='a', maxBytes=5 * 1024 * 1024,
                                         backupCount=2, encoding=None, delay=0)
        my_handler.setFormatter(log_formatter)
        my_handler.setLevel(logging.DEBUG)

        app_log = logging.getLogger('root')
        app_log.setLevel(logging.DEBUG)

        app_log.addHandler(my_handler)

        get_logger._logger = logger = app_log
    return logger

def set_print_log(val):
    import sys

    if not hasattr(set_print_log, '_stdout'):
        setattr(set_print_log, '_stdout', sys.stdout)

    _logger = get_logger()
    class _stdout:

        def __init__(self, name):
            self._logger_func = getattr(_logger, name)
            super().__init__()

        def write(self, *args):
            if len(args) > 0:
                s = args[0].rstrip()
                if len(s):
                    self._logger_func(s)

        def flush(self, *args):
            pass

    setattr(sys, 'stdout', _stdout('debug'))
    #setattr(sys, 'stderr', _stdout('error'))

def get_stdout_real():
    if hasattr(set_print_log, '_stdout'):
        return getattr(set_print_log, '_stdout'), True
    import sys
    return sys.stdout, False
