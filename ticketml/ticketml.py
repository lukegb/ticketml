#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 the TicketML authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE.md file.

from __future__ import division, absolute_import, print_function, unicode_literals

import lxml.etree
from enum import Enum
import binascii
import sys

def make_unicode(s):
    if isinstance(s, type(u"")):
        return s
    return s.decode('utf-8')

class Emphasis(Enum):
    on = True
    off = False

class DoubleHeight(Enum):
    on = True
    off = False

class DoubleWidth(Enum):
    on = True
    off = False

class Underline(Enum):
    on = True
    off = False

class Alignment(Enum):
    left = 1
    center = 2
    right = 3

class BarcodeType(Enum):
    upc_a = 1
    upc_e = 2
    jan_13 = 3
    jan_8 = 4
    code_39 = 5
    itf = 6
    codabar = 7
    code_128 = 8
    code_93 = 9

class BarcodeHriPosition(Enum):
    none = 0
    above = 1
    below = 2
    both = 3

def set_or_clear_bit(data, bit, new_value):
    new_value = bool(new_value)
    if new_value:
        data = data | (1 << bit)
    else:
        data = data & ~(1 << bit)
    return data

def h2b(hchars):
    return binascii.unhexlify(hchars)

if sys.version < '3':
    bchr = chr
else:
    def bchr(bdata):
        return bytes([bdata])

class BaseBackend(object):
    ALIGNMENT_LEFT = 0
    ALIGNMENT_CENTER = 1
    ALIGNMENT_RIGHT = 2
    ALIGNMENT_LOOKUP = {
        Alignment.left: ALIGNMENT_LEFT,
        Alignment.center: ALIGNMENT_CENTER,
        Alignment.right: ALIGNMENT_RIGHT,
    }

    CODEPAGE = 'cp437'

    BarcodeHriPosition_MAP = {
        BarcodeHriPosition.none: 0,
        BarcodeHriPosition.above: 1,
        BarcodeHriPosition.below: 2,
        BarcodeHriPosition.both: 3,
    }

    BASE_CHARS_PER_LINE = 48

    def _start_print_barcode(self, barcode_type, hri_posn, barcode_height):
        if barcode_type not in self.BARCODE_MAP:
            raise Exception('unacceptable barcode type: {}'.format(barcode_type))
        barcode_type_byte = self.BARCODE_MAP[barcode_type]

        if hri_posn not in self.BarcodeHriPosition_MAP:
            raise Exception('unacceptable barcode HRI position: {}'.format(barcode_type))
        hri_posn_byte = self.BarcodeHriPosition_MAP[hri_posn]

        assert 1 <= barcode_height <= 255, "barcode height must be between 1 and 255"

        self._write_immediately(h2b(b'1d48') + bchr(hri_posn_byte))
        self._write_immediately(h2b(b'1d68') + bchr(barcode_height))

        return barcode_type_byte

    def _set_alignment(self, new_mode):
        self._write_at_linebreak(h2b(b'1b61') + bchr(new_mode))

    def set_alignment(self, alignment):
        if alignment not in self.ALIGNMENT_LOOKUP:
            raise KeyError('unknown alignment {}'.format(alignment))
        self._set_alignment(self.ALIGNMENT_LOOKUP[alignment])


    def set_font_size(self, width, height):
        assert 1 <= width <= 8, "width must be between 1 and 8"
        assert 1 <= height <= 8, "height must be between 1 and 8"

        hex = '{}{}'.format(width-1, height-1)

        self._write_immediately(h2b(b'1d21' + hex))

    def get_characters_per_line(self, font_width):
        return self.BASE_CHARS_PER_LINE // font_width

    def linebreak(self):
        self._write_immediately(b'\n')

    def _write_immediately(self, data):
        if self._on_next_linebreak and b'\n' in data:
            pre, ln, post = data.partition(b'\n')
            self._serial.write(pre + ln + self._on_next_linebreak + post)
            self._on_next_linebreak = b''
        else:
            self._serial.write(data)
        self._at_linebreak = data.endswith(b'\n')

    def _write_at_linebreak(self, data):
        if self._at_linebreak:
            self._serial.write(data)
        else:
            self._on_next_linebreak += data


class Ibm4610Backend(BaseBackend):
    BARCODE_MAP = {
        BarcodeType.upc_a: 0,
        BarcodeType.upc_e: 1,
        BarcodeType.jan_13: 2,
        BarcodeType.jan_8: 3,
        BarcodeType.code_39: 4,
        BarcodeType.itf: 5,
        BarcodeType.codabar: 6,
        BarcodeType.code_93: 8,
        BarcodeType.code_128: 7,
    }

    BASE_CHARS_PER_LINE = 44

    def __init__(self, serial):
        self._serial = serial
        self._on_next_linebreak = b''
        self._at_linebreak = True

        self._set_alignment(self.ALIGNMENT_LEFT)

    def set_emphasis(self, on_off):
        self._write_immediately(h2b(b'1b47') + bchr(int(bool(on_off == Emphasis.on))))

    def set_double_height(self, on_off):
        self._write_immediately(h2b(b'1b68') + bchr(int(bool(on_off == DoubleHeight.on))))

    def set_double_width(self, on_off):
        self._write_immediately(h2b(b'1b57') + bchr(int(bool(on_off == DoubleWidth.on))))

    def set_underline(self, on_off):
        self._write_immediately(h2b(b'1b2d') + bchr(int(bool(on_off == Underline.on))))


    def print_text(self, text):
        self._write_immediately(text.encode(self.CODEPAGE))

    def print_logo(self, logo_num):
        self._write_immediately(b'\n')
        self._write_immediately(h2b(b'1d2f00') + bchr(logo_num))

    def print_barcode(self, barcode_type, barcode_data, hri_posn, barcode_height):
        barcode_type_byte = self._start_print_barcode(barcode_type, hri_posn, barcode_height)
        self._write_immediately(b'\n')
        self._write_immediately(h2b(b'1d6b') + bchr(barcode_type_byte) + barcode_data.encode(self.CODEPAGE) + bchr(0))

    def feed_and_cut(self):
        self._write_immediately(h2b(b'0c'))

class CbmBackend(BaseBackend):
    EMPHASIS_BIT = 3
    DOUBLEHEIGHT_BIT = 4
    DOUBLEWIDTH_BIT = 5
    UNDERLINE_BIT = 7

    ALIGNMENT_LEFT = 0
    ALIGNMENT_CENTER = 1
    ALIGNMENT_RIGHT = 2
    ALIGNMENT_LOOKUP = {
        Alignment.left: ALIGNMENT_LEFT,
        Alignment.center: ALIGNMENT_CENTER,
        Alignment.right: ALIGNMENT_RIGHT,
    }

    BARCODE_MAP = {
        BarcodeType.upc_a: 65,
        BarcodeType.upc_e: 66,
        BarcodeType.jan_13: 67,
        BarcodeType.jan_8: 68,
        BarcodeType.code_39: 69,
        BarcodeType.itf: 70,
        BarcodeType.codabar: 71,
        BarcodeType.code_93: 72,
        BarcodeType.code_128: 73,
    }
    BarcodeHriPosition_MAP = {
        BarcodeHriPosition.none: 0,
        BarcodeHriPosition.above: 1,
        BarcodeHriPosition.below: 2,
        BarcodeHriPosition.both: 3,
    }

    CODEPAGE = 'cp437'

    def __init__(self, serial):
        self._serial = serial
        self._on_next_linebreak = b''
        self._at_linebreak = True

        self._set_printing_mode(0)
        self._set_alignment(self.ALIGNMENT_LEFT)

    def _set_printing_mode(self, new_mode):
        self._printing_mode = new_mode
        self._write_at_linebreak(h2b(b'1b21') + bchr(new_mode))

    def _set_printing_mode_bit(self, bit, new_state):
        self._set_printing_mode(set_or_clear_bit(self._printing_mode, bit, new_state))

    def set_emphasis(self, on_off):
        self._set_printing_mode_bit(self.EMPHASIS_BIT, on_off == Emphasis.on)

    def set_double_height(self, on_off):
        self._set_printing_mode_bit(self.DOUBLEHEIGHT_BIT, on_off == DoubleHeight.on)

    def set_double_width(self, on_off):
        self._set_printing_mode_bit(self.DOUBLEWIDTH_BIT, on_off == DoubleWidth.on)

    def set_underline(self, on_off):
        self._set_printing_mode_bit(self.UNDERLINE_BIT, on_off == Underline.on)


    def print_text(self, text):
        self._write_immediately(text.encode(self.CODEPAGE))

    def print_logo(self, logo_num):
        self._write_immediately(b'\n')
        self._write_immediately(h2b(b'1c70') + bchr(logo_num) + h2b(b'00'))

    def print_barcode(self, barcode_type, barcode_data, hri_posn, barcode_height):
        barcode_type_byte = self._start_print_barcode(barcode_type, hri_posn, barcode_height)
        self._write_immediately(b'\n')
        self._write_immediately(h2b(b'1d6b') + bchr(barcode_type_byte) + bchr(len(barcode_data)) + barcode_data.encode(self.CODEPAGE))

    def feed_and_cut(self):
        self._write_immediately(b'\n\n\n\n' + h2b(b'1d5601'))

class TicketML(object):
    NO_PRINT_CONTENT = {
        'barcode': True,
        'sensibreak': True,
    }

    def __init__(self, tree):
        self.tree = tree
        self.stack = [{
            'emphasis': Emphasis.off,
            'double_height': DoubleHeight.off,
            'double_width': DoubleWidth.off,
            'underline': Underline.off,

            'alignment': Alignment.left,

            'font_width': 1,
            'font_height': 1,
        }]

    @classmethod
    def parse(cls, xml):
        return cls(lxml.etree.fromstring(xml))

    def go(self, context, backend):
        self.backend = backend

        tree = lxml.etree.iterwalk(self.tree, events=("start", "end"))

        for action, elem in tree:
            if elem.tag == lxml.etree.Comment:
                continue # uninterested

            handler_name = 'handle_{}'.format(elem.tag)
            handler = getattr(self, handler_name, None)
            if handler:
                handler(action, elem)

            if action == 'start' and elem.text and not self.NO_PRINT_CONTENT.get(elem.tag, False):
                self.print_text(make_unicode(elem.text))
            elif action == 'end' and elem.tail:
                self.print_text(make_unicode(elem.tail))

    def print_text(self, text):
        if not isinstance(text, type(u"")):
            raise TypeError("input must be a unicode str")
        text = text.replace('\r', '').replace('\n', '')
        if not text:
            return
        self.backend.print_text(text)

    def new_state(self, change):
        new_state = dict(self.stack[0])
        new_state.update(change)
        self.stack.insert(0, new_state)
        return new_state

    def pop_state(self):
        self.stack.pop(0)
        return self.stack[0]

    def _set_state(self, action, elem, property, enter_val):
        if action == 'start':
            new_state = self.new_state({ property: enter_val })
        elif action == 'end':
            new_state = self.pop_state()
        else:
            return

        getattr(self.backend, 'set_' + property)(new_state[property])

    def handle_b(self, action, elem):
        self._set_state(action, elem, 'emphasis', Emphasis.on)

    def handle_u(self, action, elem):
        self._set_state(action, elem, 'underline', Underline.on)

    def handle_font(self, action, elem):
        new_state_bit = {}

        if elem.get('width'):
            new_state_bit['font_width'] = int(elem.get('width'))
        if elem.get('height'):
            new_state_bit['font_height'] = int(elem.get('height'))

        if action == 'start':
            new_state = self.new_state(new_state_bit)
        elif action == 'end':
            new_state = self.pop_state()

        self.backend.set_font_size(new_state['font_width'], new_state['font_height'])

    def handle_sensibreak(self, action, elem):
        if action != 'end':
            return
 
        chars_per_line = self.backend.get_characters_per_line(self.stack[0]['font_width'])
        txt = make_unicode(elem.text).replace('\r', '').replace('\n', '')
        if len(txt) <= chars_per_line:
            self.print_text(txt)
            return

        # try to break this text intelligently:
        made_changes = True
        txt = [txt]
        while made_changes:
            made_changes = False
            new_txt = []
            for block in txt:
                if len(block) <= chars_per_line:
                    new_txt.append(block)
                    continue

                # find a space
                spacepos = block[:chars_per_line].rfind(' ')
                if spacepos == -1:
                    before = block[:chars_per_line]
                    after = block[chars_per_line+1:]
                else:
                    before = block[:spacepos]
                    after = block[spacepos+1:]
                new_txt.append(before)
                new_txt.append(after)
                made_changes = True
            txt = new_txt

        self.backend.print_text('\n'.join(txt))

    def handle_align(self, action, elem):
        new_posn = elem.get('mode')
        if new_posn is None:
            raise Exception('align "mode" property must be set')
        posns = {
            'left': Alignment.left,
            'center': Alignment.center,
            'right': Alignment.right,
        }
        if new_posn not in posns:
            raise Exception('unrecognized alignment "{}"'.format(new_posn))

        self._set_state(action, elem, 'alignment', posns[new_posn])

    def handle_br(self, action, elem):
        if action == 'end':
            self.backend.linebreak()

    def handle_ticket(self, action, elem):
        if action == 'end':
            self.backend.feed_and_cut()

    def handle_logo(self, action, elem):
        if action != 'end':
            return

        logo_num = elem.get('num')
        if logo_num is None:
            raise Exception('logo "num" property must be set')
        logo_num = int(logo_num)

        self.backend.print_logo(logo_num)

    def handle_barcode(self, action, elem):
        if action != 'end':
            return

        hriposns = dict(above=BarcodeHriPosition.above, below=BarcodeHriPosition.below, none=BarcodeHriPosition.none, both=BarcodeHriPosition.both)
        hri_position = hriposns[elem.get('hriposition', 'below')]

        barcode_types = {
            'UPC-A': BarcodeType.upc_a,
            'UPC-E': BarcodeType.upc_e,
            'JAN13': BarcodeType.jan_13,
            'EAN13': BarcodeType.jan_13,
            'JAN8': BarcodeType.jan_8,
            'EAN8': BarcodeType.jan_8,
            'CODE39': BarcodeType.code_39,
            'ITF': BarcodeType.itf,
            'CODABAR': BarcodeType.codabar,
            'CODE93': BarcodeType.code_93,
            'CODE128': BarcodeType.code_128,
        }
        barcode_type = barcode_types[elem.get('type', 'CODE93')]

        barcode_height = int(elem.get('height', '12'))

        barcode_data = make_unicode(elem.text).strip()

        self.backend.print_barcode(barcode_type, barcode_data, hri_position, barcode_height)
