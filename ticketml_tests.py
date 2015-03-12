#!/usr/bin/python2
# vim:fileencoding=utf-8

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


class CbmBackendTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CbmBackendTests, self).__init__(*args, **kwargs)
        self.mock_serial = mock.MagicMock()
        self.backend = ticketml.CbmBackend(self.mock_serial)

    def test_init_sets_default_printing_mode(self):
        print(self.mock_serial.write.call_args_list)
        self.mock_serial.write.assert_any_call(b'\x1b!\x00')  # sets printing mode to 0

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
    def test_print_text_fails_With_unencodable_text(self):
        self.mock_serial.reset_mock()
        self.backend.print_text('ルーク')
