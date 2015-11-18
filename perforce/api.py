# -*- coding: utf-8 -*-

"""
perforce.api
~~~~~~~~~~~~

This module implements the Perforce API

:copyright: (c) 2015 by Brett Dixon
:license: MIT, see LICENSE for more details
"""

from .models import Connection
import errors


__CONNECTION = None


def connect(*args, **kwargs):
    """Creates or returns a singleton :class:`.Connection` object"""
    global __CONNECTION
    if __CONNECTION is None:
        __CONNECTION = Connection(*args, **kwargs)

    return __CONNECTION


def edit(filename):
    """Checks out a file into the default changelist

    :param filename: File to check out
    :type filename: str
    """
    c = connect()
    rev = c.ls(filename)
    if rev:
        rev[0].edit()


def sync(filename):
    """Syncs a file

    :param filename: File to check out
    """
    c = connect()
    rev = c.ls(filename)
    if rev:
        rev[0].sync()


def info():
    """Returns information about the current :class:`.Connection`

    :returns: dict
    """
    c = connect()
    return c.run('info')[0]


def changelist(description=None):
    """Gets or creates a :class:`.Changelist` object with a description

    :param description: Description of changelist to find or create
    :type description: str
    :returns: :class:`.Changelist`
    """
    c = connect()

    return c.findChangelist(description)


def open(filename):
    """Edits or Adds a filename ensuring the file is in perforce and editable

    :param filename: File to check out
    :type filename: str
    """
    c = connect()
    res = c.ls(filename)
    if res and res[0].revision:
        res[0].edit()
    else:
        c.add(filename)
