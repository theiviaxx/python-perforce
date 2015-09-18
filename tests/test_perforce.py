#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_python-perforce
----------------------------------

Tests for `python-perforce` module.
"""

import unittest
import datetime
import sys

import pytest
import path

from perforce import connection
from perforce import revision
from perforce import errors

# import wingdbstub


FILE = path.path('//p4_test/synced.txt')
CLIENT_FILE = path.path(r"C:\Users\brett\Perforce\p4_unit_tests\p4_test\synced.txt")
TO_EDIT = path.path('//p4_test/edit.txt')
NOT_ADDED = path.path('//p4_test/not_added.txt')


class MarshalTests(unittest.TestCase):
    def setUp(self):
        self._conn = connection.Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')

    def test_fstat(self):
        self.assertEqual(1, len(self._conn.ls(FILE)))
        self.assertTrue(isinstance(self._conn.ls(FILE)[0], revision.Revision))

        # with self.assertRaises(errors.CommandError):
        #     self._conn.ls('foo')


# -- Connection
def test_connection_errors():
    with pytest.raises(errors.ConnectionError):
        connection.Connection(port='foo')

    with pytest.raises(errors.ConnectionError):
        connection.Connection()

    with pytest.raises(errors.ConnectionError):
        connection.Connection(port='127.0.0.1:1666')

    with pytest.raises(errors.ConnectionError):
        connection.Connection(port='127.0.0.1:1666', client='p4_unit_tests')

    with pytest.raises(errors.CommandError):
        c = connection.Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test', level=3)
        c.run('foo')

def test_global_connection():
    c1 = connection.connect(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    c2 = connection.connect(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    assert c1 is c2
    assert str(c1) == '<Connection: 127.0.0.1:1666, p4_unit_tests, p4test>'

def test_connection_properties():
    c = connection.Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test', level=2)
    assert c.level == 2
    assert c.client == 'p4_unit_tests'
    assert c.user == 'p4test'
    assert c.default.description == '<enter description here>'




class RevisionTests(unittest.TestCase):
    def setUp(self):
        self._conn = connection.Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test', level=1)

    def test_properties(self):
        r = self._conn.ls(FILE)[0]
        self.assertEqual('<Revision: //p4_test/synced.txt#2>', repr(r))
        self.assertEqual(FILE, r.depotFile)
        self.assertEqual(CLIENT_FILE.lower(), r.clientFile.lower())
        self.assertEqual(2, r.revision)
        self.assertTrue(r.isMapped)
        self.assertFalse(r.isShelved)
        self.assertEqual(None, r.action)
        self.assertEqual(None, r.type)
        self.assertEqual([], r.openedBy)
        self.assertEqual([], r.lockedBy)
        self.assertEqual(0, r.resolved)
        self.assertTrue(r.isResolved)
        self.assertTrue(r.isSynced)
        self.assertEqual(len(r), 11)

        r = self._conn.ls(TO_EDIT)[0]
        self.assertEqual('edit', r.action)
        self.assertEqual(173, r.changelist.change)
        self.assertEqual(None, r.description)
        self.assertEqual('text', r.type)
        self.assertEqual('BEB6A43ADFB950EC6F82CEED19BEEE21', r.hash)
        self.assertEqual(10, len(r))

    def test_functions(self):
        r = self._conn.ls(TO_EDIT)[0]

        r.lock()
        self.assertTrue(r.isLocked)
        r.lock(lock=False)
        self.assertFalse(r.isLocked)
        r.sync()

        r = self._conn.ls('//p4_test/not_synced.txt')[0]
        r.sync()
        self.assertTrue(r.isSynced)
        r.sync(revision=1)
        self.assertFalse(r.isSynced)

    def test_head(self):
        r = self._conn.ls(TO_EDIT)[0]

        self.assertEqual('edit', r.head.action)
        self.assertEqual(230, r.head.change)
        self.assertEqual(3, r.head.revision)
        self.assertEqual('text', r.head.type)
        self.assertEqual(datetime.datetime(2015, 9, 17, 22, 58, 4), r.head.time)
        self.assertEqual(datetime.datetime(2015, 9, 11, 8, 20, 44), r.head.modifiedTime)
        self.assertTrue(r.head.time > r.head.modifiedTime)

    def test_errors(self):
        self._conn.add('foo')
        self._conn.level = 3
        with self.assertRaises(errors.RevisionError):
            self._conn.add('foo')

    def test_invalid(self):
        r = self._conn.ls('foo')
        self.assertEqual([], r)


def test_not_added():
    c = connection.Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    rev = c.ls(NOT_ADDED)
    assert len(rev) == 0

    res = c.canAdd(NOT_ADDED)
    assert res == True
    res = c.canAdd('foo.txt')
    assert res == False


if __name__ == '__main__':
    unittest.main()