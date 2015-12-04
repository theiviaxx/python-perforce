#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_python-perforce
----------------------------------

Tests for `python-perforce` module.
"""

import unittest
import datetime

import pytest
import path

from perforce import connect, Connection, Revision, ConnectionStatus, ErrorLevel
from perforce import errors
from perforce import api

FILE = path.path('//p4_test/synced.txt')
CLIENT_FILE = path.path(r"C:\Users\brett\Perforce\p4_unit_tests\p4_test\synced.txt")
TO_EDIT = path.path('//p4_test/edit.txt')
NOT_ADDED = path.path('//p4_test/not_added.txt')
CL = 398


class MarshalTests(unittest.TestCase):
    def setUp(self):
        self._conn = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')

    def test_fstat(self):
        self.assertEqual(1, len(self._conn.ls(FILE)))
        self.assertTrue(isinstance(self._conn.ls(FILE)[0], Revision))


# -- Connection
def test_connection_errors():
    with pytest.raises(errors.ConnectionError):
        Connection(port='foo')

    with pytest.raises(errors.ConnectionError):
        Connection()

    with pytest.raises(errors.ConnectionError):
        Connection(port='127.0.0.1:1666')

    with pytest.raises(errors.ConnectionError):
        Connection(port='127.0.0.1:1666', client='p4_unit_tests')

    with pytest.raises(errors.CommandError):
        c = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
        c.run('foo')

def test_global_connection():
    c1 = connect(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    c2 = connect(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    assert c1 is c2
    assert str(c1) == '<Connection: 127.0.0.1:1666, p4_unit_tests, p4test>'

def test_connection_properties():
    c = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    assert c.level == ErrorLevel.FAILED
    assert c.client == 'p4_unit_tests'
    assert c.user == 'p4test'


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self._conn = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')

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
        self.assertEqual(CL, r.changelist.change)
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

    def test_invalid(self):
        r = self._conn.ls('foo')
        self.assertEqual([], r)


def test_not_added():
    c = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    rev = c.ls(NOT_ADDED)
    assert len(rev) == 0

    res = c.canAdd(NOT_ADDED)
    assert res == True
    res = c.canAdd('foo.txt')
    assert res == False

def test_open():
    c = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    rev = c.ls(NOT_ADDED)
    assert len(rev) == 0
    api.open(NOT_ADDED)
    rev = c.ls(NOT_ADDED)
    assert rev[0].action == 'add'
    api.open(NOT_ADDED)
    rev = c.ls(NOT_ADDED)
    assert rev[0].action == 'add'
    rev[0].revert()

    api.open(CLIENT_FILE)
    rev = c.ls(CLIENT_FILE)
    assert rev[0].action == 'edit'
    api.open(CLIENT_FILE)
    rev = c.ls(CLIENT_FILE)
    assert rev[0].action == 'edit'
    rev[0].revert()


def test_bad_info():
    c = Connection(port='127.0.0.1:1666', client='bad_client', user='p4test')
    c.run('info')
    with pytest.raises(errors.CommandError):
        cl = c.findChangelist()

    with pytest.raises(errors.CommandError):
        c = Connection(port='foo', client='bar', user='baz')
        c.run('info')

def test_status():
    c = Connection(port='127.0.0.1:1666', client='bad_client', user='p4test')
    assert c.status == ConnectionStatus.INVALID_CLIENT

    c = Connection(port='foo', client='bar', user='baz')
    assert c.status == ConnectionStatus.OFFLINE

    c = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    assert c.status == ConnectionStatus.OK
    api.connect(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    assert api.connect().status == ConnectionStatus.OK

def test_moved():
    c = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    assert '//p4_test/moved.txt' in [f.depotFile for f in c.ls('//p4_test/...')]
    assert '//p4_test/moved.txt' not in [f.depotFile for f in c.ls('//p4_test/...', exclude_deleted=True)]


def test_too_many_files():
    c = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    assert c.ls(['0'*1001, '0'*1001, '0'*1001, '0'*1001, '0'*1001, '0'*1001, '0'*1001, '0'*1001, ]) == []


if __name__ == '__main__':
    unittest.main()
