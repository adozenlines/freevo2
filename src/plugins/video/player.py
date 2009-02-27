# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# player.py - the Freevo video player
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2007 Dirk Meyer, et al.
#
# First Edition: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
#
# Please see the file AUTHORS for a complete list of authors.
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

__all__ = [ 'play', 'stop' ]

# python imports
import logging

# kaa imports
import kaa
import kaa.utils
import kaa.popcorn

# Freevo imports
from ... import core as freevo

# get logging object
log = logging.getLogger('video')

class Player(freevo.Application):
    """
    Video player object.
    """

    name = 'videoplayer'

    def __init__(self):
        capabilities = (freevo.CAPABILITY_FULLSCREEN, )
        super(Player, self).__init__('video', capabilities)
        self.player = kaa.popcorn.Player()
        # self.player.set_window(self.engine.get_window())
        self.elapsed_timer = kaa.WeakTimer(self.elapsed)


    @kaa.coroutine()
    def play(self, item, player=None):
        """
        play an item
        """
        if not self.status in (freevo.STATUS_IDLE, freevo.STATUS_STOPPED):
            # Already running, stop the current player by sending a STOP
            # event. The event will also get to the playlist behind the
            # current item and the whole list will be stopped.
            freevo.Event(freevo.STOP, handler=self.eventhandler).post()
            # Now wait for our own 'stop' signal
            yield kaa.inprogress(self.signals['stop'])
            if not self.status in (freevo.STATUS_IDLE, freevo.STATUS_STOPPED):
                log.error('unable to stop current video playback')
                yield False
        if not kaa.main.is_running():
            # Freevo is in shutdown mode, do not start a new player, the old
            # only stopped because of the shutdown.
            yield False

        # Try to get VIDEO and AUDIO resources. The ressouces will be freed
        # by the system when the application switches to STATUS_STOPPED or
        # STATUS_IDLE.
        if (yield self.get_resources('AUDIO', 'VIDEO', force=True)) == False:
            log.error("Can't get resource AUDIO, VIDEO")
            yield False

        # store item and playlist
        self.item = item
        self.playlist = self.item.get_playlist()
        if self.playlist:
            self.playlist.select(self.item)

        # set the current item to the gui engine
        # self.engine.set_item(self.item)
        self.status = freevo.STATUS_RUNNING
        self.is_in_menu = False

        self.player.signals['end'].connect_once(freevo.PLAY_END.post, self.item)
        try:
            yield self.player.open(self.item.url, player=player)
            # FIXME: set more properties
            if item.info.get('interlaced'):
                self.player.set_property('deinterlace', True)
            yield self.player.play()
            freevo.PLAY_START.post(self.item)
        except kaa.popcorn.PlayerError, e:
            self.player.signals['end'].disconnect(freevo.PLAY_END.post, self.item)
            log.exception('video playback failed')
            # We should handle it here with a messge or something like that. To
            # make playlist work, we just send start and stop. It's ugly but it
            # should work.
            freevo.PLAY_START.post(self.item)
            freevo.PLAY_END.post(self.item)
        yield True


    def stop(self):
        """
        Stop playing.
        """
        if self.status != freevo.STATUS_RUNNING:
            return True
        self.player.stop()
        self.status = freevo.STATUS_STOPPING


    def elapsed(self):
        """
        Callback for elapsed time changes.
        """
        if self.player.is_in_menu() != self.is_in_menu:
            self.is_in_menu = not self.is_in_menu
            if self.is_in_menu:
                self.eventmap = 'dvdnav'
            else:
                self.eventmap = 'video'
        # FIXME: if item does not start at position 0 the start time
        # must be taken into consideration for elapsed. This happens for
        # TS files from DVB sources.
        self.item.elapsed = round(self.player.position)


    def eventhandler(self, event):
        """
        React on some events or send them to the real player or the
        item belongig to the player
        """
        if event == freevo.STOP:
            # Stop the player and pass the event to the item
            self.stop()
            self.item.eventhandler(event)
            return True

        if event == freevo.PLAY_START:
            self.elapsed_timer.start(0.2)
            self.item.eventhandler(event)
            return True

        if event == freevo.PLAY_END:
            # Now the player has stopped (either we called self.stop() or the
            # player stopped by itself. So we need to set the application to
            # to stopped.
            self.status = freevo.STATUS_STOPPED
            self.elapsed_timer.stop()
            self.item.eventhandler(event)
            if self.status == freevo.STATUS_STOPPED:
                self.status = freevo.STATUS_IDLE
            return True

        if event in (freevo.PAUSE, freevo.PLAY):
            if self.player.get_state() == kaa.popcorn.STATE_PLAYING:
                self.player.pause()
                return True
            if self.player.get_state() == kaa.popcorn.STATE_PAUSED:
                self.player.resume()
                return True
            return False

        if event == freevo.SEEK:
            self.player.seek(int(event.arg), kaa.popcorn.SEEK_RELATIVE)
            return True

        if event == freevo.VIDEO_TOGGLE_INTERLACE:
            interlaced = not self.player.get_property('deinterlace')
            self.item.info['interlaced'] = interlaced
            self.player.set_property('deinterlace', interlaced)
            if interlaced:
                freevo.Event(freevo.OSD_MESSAGE, _('Turn on deinterlacing')).post()
            else:
                freevo.Event(freevo.OSD_MESSAGE, _('Turn off deinterlacing')).post()
            return True

        if event == freevo.VIDEO_CHANGE_ASPECT:
            modes = kaa.popcorn.SCALE_METHODS
            current = self.player.get_property('scale')
            if current in modes:
                idx = (modes.index(current) + 1) % len(modes)
                log.info('change scale to %s', modes[idx])
                self.player.set_property('scale', modes[idx])
            return True

        if event in (freevo.NEXT, freevo.PREV):
            self.player.nav_command(str(event).lower())
            return True

        if event == freevo.DVDNAV_MENU:
            self.player.nav_command('menu1')
            return True

        if str(event).startswith('DVDNAV_'):
            # dvd navigation commands
            self.player.nav_command(str(event)[7:].lower())
            return True

        # give it to the item
        return self.item.eventhandler(event)


# create singleton object
player = kaa.utils.Singleton(Player)

# create functions to use from the outside
play = player.play
stop = player.stop