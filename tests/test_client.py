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


def test_client_properties():
    con = Connection(port='127.0.0.1:1666', user='p4test')
    c = Client('p4test_stream', con)

    assert c.client == 'p4test_stream'
    assert c.root == r'C:\Users\brett\Perforce\p4test_stream'
    assert c.owner == 'p4test'
    assert c.view[0].depot == '//stream_test/main/...'
    assert c.view[0].client == '//p4test_stream/...'
    assert c.stream == '//stream_test/main'
    assert isinstance(c.access, datetime.datetime)

    with pytest.raises(errors.ConnectionError):
        c = Client('p4_unit_tests')

    os.chdir(r'C:\Users\brett\Perforce\p4_unit_tests_alt\p4_test')
    os.environ['P4CONFIG'] = '.p4config'
    c = Client('p4_unit_tests')
    assert c.client == 'p4_unit_tests'
    assert c.stream is None
    os.environ['P4CONFIG'] = ''

    c.client = 'p4test_stream'
    assert c.client == 'p4test_stream'

def test_stream_properties():
    con = Connection(port='127.0.0.1:1666', user='p4test')
    s = Stream('//stream_test/main', con)

    assert s.stream == '//stream_test/main'
    assert s.name == 'main'
    assert s.owner == 'p4test'
    assert s.type == 'mainline'
    assert s.description == 'Created by p4test.'
    assert s.view[0].depot == '//stream_test/main/...'
    assert s.view[0].client == '...'
    assert isinstance(s.access, datetime.datetime)
