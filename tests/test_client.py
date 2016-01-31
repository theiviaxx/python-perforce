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

from perforce.models import Client, Connection
from perforce import errors


def test_client_properties():
    con = Connection(port='127.0.0.1:1666', user='p4test')
    c = Client('p4test_stream', con)

    assert c.client == 'p4test_stream'
    assert c.root == r'C:\Users\brett\Perforce\p4test_stream'
    assert c.owner == 'p4test'
    assert c.view == ['//stream_test/main/... //p4test_stream/...']
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

