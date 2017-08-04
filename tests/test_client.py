#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_client
----------------------------------

Tests for `python-perforce` module.
"""

import os
import datetime

import pytest

from perforce.models import Client, Connection, Stream
from perforce import errors

P4PORT = 'DESKTOP-M97HMBQ:1666'
P4USER = 'p4test'
TEST_CLIENT = 'p4test_client_edits'


def test_client_properties():
    con = Connection(port=P4PORT, user=P4USER)
    c = Client('p4_unit_tests', con)

    assert c.client == 'p4_unit_tests'
    assert c.root == r'E:\Users\brett\Perforce\p4_unit_tests'
    assert c.owner == P4USER
    assert c.view[0].depot == '//p4_test/...'
    assert c.view[0].client == '//p4_unit_tests/p4_test/...'
    assert isinstance(c.access, datetime.datetime)

    c = Client(TEST_CLIENT)
    c.description = 'bar'
    assert c.description == 'bar'
    c.submitOptions = 'revertunchanged'
    assert c.submitOptions == 'revertunchanged'

    assert c._dirty is True
    c.save()
    assert c._dirty is False

    c = Client(TEST_CLIENT)
    assert c.description == 'bar'
    assert c.submitOptions == 'revertunchanged'

    c.description = 'foo'
    c.submitOptions = 'submitunchanged'
    c.save()

    # with pytest.raises(errors.ConnectionError):
    #     c = Client('p4_unit_tests')

    # os.chdir(r'E:\Users\brett\Perforce\p4_unit_tests_alt\p4_test')
    # os.environ['P4CONFIG'] = '.p4config'
    # c = Client('p4_unit_tests')
    # assert c.client == 'p4_unit_tests'
    # assert c.stream is None
    # os.environ['P4CONFIG'] = ''

# def test_client_properties():
#     con = Connection(port=P4PORT, user=P4USER)
#     c = Client('p4test_stream', con)
#
#     assert c.client == 'p4test_stream'
#     assert c.root == r'E:\Users\brett\Perforce\p4test_stream'
#     assert c.owner == P4USER
#     assert c.view[0].depot == '//stream_test/main/...'
#     assert c.view[0].client == '//p4test_stream/...'
#     assert c.stream == '//stream_test/main'
#     assert isinstance(c.access, datetime.datetime)
#
#     # with pytest.raises(errors.ConnectionError):
#     #     c = Client('p4_unit_tests')
#
#     os.chdir(r'E:\Users\brett\Perforce\p4_unit_tests_alt\p4_test')
#     os.environ['P4CONFIG'] = '.p4config'
#     c = Client('p4_unit_tests')
#     assert c.client == 'p4_unit_tests'
#     assert c.stream is None
#     os.environ['P4CONFIG'] = ''
#
#     c.client = 'p4test_stream'
#     assert c.client == 'p4test_stream'
#
#
# def test_stream_properties():
#     con = Connection(port=P4PORT, user=P4USER)
#     s = Stream('//stream_test/main', con)
#
#     assert s.stream == '//stream_test/main'
#     assert s.name == 'main'
#     assert s.owner == 'p4test'
#     assert s.type == 'mainline'
#     assert s.description == 'Created by p4test.'
#     assert s.view[0].depot == '//stream_test/main/...'
#     assert s.view[0].client == '...'
#     assert isinstance(s.access, datetime.datetime)
