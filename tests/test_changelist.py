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

from perforce import connection
from perforce import changelist
from perforce import errors

# import wingdbstub


TO_ADD = path.path(r"C:\Users\brett\Perforce\p4_unit_tests\p4_test\to_add1.txt")


class ChangelistTests(unittest.TestCase):
    def setUp(self):
        self._conn = connection.Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')

    def test_changelist(self):
        cl = self._conn.findChangelist(173)
        self.assertEqual(cl.description, 'DO NOT COMMIT')
        self.assertEqual(len(cl), 1)
        self.assertEqual(173, int(cl))
        self.assertEqual('p4_unit_tests', cl.client)
        self.assertEqual('pending', cl.status)
        self.assertEqual('p4test', cl.user)
        self.assertEqual(datetime.datetime(2015, 9, 17, 22, 2, 41), cl.time)
        self.assertEqual(str(cl), '<Changelist 173>')

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

        del cl

        cl = self._conn.findChangelist('submitting')
        with cl:
            rev = self._conn.ls('//p4_test/submit.txt')[0]
            cl.append(rev)
            with open(rev.clientFile, 'w+') as fh:
                s = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(64))
                fh.write(s)
        
        cl.submit()

def test_reopen():
    c = connection.Connection(port='127.0.0.1:1666', client='p4_unit_tests', user='p4test')
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
    del cl
    del cl2



if __name__ == '__main__':
    unittest.main()