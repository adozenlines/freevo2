# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# progress_area.py - A progress bar for a playing item
# -----------------------------------------------------------------------------
# $Id$
#
# This file includes a simple area for showing a progressbar of a playing
# item.
#
# TODO: make it possible to set stuff like colors in the theme fxd file
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002-2004 Krister Lagerstrom, Dirk Meyer, et al.
#
# Maintainer:    Dirk Meyer <dmeyer@tzi.de>
#
# Please see the file freevo/Docs/CREDITS for a complete list of authors.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------------

__all__ = [ 'ProgressArea' ]

from area import Area
from gui import Progressbar

class ProgressArea(Area):
    """
    An Area holding a progressbar about the current position of a playing
    item.
    """
    def __init__(self):
        Area.__init__(self, 'progress')
        self.bar = None
        self.__last_c = None


    def clear(self):
        """
        Clear all content objects
        """
        if self.bar:
            self.bar.unparent()
            self.bar = None


    def update(self):
        """
        Update the progressbar
        """
        content = self.calc_geometry(self.layout.content, copy_object=True)

        try:
            length = int(self.infoitem.info['length'])
        except Exception, e:
            _debug_(e, 0)
            length = 0
        start = 0
        if self.infoitem.info['start']:
            start = int(self.infoitem.info['start'])

        # get start pos
        pos = self.infoitem.elapsed - start

        if self.__last_c != (content.x, content.y, content.width,
                                content.height):
            if self.bar:
                self.bar.unparent()
            self.bar = Progressbar((content.x, content.y),
                                   (content.width, content.height),
                                   2, (0,0,0), (255, 255, 255, 95), 0,
                                   None, (0, 0, 150), 0, length)
            self.layer.add_child(self.bar)
            self.__last_c = content.x, content.y, content.width, \
                            content.height
        self.bar.set_bar_position(pos)