# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# fade.py - Fade objects in or out
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.1  2004/08/27 14:15:25  dischi
# split animations into different files
#
#
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

__all__ = [ 'FadeAnimation' ]

from base import BaseAnimation

class FadeAnimation(BaseAnimation):
    """
    Animation class to fade objects in or out. The alpha value of each
    object is set to 'start' and than moved to 'stop' with the given
    framerate.
    """
    def __init__(self, objects, frames, start, stop, fps=25):
        BaseAnimation.__init__(self, fps)
        self.objects     = objects
        self.max_frames  = max(frames, 1)
        self.frame       = 0
        self.diff        = stop - start
        self.start_alpha = start
        # make sure all objects are visible
        map(lambda o: o.show(), objects)
        # set start alpha value to all objects
        map(lambda o: o.set_alpha(start), objects)


    def update(self):
        """
        update the animation
        """
        self.frame += 1
        # calculate the new alpha
        diff = int(self.frame * (float(self.diff) / self.max_frames))
        alpha = self.start_alpha + diff
        # set new alpha
        map(lambda o: o.set_alpha(alpha), self.objects)
        if self.frame == self.max_frames:
            # remove animation when done
            self.remove()
            if self.start_alpha - self.diff == 0:
                # hide objects from the screen if the now have alpha == 0
                # Also restore the alpha so they can be shown again
                if self.start_alpha == 255:
                    map(lambda o: o.set_alpha(255), objects)
                map(lambda o: o.hide, objects)


    def finish(self):
        """
        finish the animation
        """
        self.frame = self.max_frames - 1
        self.update()
        BaseAnimation.finish(self)