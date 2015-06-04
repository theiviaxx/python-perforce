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


TO_ADD = path.path(r"C:\work\p4_test\p4_test\toadd.txt")


class ChangelistTests(unittest.TestCase):
    def setUp(self):
        self._conn = connection.Connection(port='127.0.0.1:1666', client='p4_unit_test', user='bdixon')

    def test_changelist(self):
        cl = self._conn.findChangelist(40)
        self.assertEqual(cl.description, 'DO NOT COMMIT')
        self.assertEqual(len(cl), 1)
        self.assertEqual(40, int(cl))
        self.assertEqual('p4_unit_test', cl.client)
        self.assertEqual('pending', cl.status)
        self.assertEqual('bdixon', cl.user)
        self.assertEqual(datetime.datetime(2015, 4, 13, 22, 36, 27), cl.time)

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
            self._conn.add(TO_ADD, cl)
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



if __name__ == '__main__':
    unittest.main()