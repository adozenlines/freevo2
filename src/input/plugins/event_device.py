#if 0 /*
# -----------------------------------------------------------------------
# event_device.py - An event device (/dev/input/eventX) plugin for Freevo.
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.3  2004/10/06 18:52:52  dischi
# use REMOTE_MAP now and switch to new notifier code
#
# Revision 1.2  2004/09/30 02:16:20  rshortt
# -turned this into an InputPlugin type
# -use the new (old) keymap
# -remove EVDEV_KEYMAP
# -set/get device keycodes
# -request exclusive access to the event device
# -add EVDEV_NAME to make it easy for users to pick it from a list, at least
#  until we autodetect it.
#
# Revision 1.1  2004/09/25 04:45:51  rshortt
# A linux event input device plugin, still a work in progress but I am using
# this for my PVR-250 remote with a custom keymap.  You may find some input
# tools to modify the keymap at http://dl.bytesex.org/cvs-snapshots/input-20040421-115547.tar.gz .
# I will incorporate the keymap viewing & loading tool into a freevo helper
# program.  plugin.activate('input.event_device')
#
# Revision 1.2  2004/09/20 01:36:15  rshortt
# Some improvements David Benoit and I worked on.
#
# Revision 1.1  2004/09/01 17:36:43  rshortt
# Event input device support.  A work in progress / proof of concept.  With this
# we can totally bypass lirc if there's an event input driver for a given
# remote.
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
#endif
import notifier

import sys
import os
import select
import struct
import traceback
import fcntl
from time import sleep

import config
import plugin

#from input.linux_input import *
import input.linux_input as li
import input.evdev_keymaps as ek

from event import *


class PluginInterface(plugin.InputPlugin):

    def __init__(self):
        plugin.InputPlugin.__init__(self)

        self.plugin_name = 'EVDEV'
        self.device_name = config.EVDEV_DEVICE
        self.m_ignoreTill = 0
        self.m_ignore = config.EVDEV_REPEAT_IGNORE
        self.m_repeatRate = config.EVDEV_REPEAT_RATE
     
        if not self.device_name:
            print 'Input device plugin disabled, exiting.'
            return

        try:
            self.fd = os.open(self.device_name, 
                              os.O_RDONLY|os.O_NONBLOCK)
        except OSError:
            print 'Unable to open %s, exiting.' % self.device_name
            return

        exclusive = li.exclusive_access(self.fd)
        if exclusive != -1:
            print 'Freevo granted exclusive access to %s.' % self.device_name

        print 'Event device name: %s' % li.get_name(self.fd)

    
        print 'Using input device %s.' % self.device_name

        self.keymap = {}
        for key in config.REMOTE_MAP:
            if hasattr(li, 'KEY_%s' % key):
                code = getattr(li, 'KEY_%s' % key)
                self.keymap[code] = config.REMOTE_MAP[key]

        device_codes = ek.maps.get(config.EVDEV_NAME)
        for s, k in device_codes.items():
            print 'Adding key: 0x%04x = %3d' % (s, k)
            if not li.set_keycode(self.fd, s, k):
                print 'Failed to set key: 0x%04x = %3d' % (s, k)

        keymap = li.get_keymap(self.fd)
        print 'KEYCODES:'
        for s, k in keymap.items():
            print '    0x%04x = %3d' % (s, k)

        notifier.addSocket( self.fd, self.handle )


    def config(self):
        # XXX TODO: Autodetect which type of device it is so we don't need
        #           to set EVDEV_NAME, or have the user pick it from a list.
        #           Right now it is called something pretty to make it easier
        #           for users to choose the right one.

        return [
                ( 'EVDEV_NAME', 'Hauppauge PVR-250/350 IR remote', 'Long name of device.' ),
                ( 'EVDEV_DEVICE', '/dev/input/event0', 'Input device to use.' ),
                ( 'EVDEV_REPEAT_IGNORE', 500, 
                  'Time before first repeat (miliseconds).' ),
                ( 'EVDEV_REPEAT_RATE',   100, 
                  'Time between consecutive repeats (miliseconds).' ), ]


    def handle( self ):
        command = ''    
        c = os.read(self.fd, 16)

#struct input_event {
#        struct timeval time;
#        __u16 type;
#        __u16 code;
#        __s32 value;
#};
#struct timeval {
#        time_t          tv_sec;         /* seconds */ long
#        suseconds_t     tv_usec;        /* microseconds */ long
#};

#        S_EVDATA = '2l2Hi'
        S_EVDATA = '@llHHi'

        data = struct.unpack(S_EVDATA, c)

        # make that in milliseconds
        now = (data[0] * 1000) + (data[1] / 1000)
        type = data[2]
        code = data[3]
        value = data[4]

        print '  time: %d type=%04x code=%04x value=%08x' % (now, type, code, value)

        # was it a reset?  if so, ignore
        if type == 0 :
            # print '  ignoring reset from input'
            return
        else :
            pass
        
        # I also want to ignore the "up"
        if value == 0 :
            # print '  ignoring up'
            return
        elif value == 1 :
            # set when we want to start paying attention to repeats
            self.m_ignoreTill = now + self.m_ignore
        elif value == 2 :
            if now < self.m_ignoreTill :
                print '  ignoring repeat until %d' % self.m_ignoreTill
                return
            else:
                # we let this one through, but set when we want to start
                # paying attention to the next repeat 
                self.m_ignoreTill = now + self.m_repeatRate
                pass
            pass
        else:
            pass
                
        key = self.keymap.get(code)
        if not key :
            print ' UNMAPPED KEY'
            return
        else:
            pass

        print '  sending off event %s' % key
        self.post_key(key)

        return True