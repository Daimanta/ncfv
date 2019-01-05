#! /usr/bin/env python

#    test_stringops.py - tests of ncfv string operations
#    Copyright (C) 2005  Matthew Mueller <donut AT dakotacom DOT net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from unittest import TestCase

from ncfv.strutil import uwidth, lchoplen, rchoplen


class uwidthTestCase(TestCase):
    def test_simple(self):
        self.assertEqual(uwidth(u'hello world'), 11)

    def test_nonspacing(self):
        self.assertEqual(uwidth(u'\0'), 0)
        self.assertEqual(uwidth(u'\u200b'), 0)
        self.assertEqual(uwidth(u'\u3099'), 0)
        self.assertEqual(uwidth(u'\u0327'), 0)

    def test_wide(self):
        self.assertEqual(uwidth(u'\u3053\u3093\u306b\u3061\u306f'), 10)
        self.assertEqual(uwidth(u'\u304c\u304e\u3050\u3052\u3054'), 10)
        self.assertEqual(uwidth(u'\u304b\u3099\u304d\u3099\u304f\u3099\u3051\u3099\u3053\u3099'), 10)

    def test_halfwidth(self):
        self.assertEqual(uwidth(u'\uFF79'), 1)
        self.assertEqual(uwidth(u'\uFF73\uFF79\uFF79\uFF79'), 4)

    def test_compose_noprecombined(self):
        self.assertEqual(uwidth(
            u'\u01b5\u0327\u0308\u01b6\u0327\u0308\u01b7\u0327\u0308\u01b8\u0327\u0308\u01b9\u0327\u0308\u01ba\u0327\u0308'),
            6)


class chopTestCase(TestCase):
    def test_lchoplen_simple(self):
        print(lchoplen('hello world', 10))
        self.assertEqual('hello world', lchoplen('hello world', 12))
        self.assertEqual('hello world', lchoplen('hello world', 11))
        self.assertEqual('...o world', lchoplen('hello world', 10))
        self.assertEqual('...', lchoplen('hello world', 3))

    def test_rchoplen_simple(self):
        self.assertEqual(rchoplen(u'hello world', 12), u'hello world')
        self.assertEqual(rchoplen(u'hello world', 11), u'hello world')
        self.assertEqual(rchoplen(u'hello world', 10), u'hello w...')
        self.assertEqual(rchoplen(u'hello world', 3), u'...')

    def test_lchoplen_wide(self):
        self.assertEqual('\u3053\u3093\u306b\u3061\u306f', lchoplen('\u3053\u3093\u306b\u3061\u306f', 8))
        self.assertEqual('\u3053\u3093\u306b\u3061\u306f', lchoplen('\u3053\u3093\u306b\u3061\u306f', 5))
        self.assertEqual('...\u306f', lchoplen('\u3053\u3093\u306b\u3061\u306f', 4))
        self.assertEqual('...', lchoplen('\u3053\u3093\u306b\u3061\u306f', 3))

    def test_rchoplen_wide(self):
        self.assertEqual(rchoplen(u'\u3053\u3093\u306b\u3061\u306f', 8), u'\u3053\u3093\u306b\u3061\u306f')
        self.assertEqual(rchoplen(u'\u3053\u3093\u306b\u3061\u306f', 5), u'\u3053\u3093\u306b\u3061\u306f')
        self.assertEqual(rchoplen(u'\u3053\u3093\u306b\u3061\u306f', 4), u'\u3053...')
        self.assertEqual(rchoplen(u'\u3053\u3093\u306b\u3061\u306f', 3), u'...')

if __name__ == '__main__':
    ncfvtest.main()
