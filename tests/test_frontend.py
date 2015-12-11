#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 the TicketML authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE.md file.

from __future__ import division, absolute_import, print_function, unicode_literals

import ticketml
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

    @raises(UnicodeEncodeError)
    def test_print_text_fails_with_unencodable_text(self):
        self.mock_serial.reset_mock()
        self.backend.print_text('ルーク')


class TicketMLTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TicketMLTests, self).__init__(*args, **kwargs)
        self.ticketml = ticketml.TicketML(None)
        self.backend = mock.MagicMock()
        self.ticketml.backend = self.backend

    def test_passes_through_unicode(self):
        self.ticketml.print_text(u"hello")
        self.backend.print_text.assert_called_once_with(u"hello")
        self.assertTrue(isinstance(self.backend.print_text.call_args[0][0], type(u"")))

    @raises(TypeError)
    def test_rejects_bytes(self):
        self.ticketml.print_text(b"hello")


class CbmBackendTests(BackendMixin, unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CbmBackendTests, self).__init__(*args, **kwargs)
        self.backend = ticketml.CbmBackend(self.mock_serial)

    def test_init_sets_default_printing_mode(self):
        self.mock_serial.write.assert_any_call(b'\x1b!\x00')  # sets printing mode to 0


class Ibm4610BackendTests(BackendMixin, unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(Ibm4610BackendTests, self).__init__(*args, **kwargs)
        self.backend = ticketml.Ibm4610Backend(self.mock_serial)
