# -*- coding: utf-8 -*-

"""
perforce.errors
~~~~~~~~~~~~~~~

This module implements the Exceptions raised

:copyright: (c) 2015 by Brett Dixon
:license: MIT, see LICENSE for more details
"""


class Error(Exception):
    pass


class CommandError(Exception):
    """Errors that occur while running a command"""


class ChangelistError(Exception):
    """Errors that occur in a Changelist"""


class ShelveError(Exception):
    """Errors that occur when shelving/unshelving a file revision"""


class RevisionError(Exception):
    """Errors that occur on a file revision"""


class ConnectionError(Exception):
    """Errors that occurred with the connection"""

