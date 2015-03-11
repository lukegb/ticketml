#!/usr/bin/python2
# vim:fileencoding=utf-8

# Copyright (c) 2015 the TicketML authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE.md file.

import enum
import lxml.etree

on_off_enum = enum.Enum('ON', 'OFF')

EMPHASIS = on_off_enum
DOUBLE_HEIGHT = on_off_enum
DOUBLE_WIDTH = on_off_enum
UNDERLINE = on_off_enum

ALIGNMENT = enum.Enum('LEFT', 'CENTER', 'RIGHT')

BARCODE_TYPE = enum.Enum('UPCA', 'UPCE', 'JAN13', 'JAN8', 'CODE39', 'ITF', 'CODABAR', 'CODE128', 'CODE93')
BARCODE_HRI_POSITION = enum.Enum('NONE', 'ABOVE', 'BELOW', 'BOTH')

def set_or_clear_bit(data, bit, new_value):
    new_value = bool(new_value)
    if new_value:
        data = data | (1 << bit)
    else:
        data = data & ~(1 << bit)
    return data

class BaseBackend(object):
    ALIGNMENT_LEFT = 0
    ALIGNMENT_CENTER = 1
    ALIGNMENT_RIGHT = 2
    ALIGNMENT_LOOKUP = {
        ALIGNMENT.LEFT: ALIGNMENT_LEFT,
        ALIGNMENT.CENTER: ALIGNMENT_CENTER,
        ALIGNMENT.RIGHT: ALIGNMENT_RIGHT,
    }

    CODEPAGE = 'cp437'

    BARCODE_HRI_POSITION_MAP = {
        BARCODE_HRI_POSITION.NONE: 0,
        BARCODE_HRI_POSITION.ABOVE: 1,
        BARCODE_HRI_POSITION.BELOW: 2,
        BARCODE_HRI_POSITION.BOTH: 3,
    }

    BASE_CHARS_PER_LINE = 48

    def _start_print_barcode(self, barcode_type, hri_posn, barcode_height):
        if barcode_type not in self.BARCODE_MAP:
            raise Exception('unacceptable barcode type: {}'.format(barcode_type))
        barcode_type_byte = self.BARCODE_MAP[barcode_type]

        if hri_posn not in self.BARCODE_HRI_POSITION_MAP:
            raise Exception('unacceptable barcode HRI position: {}'.format(barcode_type))
        hri_posn_byte = self.BARCODE_HRI_POSITION_MAP[hri_posn]

        assert 1 <= barcode_height <= 255, "barcode height must be between 1 and 255"

        self._serial.write('1d48'.decode('hex') + chr(hri_posn_byte))
        self._serial.write('1d68'.decode('hex') + chr(barcode_height))

        return barcode_type_byte

    def _set_alignment(self, new_mode):
        self._serial.write('1b61'.decode('hex') + chr(new_mode))

    def set_alignment(self, alignment):
        if alignment not in self.ALIGNMENT_LOOKUP:
            raise KeyError('unknown alignment {}'.format(alignment))
        self._set_alignment(self.ALIGNMENT_LOOKUP[alignment])


    def set_font_size(self, width, height):
        assert 1 <= width <= 8, "width must be between 1 and 8"
        assert 1 <= height <= 8, "height must be between 1 and 8"

        hex = '{}{}'.format(width-1, height-1)

        self._serial.write(('1d21' + hex).decode('hex'))

    def get_characters_per_line(self, font_width):
        return self.BASE_CHARS_PER_LINE / font_width

class Ibm4610Backend(object):
    BARCODE_MAP = {
        BARCODE_TYPE.UPCA: 0,
        BARCODE_TYPE.UPCE: 1,
        BARCODE_TYPE.JAN13: 2,
        BARCODE_TYPE.JAN8: 3,
        BARCODE_TYPE.CODE39: 4,
        BARCODE_TYPE.ITF: 5,
        BARCODE_TYPE.CODABAR: 6,
        BARCODE_TYPE.CODE93: 8,
        BARCODE_TYPE.CODE128: 7,
    }

    def __init__(self, serial):
        self._serial = serial

        self._set_alignment(self.ALIGNMENT_LEFT)

    def set_emphasis(self, on_off):
        self._serial.write('1b47'.decode('hex') + chr(int(bool(on_off == EMPHASIS.ON))))

    def set_double_height(self, on_off):
        self._serial.write('1b68'.decode('hex') + chr(int(bool(on_off == DOUBLE_HEIGHT.ON))))

    def set_double_width(self, on_off):
        self._serial.write('1b57'.decode('hex') + chr(int(bool(on_off == DOUBLE_WIDTH.ON))))

    def set_underline(self, on_off):
        self._serial.write('1b2d'.decode('hex') + chr(int(bool(on_off == UNDERLINE.ON))))


    def print_text(self, text):
        self._serial.write(text.encode(self.CODEPAGE))

    def print_logo(self, logo_num):
        self._serial.write('\n')
        self._serial.write('1d2f00'.decode('hex') + chr(logo_num))

    def print_barcode(self, barcode_type, barcode_data, hri_posn, barcode_height):
        barcode_type_byte = self._start_print_barcode(barcode_type, hri_posn, barcode_height)
        self._serial.write('\n')
        self._serial.write('1d6b'.decode('hex') + chr(barcode_type_byte) + barcode_data + chr(0))

    def feed_and_cut(self):
        self._serial.write('0c'.decode('hex'))

class CbmBackend(BaseBackend):
    EMPHASIS_BIT = 3
    DOUBLE_HEIGHT_BIT = 4
    DOUBLE_WIDTH_BIT = 5
    UNDERLINE_BIT = 7

    ALIGNMENT_LEFT = 0
    ALIGNMENT_CENTER = 1
    ALIGNMENT_RIGHT = 2
    ALIGNMENT_LOOKUP = {
        ALIGNMENT.LEFT: ALIGNMENT_LEFT,
        ALIGNMENT.CENTER: ALIGNMENT_CENTER,
        ALIGNMENT.RIGHT: ALIGNMENT_RIGHT,
    }

    BARCODE_MAP = {
        BARCODE_TYPE.UPCA: 65,
        BARCODE_TYPE.UPCE: 66,
        BARCODE_TYPE.JAN13: 67,
        BARCODE_TYPE.JAN8: 68,
        BARCODE_TYPE.CODE39: 69,
        BARCODE_TYPE.ITF: 70,
        BARCODE_TYPE.CODABAR: 71,
        BARCODE_TYPE.CODE93: 72,
        BARCODE_TYPE.CODE128: 73,
    }
    BARCODE_HRI_POSITION_MAP = {
        BARCODE_HRI_POSITION.NONE: 0,
        BARCODE_HRI_POSITION.ABOVE: 1,
        BARCODE_HRI_POSITION.BELOW: 2,
        BARCODE_HRI_POSITION.BOTH: 3,
    }

    CODEPAGE = 'cp437'

    def __init__(self, serial):
        self._serial = serial

        self._set_printing_mode(0)
        self._set_alignment(self.ALIGNMENT_LEFT)

    def _set_printing_mode(self, new_mode):
        self._printing_mode = new_mode
        self._serial.write('1b21'.decode('hex') + chr(new_mode))

    def _set_printing_mode_bit(self, bit, new_state):
        self._set_printing_mode(set_or_clear_bit(self._printing_mode, bit, new_state))

    def set_emphasis(self, on_off):
        self._set_printing_mode_bit(self.EMPHASIS_BIT, on_off == EMPHASIS.ON)

    def set_double_height(self, on_off):
        self._set_printing_mode_bit(self.DOUBLE_HEIGHT_BIT, on_off == DOUBLE_HEIGHT.ON)

    def set_double_width(self, on_off):
        self._set_printing_mode_bit(self.DOUBLE_WIDTH_BIT, on_off == DOUBLE_WIDTH.ON)

    def set_underline(self, on_off):
        self._set_printing_mode_bit(self.UNDERLINE_BIT, on_off == UNDERLINE.ON)


    def print_text(self, text):
        self._serial.write(text.encode(self.CODEPAGE))

    def print_logo(self, logo_num):
        self._serial.write('\n')
        self._serial.write('1c70'.decode('hex') + chr(logo_num) + '00'.decode('hex'))

    def print_barcode(self, barcode_type, barcode_data, hri_posn, barcode_height):
        barcode_type_byte = self._start_print_barcode(barcode_type, hri_posn, barcode_height)
        self._serial.write('\n')
        self._serial.write('1d6b'.decode('hex') + chr(barcode_type_byte) + chr(len(barcode_data)) + barcode_data)

    def feed_and_cut(self):
        self._serial.write('\n\n\n\n' + '1d5601'.decode('hex'))

class TicketML(object):
    NO_PRINT_CONTENT = {
        'barcode': True,
        'sensibreak': True,
    }

    def __init__(self, tree):
        self.tree = tree
        self.stack = [{
            'emphasis': EMPHASIS.OFF,
            'double_height': DOUBLE_HEIGHT.OFF,
            'double_width': DOUBLE_WIDTH.OFF,
            'underline': UNDERLINE.OFF,

            'alignment': ALIGNMENT.LEFT,

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
                self.print_text(elem.text)
            elif action == 'end' and elem.tail:
                self.print_text(elem.tail)

    def print_text(self, text):
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
        self._set_state(action, elem, 'emphasis', EMPHASIS.ON)

    def handle_u(self, action, elem):
        self._set_state(action, elem, 'underline', UNDERLINE.ON)

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
        txt = elem.text.replace('\r', '').replace('\n', '')
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
                print "altered", block, "to", before, "[and]", after
                made_changes = True
            txt = new_txt

        self.backend.print_text('\n'.join(txt))

    def handle_align(self, action, elem):
        new_posn = elem.get('mode')
        if new_posn is None:
            raise Exception('align "mode" property must be set')
        posns = {
            'left': ALIGNMENT.LEFT,
            'center': ALIGNMENT.CENTER,
            'right': ALIGNMENT.RIGHT,
        }
        if new_posn not in posns:
            raise Exception('unrecognized alignment "{}"'.format(new_posn))

        self._set_state(action, elem, 'alignment', posns[new_posn])

    def handle_br(self, action, elem):
        if action == 'end':
            self.backend.print_text('\n')

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

        hriposns = dict(above=BARCODE_HRI_POSITION.ABOVE, below=BARCODE_HRI_POSITION.BELOW, none=BARCODE_HRI_POSITION.NONE, both=BARCODE_HRI_POSITION.BOTH)
        hri_position = hriposns[elem.get('hriposition', 'below')]

        barcode_types = {
            'UPC-A': BARCODE_TYPE.UPCA,
            'UPC-E': BARCODE_TYPE.UPCE,
            'JAN13': BARCODE_TYPE.JAN13,
            'EAN13': BARCODE_TYPE.JAN13,
            'JAN8': BARCODE_TYPE.JAN8,
            'EAN8': BARCODE_TYPE.JAN8,
            'CODE39': BARCODE_TYPE.CODE39,
            'ITF': BARCODE_TYPE.ITF,
            'CODABAR': BARCODE_TYPE.CODABAR,
            'CODE93': BARCODE_TYPE.CODE93,
            'CODE128': BARCODE_TYPE.CODE128,
        }
        barcode_type = barcode_types[elem.get('type', 'CODE93')]

        barcode_height = int(elem.get('height', '12'))

        barcode_data = elem.text.strip()

	self.backend.print_barcode(barcode_type, barcode_data, hri_position, barcode_height)
