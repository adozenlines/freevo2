# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# interface.py - interface between mediamenu and image
# -----------------------------------------------------------------------
# $Id$
#
# This file defines the PluginInterface for the image module
# of Freevo. It is loaded by __init__.py and will activate the
# mediamenu for images.
#
# Notes:
# Todo:
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.6  2004/09/13 19:32:46  dischi
# move the fxdhandler into an extra file
#
# Revision 1.5  2004/09/13 18:00:50  dischi
# last cleanups for the image module in Freevo

# -----------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002 Krister Lagerstrom, et al.
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
# ----------------------------------------------------------------------- */

# only export 'PluginInterface' to the outside. This will be used
# with plugin.activate('image') and everything else should be handled
# by using plugin.mimetype()
__all__ = [ 'PluginInterface' ]

# Add support for bins album files
from mmpython.image import bins

# Freevo imports
import config
import util
import plugin

# ImageItem
from imageitem import ImageItem

# fxdhandler for <slideshow> tags
from fxdhandler import fxdhandler

class PluginInterface(plugin.MimetypePlugin):
    """
    Plugin to handle all kinds of image items
    """
    def __init__(self):
        plugin.MimetypePlugin.__init__(self)
        self.display_type = [ 'image' ]

        # register the callbacks
        plugin.register_callback('fxditem', ['image'], 'slideshow', fxdhandler)

        # activate the mediamenu for image
        level = plugin.is_active('image')[2]
        plugin.activate('mediamenu', level=level, args='image')


    def suffix(self):
        """
        return the list of suffixes this class handles
        """
        return config.IMAGE_SUFFIX


    def get(self, parent, files):
        """
        return a list of items based on the files
        """
        items = []
        for file in util.find_matches(files, config.IMAGE_SUFFIX):
            items.append(ImageItem(file, parent))
            files.remove(file)
        return items


    def dirinfo(self, diritem):
        """
        set informations for a diritem based on album.xml
        """
        if vfs.isfile(diritem.dir + '/album.xml'):
            # Add album.xml information from bins to the
            # directory informations
            info  = bins.get_bins_desc(diritem.dir)
            if not info.has_key('desc'):
                return

            info = info['desc']
            if info.has_key('sampleimage') and info['sampleimage']:
                # Check if the album.xml defines a sampleimage.
                # If so, use it as image for the directory
                image = vfs.join(diritem.dir, info['sampleimage'])
                if vfs.isfile(image):
                    diritem.image = image

            # set the title from album.xml
            if info.has_key('title') and info['title']:
                diritem.name = info['title']