# -*- coding: utf-8 -*-

"""
Pythonic Perforce API
~~~~~~~~~~~~~~~~~~~~~


:copyright: (c) 2015 by Brett Dixon
:license: MIT, see LICENSE for more details
"""

__title__ = 'perforce'
__version__ = '0.3.6'
__author__ = 'Brett Dixon'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015 Brett Dixon'

import logging.config

from .models import Connection, Revision, Changelist, ConnectionStatus, ErrorLevel
from .api import connect, edit, sync, info, changelist, open


CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level':'INFO',
            'class':'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

logging.config.dictConfig(CONFIG)

