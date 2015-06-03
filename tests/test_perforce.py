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
print(sys.path)

import path

from perforce import connection
from perforce import revision
from perforce import errors



FILE = path.path('//p4_test/synced.txt')
CLIENT_FILE = path.path(r"C:\work\p4_test\p4_test\synced.txt")
TO_EDIT = path.path('//p4_test/edit.txt')
NOT_ADDED = path.path('//p4_test/not_added.txt')


class MarshalTests(unittest.TestCase):
    def setUp(self):
        self._conn = connection.Connection(port='127.0.0.1:1666', client='p4_unit_test')

    def test_fstat(self):
        self.assertEqual(1, len(self._conn.ls(FILE)))
        self.assertTrue(isinstance(self._conn.ls(FILE)[0], revision.Revision))

        # with self.assertRaises(errors.CommandError):
        #     self._conn.ls('foo')


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self._conn = connection.Connection(port='127.0.0.1:1666', client='p4_unit_test')

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

        r = self._conn.ls(TO_EDIT)[0]
        self.assertEqual('edit', r.action)
        self.assertEqual(40, r.change.change)
        self.assertEqual(None, r.description)
        self.assertEqual('text', r.type)
        self.assertEqual('D41D8CD98F00B204E9800998ECF8427E', r.hash)
        self.assertEqual(0, len(r))

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
        self.assertEqual(43, r.head.change)
        self.assertEqual(2, r.head.revision)
        self.assertEqual('text', r.head.type)
        self.assertEqual(datetime.datetime.fromtimestamp(1428993263), r.head.time)
        self.assertEqual(datetime.datetime.fromtimestamp(1428989411), r.head.modifiedTime)
        self.assertTrue(r.head.time > r.head.modifiedTime)

    def test_errors(self):
        self._conn.add('foo')
        self._conn.level = 3
        with self.assertRaises(errors.RevisionError):
            self._conn.add('foo')


if __name__ == '__main__':
    unittest.main()