# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# tvstat.py - A small helper to get some information on your 
#             v4l2 and DVB devices.
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.1  2004/08/12 16:58:58  rshortt
# Run this helper to see how freevo autodetected your tv/dvb cards.  This will be changing slightly and will be a good tool to get debug information from users.
#
#
#
# -----------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2003 Krister Lagerstrom, et al. 
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

import time, string, sys

import config, tv.v4l2, tv.ivtv


def main():

    for key, card in config.TV_SETTINGS.items():
        print '\n*** %s ***' % key
        v4l2 = None

        if isinstance(card, config.IVTVCard):
            v4l2 = tv.ivtv.IVTV(card.vdev)
            print 'vdev: %s' % card.vdev

        elif isinstance(card, config.TVCard):
            v4l2 = tv.v4l2.Videodev(card.vdev)
            print 'vdev: %s' % card.vdev

        elif isinstance(card, config.DVBCard):
            print 'adapter: %s' % card.adapter


        if v4l2:
            v4l2.init_settings(key)
            v4l2.print_settings()
            v4l2.close()
    

if __name__ == '__main__':
    main()
