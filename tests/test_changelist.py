#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_python-perforce
----------------------------------

Tests for `python-perforce` module.
"""

import unittest
import datetime
import random
import string

import path

from perforce import Connection, Changelist
from perforce import errors

# import wingdbstub


TO_ADD = path.path(r"C:\Users\brett\Perforce\p4_unit_tests\p4_test\to_add1.txt")
CL = 398

class ChangelistTests(unittest.TestCase):
    def setUp(self):
        self._conn = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')

    def test_changelist(self):
        cl = self._conn.findChangelist(CL)
        self.assertEqual(cl.description, 'DO NOT COMMIT')
        self.assertEqual(len(cl), 1)
        self.assertEqual(CL, int(cl))
        self.assertEqual('p4_unit_tests', cl.client)
        self.assertEqual('pending', cl.status)
        self.assertEqual('p4test', cl.user)
        self.assertEqual(datetime.datetime(2015, 10, 1, 23, 6, 15), cl.time)
        self.assertEqual(str(cl), '<Changelist {}>'.format(CL))

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
    c = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
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
    c = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')

    cl = c.findChangelist('testing')
    assert cl.description == 'testing'
    cl.delete()

    cl = c.findChangelist('this\nis\nmultiline')
    assert format(cl).endswith('Client: p4_unit_tests\n\nUser:   p4test\n\nStatus: pending\n\nDescription:\n\tthis\n\tis\n\tmultiline\n\t\n\nFiles:\n\n')
    cl.delete()

    cl = c.findChangelist('this\nis\nmultiline\n\n')
    assert format(cl).endswith('Client: p4_unit_tests\n\nUser:   p4test\n\nStatus: pending\n\nDescription:\n\tthis\n\tis\n\tmultiline\n\t\n\nFiles:\n\n')
    cl.delete()

def test_changelist_object():
    c = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    cl = Changelist(c, 145)
    assert len(cl) == 1
    assert cl[0].isEdit == False


def test_iadd():
    c = Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
    cl = c.findChangelist('iadd')
    files = c.ls('//p4_test/s...', exclude_deleted=True)
    cl += files
    assert len(cl) == 2
    cl.delete()


if __name__ == '__main__':
    unittest.main()
