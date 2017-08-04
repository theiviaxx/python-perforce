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
import random
import string

import path
import pytest
import six

from perforce import Connection, Changelist
from perforce import errors


TO_ADD = path.path(r"E:\Users\brett\Perforce\p4_unit_tests\p4_test\to_add1.txt")
CL = 23
P4PORT = 'DESKTOP-M97HMBQ:1666'
P4USER = 'p4test'
P4CLIENT = 'p4_unit_tests'


class ChangelistTests(unittest.TestCase):
    def setUp(self):
        self._conn = Connection(port=P4PORT, client=P4CLIENT, user=P4USER)
        # pytest.deprecated_call(self._conn.findChangelist, CL)

    def test_changelist(self):
        cl = self._conn.findChangelist(CL)
        self.assertEqual(cl.description, 'DO NOT COMMIT')
        self.assertEqual(len(cl), 2)
        self.assertEqual(CL, int(cl))
        self.assertEqual(P4CLIENT, cl.client)
        self.assertEqual('pending', cl.status)
        self.assertEqual(P4USER, cl.user)
        self.assertEqual(datetime.datetime(2017, 7, 3, 21, 4, 32), cl.time)
        self.assertEqual(repr(cl), '<Changelist {}>'.format(CL))

        assert cl[0].depotFile == '//p4_test/edit.txt'

        default = self._conn.findChangelist()

        with self.assertRaises(TypeError):
            'foo' in cl

        for r in cl:
            pass

        cl.description = 'xxx'
        self.assertEqual(cl.description, 'xxx')

        with self._conn.findChangelist('testing') as cl:
            self.assertEqual(cl.description, 'testing')
            rev = self._conn.ls('//p4_test/synced.txt')[0]
            cl.append(rev)
            try:
                cl.append(r'C:/tmp/foo.txt')
            except errors.RevisionError:
                pass
            cl.append(TO_ADD)
            self.assertEqual(len(cl), 2)
            self.assertTrue(cl.isDirty)

        cl = self._conn.findChangelist('testing')
        self.assertEqual(len(cl), 2)
        rev = self._conn.ls('//p4_test/synced.txt')[0]
        rev.revert()
        cl.query()
        self.assertEqual(len(cl), 1)
        cl.revert()
        self.assertEqual(len(cl), 0)

        cl.delete()

        cl = self._conn.findChangelist('submitting')
        with cl:
            rev = self._conn.ls('//p4_test/submit.txt')[0]
            cl.append(rev)
            with open(rev.clientFile, 'w+') as fh:
                s = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(64))
                fh.write(s)

        cl.submit()

def test_reopen():
    c = Connection(port=P4PORT, client=P4CLIENT, user=P4USER)
    rev = c.ls('//p4_test/synced.txt')[0]

    default = c.findChangelist()
    default.append(rev)
    default.save()
    assert len(default) == 1

    cl = c.findChangelist('testing')
    cl.append(rev)
    cl.save()
    assert len(cl) == 1

    cl2 = c.findChangelist('testing2')
    cl2.append(rev)
    cl2.save()
    assert len(cl2) == 1
    #assert len(cl) == 0
    rev.revert()
    assert len(cl2) == 0
    cl.delete()
    cl2.delete()

def test_descriptions():
    c = Connection(port=P4PORT, client=P4CLIENT, user=P4USER)

    cl = c.findChangelist('testing')
    assert cl.description == 'testing'
    cl.delete()

    cl = c.findChangelist('this\nis\nmultiline')
    assert format(cl).endswith('Client: p4_unit_tests\n\nUser:   p4test\n\nStatus: pending\n\nDescription:\n\tthis\n\tis\n\tmultiline\n\t\n\nFiles:\n\n')
    cl.delete()

    cl = c.findChangelist('this\nis\nmultiline\n\n')
    assert format(cl).endswith('Client: p4_unit_tests\n\nUser:   p4test\n\nStatus: pending\n\nDescription:\n\tthis\n\tis\n\tmultiline\n\t\n\nFiles:\n\n')
    cl.delete()

    cl1 = c.findChangelist('this\nis\n\nmultiline')
    cl2 = c.findChangelist('this\nis\n\nmultiline')
    assert cl1 == cl2
    cl1.delete()


# def test_changelist_object():
#     c = Connection(port=P4PORT, client=P4CLIENT, user=P4USER)
#     cl = Changelist(c, 145)
#     assert len(cl) == 1
#     assert cl[0].isEdit is False
#
#     os.chdir(r'E:\Users\brett\Perforce\p4_unit_tests_alt\p4_test')
#     os.environ['P4CONFIG'] = '.p4config'
#     cl = Changelist(145)
#     assert len(cl) == 1
#     assert cl[0].isEdit == False
#     os.environ['P4CONFIG'] = ''
#
#
def test_iadd():
    c = Connection(port=P4PORT, client=P4CLIENT, user=P4USER)
    cl = c.findChangelist('iadd')
    files = c.ls('//p4_test/s...', exclude_deleted=True)
    cl += files
    assert len(cl) == 2
    cl.delete()
