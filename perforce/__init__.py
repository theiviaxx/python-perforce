# -*- coding: utf-8 -*-

"""
Pythonic Perforce API
~~~~~~~~~~~~~~~~~~~~~


:copyright: (c) 2015 by Brett Dixon
:license: MIT, see LICENSE for more details
"""

__title__ = 'perforce'
__version__ = '0.5.2'
__author__ = 'Brett Dixon'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015 Brett Dixon'

from .models import Connection, Revision, Changelist, ConnectionStatus, ErrorLevel, Client, Stream, AccessType
from .api import connect, edit, sync, info, changelist, open

