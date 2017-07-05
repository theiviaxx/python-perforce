# -*- coding: utf-8 -*-

"""
perforce.api
~~~~~~~~~~~~

This module implements the Perforce API

:copyright: (c) 2015 by Brett Dixon
:license: MIT, see LICENSE for more details
"""

from .models import Connection


__CONNECTION = None


def connect(*args, **kwargs):
    """Creates or returns a singleton :class:`.Connection` object"""
    global __CONNECTION
    if __CONNECTION is None:
        __CONNECTION = Connection(*args, **kwargs)

    return __CONNECTION


def edit(filename, connection=None):
    """Checks out a file into the default changelist

    :param filename: File to check out
    :type filename: str
    :param connection: Connection object to use
    :type connection: :py:class:`Connection`
    """
    c = connection or connect()
    rev = c.ls(filename)
    if rev:
        rev[0].edit()


def sync(filename, connection=None):
    """Syncs a file

    :param filename: File to check out
    :type filename: str
    :param connection: Connection object to use
    :type connection: :py:class:`Connection`
    """
    c = connection or connect()
    rev = c.ls(filename)
    if rev:
        rev[0].sync()


def info(connection=None):
    """Returns information about the current :class:`.Connection`

    :param connection: Connection object to use
    :type connection: :py:class:`Connection`
    :returns: dict
    """
    c = connection or connect()
    return c.run(['info'])[0]


def changelist(description=None, connection=None):
    """Gets or creates a :class:`.Changelist` object with a description

    :param description: Description of changelist to find or create
    :type description: str
    :param connection: Connection object to use
    :type connection: :py:class:`Connection`
    :returns: :class:`.Changelist`
    """
    c = connection or connect()

    return c.findChangelist(description)


def open(filename, connection=None):
    """Edits or Adds a filename ensuring the file is in perforce and editable

    :param filename: File to check out
    :type filename: str
    :param connection: Connection object to use
    :type connection: :py:class:`Connection`
    """
    c = connection or connect()
    res = c.ls(filename)
    if res and res[0].revision:
        res[0].edit()
    else:
        c.add(filename)
