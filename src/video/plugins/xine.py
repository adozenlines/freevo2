# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# xine.py - the Freevo XINE module for video
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
#
# Activate this plugin by putting plugin.activate('video.xine') in your
# local_conf.py. Than xine will be used for DVDs when you SELECT the item.
# When you select a title directly in the menu, this plugin won't be used
# and the default player (mplayer) will be used. You need xine-ui >= 0.9.22
# to use this.
#
# Todo:        
#
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.65  2005/06/24 20:51:40  dischi
# remove USER_END and self.parent.current_item
#
# Revision 1.64  2005/06/19 16:30:28  dischi
# adjust to application/base.py changes
#
# Revision 1.63  2005/06/09 19:43:55  dischi
# clean up eventhandler usage
#
# Revision 1.62  2005/05/07 17:33:36  dischi
# fix dvd handling
#
# Revision 1.61  2005/04/10 17:58:12  dischi
# switch to new mediainfo module
#
# Revision 1.60  2005/04/01 18:04:14  rshortt
# Add support for df_xine.
#
# Revision 1.59  2004/12/18 13:37:27  dischi
# adjustments to new childapp
#
# Revision 1.58  2004/12/07 16:05:16  dischi
# fix event context setting
#
# Revision 1.57  2004/11/21 10:12:47  dischi
# improve system detect, use config.detect now
#
# Revision 1.56  2004/11/20 18:23:05  dischi
# use python logger module for debug
#
# Revision 1.55  2004/10/06 19:13:41  dischi
# use config auto detection for xine version
#
# Revision 1.54  2004/10/06 19:01:32  dischi
# use new childapp interface
#
# Revision 1.53  2004/09/29 18:48:41  dischi
# fix xine lirc handling
#
# Revision 1.52  2004/09/29 18:47:37  dischi
# fix xine lirc handling
#
# Revision 1.51  2004/08/25 12:51:46  dischi
# moved Application for eventhandler into extra dir for future templates
#
# Revision 1.50  2004/08/23 20:36:44  dischi
# rework application handling
#
# Revision 1.49  2004/08/22 20:12:12  dischi
# class application doesn't change the display (screen) type anymore
#
# Revision 1.48  2004/08/01 10:45:19  dischi
# make the player an "Application"
#
# Revision 1.47  2004/07/26 18:10:20  dischi
# move global event handling to eventhandler.py
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


import time, os, re
import copy

import config     # Configuration handler. reads config file.
import util
import childapp
from application import Application

from event import *
import plugin

import logging
log = logging.getLogger('video')

class PluginInterface(plugin.Plugin):
    """
    Xine plugin for the video player.
    """
    def __init__(self):
        config.detect('xine')

        try:
            config.XINE_COMMAND
        except:
            self.reason = '\'XINE_COMMAND\' not defined'
            return

        if config.XINE_COMMAND.find('fbxine') >= 0:
            type = 'fb'
            if config.FBXINE_VERSION < '0.99.1' and \
                   config.FBXINE_VERSION < '0.9.23':
                self.reason = "'fbxine' version too old"
                return
        elif config.XINE_COMMAND.find('df_xine') >= 0:
           type = 'df' 
        else:
            type = 'X'
            if config.XINE_VERSION < '0.99.1' and \
                   config.XINE_VERSION < '0.9.23':
                self.reason = "'xine' version too old"
                return

        plugin.Plugin.__init__(self)

        # register xine as the object to play
        plugin.register(Xine(type, config.XINE_VERSION),
                        plugin.VIDEO_PLAYER, True)



class Xine(Application):
    """
    the main class to control xine
    """
    def __init__(self, type, version):
        Application.__init__(self, 'xine', 'video', True)
        self.name      = 'xine'
        self.xine_type = type
        self.version   = version
        self.app       = None
        self.command   = config.XINE_COMMAND.split(' ') + \
                         [ '--stdctl', '-V', config.XINE_VO_DEV,
                           '-A', config.XINE_AO_DEV ] + \
                           config.XINE_ARGS_DEF.split(' ')


    def rate(self, item):
        """
        How good can this player play the file:
        2 = good
        1 = possible, but not good
        0 = unplayable
        """
        if item.url.startswith('dvd://'):
            return 2
        if item.url.startswith('vcd://'):
            if self.version > 922 and item.url == 'vcd://':
                return 2
            return 0

        if item.mimetype in config.VIDEO_XINE_SUFFIX:
            return 2
        if item.network_play:
            return 1
        return 0
    
    
    def play(self, options, item):
        """
        play a dvd with xine
        """
        self.item        = item
        self.set_eventmap('video')
        if config.EVENTS.has_key(item.mode):
            self.set_eventmap(item.mode)

        if plugin.getbyname('MIXER'):
            plugin.getbyname('MIXER').reset()

        command = copy.copy(self.command)

        if item['deinterlace'] and (self.xine_type == 'X' or self.version > 922):
            command.append('-D')

        if config.XINE_COMMAND.startswith(config.CONF.xine) and config.XINE_USE_LIRC:
            command.append('--no-lirc')

        if config.XINE_COMMAND.startswith(config.CONF.fbxine) and config.FBXINE_USE_LIRC:
            command.append('--no-lirc')

        if self.version < 923:
            for arg in command:
                if arg.startswith('--post'):
                    command.remove(arg)
                    break
                
        self.max_audio        = 0
        self.current_audio    = -1
        self.max_subtitle     = 0
        self.current_subtitle = -1

        if item.mode == 'dvd':
            if item.info['tracks']:
                for track in item.info['tracks']:
                    self.max_audio = max(self.max_audio, len(track['audio']))
                    self.max_subtitle = max(self.max_subtitle, len(track['subtitles']))
            else:
                self.max_audio = len(item.info['audio'])
                self.max_subtitle = len(item.info['subtitles'])
                
        if item.mode == 'dvd' and hasattr(item, 'filename') and item.filename and \
               item.filename.endswith('.iso'):
            # dvd:///full/path/to/image.iso/
            command.append('dvd://%s/' % item.filename)

        elif item.mode == 'dvd' and hasattr(item.media, 'devicename'):
            # dvd:///dev/dvd/2
            url = 'dvd://%s/%s' % (item.media.devicename, item.url[6:])
            command.append(url.strip('/'))

        elif item.mode == 'dvd': # no devicename? Probably a mirror image on the HD
            command.append(item.url)

        elif item.mode == 'vcd':
            # vcd:///dev/cdrom -- NO track support (?)
            command.append('vcd://%s' % item.media.devicename)

        elif item.mimetype == 'cue':
            command.append('vcd://%s' % item.filename)
            self.set_eventmap('vcd')
            
        else:
            command.append(item.url)
            
        log.info('Xine.play(): Starting cmd=%s' % command)

        self.show()
        self.app = childapp.Instance( command, prio = config.MPLAYER_NICE )
        return None
    

    def stop(self):
        """
        Stop xine
        """
        Application.stop(self)
        if self.app:
            self.app.stop('quit\n')
            self.app = None

    def eventhandler(self, event):
        """
        eventhandler for xine control. If an event is not bound in this
        function it will be passed over to the items eventhandler
        """
        if not self.app:
            return self.item.eventhandler(event)
            
        if event == PLAY_END:
            self.stop()
            self.item.eventhandler(event)
            return True

        if event == PAUSE or event == PLAY:
            self.app.write('pause\n')
            return True

        if event == STOP:
            self.stop()
            self.item.eventhandler(event)
            return True

        if event == SEEK:
            pos = int(event.arg)
            if pos < 0:
                action='SeekRelative-'
                pos = 0 - pos
            else:
                action='SeekRelative+'
            if pos <= 15:
                pos = 15
            elif pos <= 30:
                pos = 30
            else:
                pos = 30
            self.app.write('%s%s\n' % (action, pos))
            return True

        if event == TOGGLE_OSD:
            self.app.write('OSDStreamInfos\n')
            return True

        if event == VIDEO_TOGGLE_INTERLACE:
            self.app.write('ToggleInterleave\n')
            self.item['deinterlace'] = not self.item['deinterlace']
            return True

        if event == NEXT:
            self.app.write('EventNext\n')
            return True

        if event == PREV:
            self.app.write('EventPrior\n')
            return True

        # DVD NAVIGATION
        if event == DVDNAV_LEFT:
            self.app.write('EventLeft\n')
            return True
            
        if event == DVDNAV_RIGHT:
            self.app.write('EventRight\n')
            return True
            
        if event == DVDNAV_UP:
            self.app.write('EventUp\n')
            return True
            
        if event == DVDNAV_DOWN:
            self.app.write('EventDown\n')
            return True
            
        if event == DVDNAV_SELECT:
            self.app.write('EventSelect\n')
            return True
            
        if event == DVDNAV_TITLEMENU:
            self.app.write('TitleMenu\n')
            return True
            
        if event == DVDNAV_MENU:
            self.app.write('Menu\n')
            return True

        # VCD NAVIGATION
        if event in INPUT_ALL_NUMBERS:
            self.app.write('Number%s\n' % event.arg)
            time.sleep(0.1)
            self.app.write('EventSelect\n')
            return True
        
        if event == MENU:
            self.app.write('TitleMenu\n')
            return True


        # DVD/VCD language settings
        if event == VIDEO_NEXT_AUDIOLANG and self.max_audio:
            if self.current_audio < self.max_audio - 1:
                self.app.write('AudioChannelNext\n')
                self.current_audio += 1
                # wait until the stream is changed
                time.sleep(0.1)
            else:
                # bad hack to warp around
                if self.xine_type == 'fb':
                    self.app.write('AudioChannelDefault\n')
                    time.sleep(0.1)
                for i in range(self.max_audio):
                    self.app.write('AudioChannelPrior\n')
                    time.sleep(0.1)
                self.current_audio = -1
            return True
            
        if event == VIDEO_NEXT_SUBTITLE and self.max_subtitle:
            if self.current_subtitle < self.max_subtitle - 1:
                self.app.write('SpuNext\n')
                self.current_subtitle += 1
                # wait until the stream is changed
                time.sleep(0.1)
            else:
                # bad hack to warp around
                if self.xine_type == 'fb':
                    self.app.write('SpuDefault\n')
                    time.sleep(0.1)
                for i in range(self.max_subtitle):
                    self.app.write('SpuPrior\n')
                    time.sleep(0.1)
                self.current_subtitle = -1
            return True
            
        if event == VIDEO_NEXT_ANGLE:
            self.app.write('EventAngleNext\n')
            time.sleep(0.1)
            return True            

        # nothing found? Try the eventhandler of the object who called us
        return self.item.eventhandler(event)
