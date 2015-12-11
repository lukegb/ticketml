#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 the TicketML authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE.md file.

from __future__ import division, absolute_import, print_function, unicode_literals

import ticketml
from ticketml.ticketml import Emphasis, Alignment
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock
from nose.tools import *


class BackendMixin(object):
    def __init__(self, *args, **kwargs):
        super(BackendMixin, self).__init__(*args, **kwargs)
        self.mock_serial = mock.MagicMock()

    def test_init_sets_left_alignment(self):
        self.mock_serial.write.assert_any_call(b'\x1ba\x00')  # sets alignment to left

    def test_print_text_prints_text(self):
        self.mock_serial.reset_mock()
        self.backend.print_text('ASDF')
        self.mock_serial.write.assert_called_once_with(b'ASDF')

    def test_print_text_encodes_as_cp850(self):
        self.mock_serial.reset_mock()
        self.backend.print_text('£')
        self.mock_serial.write.assert_called_once_with(b'\x9c')

    def test_cut_considered_as_linebreak(self):
        self.backend.print_text('hi')
        self.backend.feed_and_cut()
        self.assertTrue(self.backend._at_linebreak)
        self.mock_serial.reset_mock()
        self.backend.set_alignment(Alignment.right)
        self.assertTrue(self.mock_serial.write.called)
        self.assertTrue(self.backend._at_linebreak)

    @raises(UnicodeEncodeError)
    def test_print_text_fails_with_unencodable_text(self):
        self.mock_serial.reset_mock()
        self.backend.print_text('ルーク')


class CbmBackendTests(BackendMixin, unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CbmBackendTests, self).__init__(*args, **kwargs)
        self.backend = ticketml.CbmBackend(self.mock_serial)

    def test_init_sets_default_printing_mode(self):
        self.mock_serial.write.assert_any_call(b'\x1b!\x00')  # sets printing mode to 0

    def test_printing_mode_change_midline(self):
        self.backend.print_text('hello')
        self.backend.set_emphasis(Emphasis.on)
        self.mock_serial.write.assert_any_call(b'\x1b!\x08')  # sets printing mode to 0


class Ibm4610BackendTests(BackendMixin, unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(Ibm4610BackendTests, self).__init__(*args, **kwargs)
        self.backend = ticketml.Ibm4610Backend(self.mock_serial)
