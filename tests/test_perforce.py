#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_python-perforce
----------------------------------

Tests for `python-perforce` module.
"""

import os
import unittest
import datetime

import pytest
import path
import six

from perforce import connect, Connection, Revision, ConnectionStatus, ErrorLevel
from perforce import errors
from perforce import api

FILE = path.Path('//p4_test/synced.txt')
CLIENT_FILE = path.Path(r"E:\Users\brett\Perforce\p4_unit_tests\p4_test\synced.txt")
TO_EDIT = path.Path('//p4_test/edit.txt')
NOT_ADDED = path.Path('//p4_test/not_added.txt')
NOT_ADDED_EMPTY = path.Path('//p4_test/not_added_empty.txt')
P4PORT = 'DESKTOP-M97HMBQ:1666'
P4USER = 'p4test'
P4CLIENT = 'p4_unit_tests'


class MarshalTests(unittest.TestCase):
    def setUp(self):
        self._conn = Connection(port=P4PORT, client=P4CLIENT, user=P4USER)

    def test_fstat(self):
        self.assertEqual(1, len(self._conn.ls(FILE)))
        self.assertTrue(isinstance(self._conn.ls(FILE)[0], Revision))


# -- Connection
def test_connection_errors():
    with pytest.raises(errors.CommandError):
        api.info(Connection(port='foo'))

    with pytest.raises(errors.CommandError):
        os.environ['P4PORT'] = 'foo'
        api.info(Connection())
        os.unsetenv('P4PORT')

    # with pytest.raises(errors.CommandError):
    #     api.info(Connection(port=P4PORT))
    #
    # with pytest.raises(errors.CommandError):
    #     api.info(Connection(port=P4PORT, client=P4CLIENT))
    #
    # with pytest.raises(errors.CommandError):
    #     api.info(Connection(port=P4PORT, client=P4CLIENT, user=P4USER))


def test_global_connection():
    c1 = connect(port=P4PORT, client=P4CLIENT, user=P4USER)
    c2 = connect(port=P4PORT, client=P4CLIENT, user=P4USER)
    assert c1 is c2
    assert str(c1) == '<Connection: DESKTOP-M97HMBQ:1666, p4_unit_tests, p4test>'


def test_connection_properties():
    c = Connection(port=P4PORT, client=P4CLIENT, user=P4USER)
    assert c.level == ErrorLevel.FAILED
    c.level = ErrorLevel.INFO
    assert c.level == ErrorLevel.INFO
    assert str(c.client) == 'p4_unit_tests'
    assert c.user == 'p4test'


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self._conn = Connection(port=P4PORT, client=P4CLIENT, user=P4USER)

    def test_properties(self):
        r = self._conn.ls(FILE)[0]
        self.assertEqual('<Revision: //p4_test/synced.txt#1>', repr(r))
        self.assertEqual(FILE, r.depotFile)
        self.assertEqual(CLIENT_FILE.lower(), r.clientFile.lower())
        self.assertEqual(1, r.revision)
        self.assertTrue(r.isMapped)
        self.assertFalse(r.isShelved)
        self.assertEqual(None, r.action)
        self.assertEqual(None, r.type)
        self.assertEqual([], r.openedBy)
        self.assertEqual([], r.lockedBy)
        self.assertEqual(0, r.resolved)
        self.assertTrue(r.isResolved)
        self.assertTrue(r.isSynced)
        self.assertEqual(len(r), 6)

        r = self._conn.ls(TO_EDIT)[0]
        self.assertEqual('edit', r.action)
        self.assertEqual(23, r.changelist.change)
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

        r = Revision('//p4_test/synced.txt', self._conn)
        r.move('//p4_test/foo.txt')
        self.assertEqual(r.depotFile, '//p4_test/foo.txt')
        r.revert()

        r = Revision('//p4_test/synced.txt', self._conn)
        r.delete()
        self.assertFalse(r.clientFile.exists())
        r.revert()

    def test_head(self):
        r = self._conn.ls(TO_EDIT)[0]

        self.assertEqual('edit', r.head.action)
        self.assertEqual(26, r.head.change)
        self.assertEqual(2, r.head.revision)
        self.assertEqual('text', r.head.type)
        self.assertEqual(datetime.datetime(2017, 7, 3, 23, 15, 31), r.head.time)
        self.assertEqual(datetime.datetime(2017, 7, 3, 20, 58, 47), r.head.modifiedTime)
        self.assertTrue(r.head.time > r.head.modifiedTime)

    def test_invalid(self):
        r = self._conn.ls('foo')
        self.assertEqual([], r)


def test_not_added():
    c = Connection(port=P4PORT, client=P4CLIENT, user=P4USER)
    rev = c.ls(NOT_ADDED)
    assert len(rev) == 0

    res = c.canAdd(NOT_ADDED)
    assert res == True
    res = c.canAdd('foo.txt')
    assert res == False

def test_open():
    c = Connection(port=P4PORT, client=P4CLIENT, user=P4USER)
    rev = c.ls(NOT_ADDED)
    assert len(rev) == 0
    api.open(NOT_ADDED)
    rev = c.ls(NOT_ADDED)
    assert rev[0].action == 'add'
    api.open(NOT_ADDED)
    rev = c.ls(NOT_ADDED)
    assert rev[0].action == 'add'
    rev[0].revert()

    api.open(NOT_ADDED_EMPTY)
    rev = c.ls(NOT_ADDED_EMPTY)
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
    c = Connection(port=P4PORT, client='bad_client', user=P4USER)
    c.run(['info'])
    with pytest.raises(errors.CommandError):
        cl = c.findChangelist()

    with pytest.raises(errors.CommandError):
        c = Connection(port='foo', client='bar', user='baz')
        c.run(['info'])

def test_status():
    c = Connection(port=P4PORT, client='bad_client', user=P4USER)
    assert c.status == ConnectionStatus.INVALID_CLIENT

    c = Connection(port='foo', client='bar', user='baz')
    assert c.status == ConnectionStatus.OFFLINE

    c = Connection(port=P4PORT, client=P4CLIENT, user=P4USER)
    assert c.status == ConnectionStatus.OK
    api.connect(port=P4PORT, client=P4CLIENT, user=P4USER)
    assert api.connect().status == ConnectionStatus.OK

def test_moved():
    c = Connection(port=P4PORT, client=P4CLIENT, user=P4USER)
    assert '//p4_test/moved_file.txt' in [f.depotFile for f in c.ls('//p4_test/...')]
    assert '//p4_test/moved_file.txt' not in [f.depotFile for f in c.ls('//p4_test/...', exclude_deleted=True)]


def test_too_many_files():
    c = Connection(port=P4PORT, client=P4CLIENT, user=P4USER)
    assert c.ls(['0'*1001, '0'*1001, '0'*1001, '0'*1001, '0'*1001, '0'*1001, '0'*1001, '0'*1001, ]) == []
