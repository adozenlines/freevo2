# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# directory.py - Directory handling
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002 Krister Lagerstrom, 2003-2007 Dirk Meyer, et al.
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

# python imports
import os
import stat
import copy
import logging
import time

# kaa imports
import kaa
import kaa.notifier
import kaa.beacon
from kaa.weakref import weakref
from kaa.strutils import str_to_unicode

# freevo imports
from freevo.ui import config

import menu
import fxditem

from menu import Files, Action, ActionItem, MediaPlugin
from playlist import Playlist
from event import OSD_MESSAGE, DIRECTORY_CHANGE_MENU_TYPE, \
     DIRECTORY_TOGGLE_HIDE_PLAYED

from application import MessageWindow

# get logging object
log = logging.getLogger()

# get config object directory
config = config.directory

# register to beacon as string: on/off/auto
kaa.beacon.register_file_type_attrs('dir',
    freevo_cache  = (list, kaa.beacon.ATTR_SIMPLE),
    freevo_config = (dict, kaa.beacon.ATTR_SIMPLE),
)

def find_start_string(s1, s2):
    """
    Find similar start in both strings
    """
    ret = ''
    tmp = ''
    while True:
        if len(s1) < 2 or len(s2) < 2:
            return ret
        if s1[0] == s2[0]:
            tmp += s2[0]
            if s1[1] in (u' ', u'-', u'_', u',', u':', '.') and \
               s2[1] in (u' ', u'-', u'_', u',', u':', '.'):
                ret += tmp + u' '
                tmp = ''
            s1 = s1[1:].lstrip(u' -_,:.')
            s2 = s2[1:].lstrip(u' -_,:.')
        else:
            return ret


def remove_start_string(string, start):
    """
    remove start from the beginning of string.
    """
    start = start.replace(u' ', '')
    for i in range(len(start)):
        string = string[1:].lstrip(' -_,:.')

    return string[0].upper() + string[1:]


class DirItem(Playlist):
    """
    class for handling directories
    """
    type = 'dir'

    def __init__(self, directory, parent, name = '', type = None):

        # store type as menu_type and go on handling it as media_type
        # with tv replaced by video. Only DirItem has a difference between
        # media_type and menu_type with the extra tv value. This is needed
        # to show a tv based skin when browsing a dir from the tv plugin.
        self.menu_type = type
        if type == 'tv':
            type = 'video'
            
        Playlist.__init__(self, parent=parent, type=type)
        self.item_menu  = None
        self.set_url(directory)
        self.files = Files()
        if directory.get('read_only'):
            self.files.read_only = True
        self.files.append(directory)
        if name:
            self.name = str_to_unicode(name)
        if self['show_all_items']:
            # FIXME: no way to set this
            self.media_type = None
        self.query = None
        

    @kaa.notifier.yield_execution()
    def _calculate_num_items(self):
        """
        calculate the number of items in the directory.
        """
        log.info('create metainfo for %s', self.filename)
        listing = kaa.beacon.query(parent=self.info)
        if not listing.valid:
            yield listing.wait()
        listing = listing.get(filter='extmap')
        mediatype = ''
        if self.media_type:
            media_type = '_%s' % self.media_type
        num = 0
        for p in MediaPlugin.plugins(self.media_type):
            num += p.count(self, listing)
        self['cache:num_play_items%s' % media_type] = num
        self['cache:num_dir_items%s' % media_type] = len(listing.get('beacon:dir'))
        self['cache:num_items%s' % media_type] = num + len(listing.get('beacon:dir'))
        # update menu since we have the info now
        # FIXME: what happens if a download is happening in that dir?
        self.get_menustack().refresh()

        
    def __getitem__(self, key):
        """
        return the specific attribute
        """
        if key == 'type':
            return _('Directory')

        if key.startswith('num_'):
            if self.media_type:
                key = 'cache:' + key + '_' + self.media_type
            num = Playlist.__getitem__(self, key)
            if num is None:
                self._calculate_num_items()
            return num

        if key in ( 'freespace', 'totalspace' ):
            s = os.statvfs(self.filename)
            if key == 'freespace':
                space = s[statvfs.F_BAVAIL] * long(s[statvfs.F_BSIZE])
            else:
                space = s[statvfs.F_BLOCKS] * long(s[statvfs.F_BSIZE])
            space = space / 1000000
            if space > 1000:
                space='%s,%s' % (space / 1000, space % 1000)
            return space

        if key.startswith('cfg:'):
            value = self.info.get('tmp:%s' % key[4:])
            if value is not None:
                # tmp override of that value
                return value
            # get config value from freevo_config
            value = Playlist.__getitem__(self, key)
            if value not in (None, 'auto'):
                # value is set for this item
                if value == 'on':
                    return True
                if value == 'off':
                    return False
                return value
            if isinstance(self.parent, DirItem):
                # return the value from the parent (auto)
                return self.parent[key]
            # auto and no parent, use config file values
            if key == 'cfg:sort':
                if self.menu_type == 'tv':
                    return config.tvsort
                return config.sort
            # config files does not know about hide_played and reverse
            value = getattr(config, key[4:], False)
            if isinstance(value, bool):
                return value
            return self.media_type in value.split(',')

        return Playlist.__getitem__(self, key)


    # eventhandler for this item
    def eventhandler(self, event):

        if self.item_menu == None:
            return Playlist.eventhandler(self, event)

        if event == DIRECTORY_CHANGE_MENU_TYPE:
            possible = [ ]

            for p in MediaPlugin.plugins():
                for t in p.possible_media_types:
                    if not t in possible:
                        possible.append(t)

            try:
                pos = possible.index(self.media_type)
                type = possible[(pos+1) % len(possible)]
            except (IndexError, ValueError), e:
                return Playlist.eventhandler(self, event)

            self.media_type = self.menu_type = type
            # deactivate autoplay but not save it
            self['tmp:autoplay_single_item'] = False
            self.item_menu.autoselect = False
            self.browse()
            OSD_MESSAGE.post('%s view' % type)
            return True

        if event == DIRECTORY_TOGGLE_HIDE_PLAYED:
            self['cfg:hide_played'] = not self['cfg:hide_played']
            self['tmp:autoplay_single_item'] = False
            self.item_menu.autoselect = False
            self.browse()
            if self['cfg:hide_played']:
                OSD_MESSAGE.post('Hide played items')
            else:
                OSD_MESSAGE.post('Show all items')

        return Playlist.eventhandler(self, event)


    # ======================================================================
    # actions
    # ======================================================================

    def actions(self):
        """
        return a list of actions for this item
        """
        browse = Action(_('Browse directory'), self.browse)
        play = Action(_('Play all files in directory'), self.play)

        if self['num_items']:
            if self['cfg:autoplay_items'] and not self['num_dir_items']:
                items = [ play, browse ]
            else:
                items = [ browse, play ]
        else:
            items = [ browse ]

        if self.info['num_items']:
            a = Action(_('Random play all items'), self.play)
            a.parameter(random=True)
            items.append(a)

        if self['num_dir_items']:
            a = Action(_('Recursive random play all items'), self.play)
            a.parameter(random=True, recursive=True)
            items.append(a)
            a = Action(_('Recursive play all items'), self.play)
            a.parameter(recursive=True)
            items.append(a)

        a = Action(_('Configure directory'), self.configure, 'configure')
        items.append(a)

        return items



    def play(self, random=False, recursive=False):
        """
        play directory
        """
        # FIXME: add password checking here
        if not os.path.exists(self.filename):
	    MessageWindow(_('Directory does not exist')).show()
            return
        query = kaa.beacon.query(parent=self.info, recursive=recursive)
        pl = Playlist(playlist = query, parent = self,
                      type=self.media_type, random=random)
        pl.play()

        # Now this is ugly. If we do nothing 'pl' will be deleted by the
        # garbage collector, so we have to store it somehow
        self.__pl_for_gc = pl
        return


    def browse(self):
        """
        build the items for the directory
        """
        # FIXME: check for password

        play_items = []
        dir_items  = []
        pl_items   = []

        # Delete possible skin settings
        # FIXME: This is a very bad handling, maybe signals?
        if hasattr(self.item_menu, 'skin_default_has_description'):
            del self.item_menu.skin_default_has_description
        if hasattr(self.item_menu, 'skin_default_no_images'):
            del self.item_menu.skin_default_no_images

        elif not os.path.exists(self.filename):
            # FIXME: better handling!!!!!
	    MessageWindow(_('Directory does not exist')).show()
            return

        if self.query is None:
            self.query = kaa.beacon.query(parent=self.info)
            self.query.signals['changed'].connect_weak(self.browse)
            self.query.monitor()
            if not self.query.valid:
                # the changed signal will be called when the listing
                # is ready and this will trigger browse again.
                return
                
        listing = self.query.get(filter='extmap')

        #
        # build items
        #
        # build play_items, pl_items and dir_items
        for p in MediaPlugin.plugins(self.media_type):
            for i in p.get(self, listing):
                if i.type == 'playlist':
                    pl_items.append(i)
                elif i.type == 'dir':
                    dir_items.append(i)
                else:
                    play_items.append(i)

        # normal DirItems
        for item in listing.get('beacon:dir'):
            d = DirItem(item, self, type = self.menu_type)
            dir_items.append(d)

        # remember listing
        self.listing = listing

        # handle hide_played
        if self['cfg:hide_played']:
            play_items = [ p for p in play_items if not p.info.get('last_played') ]

        # remove same beginning from all play_items
        substr = ''
        if len(play_items) > 4 and len(play_items[0].name) > 5:
            substr = play_items[0].name[:-5].lower()
            for i in play_items[1:]:
                if len(i.name) > 5:
                    substr = find_start_string(i.name.lower(), substr)
                    if not substr or len(substr) < 10:
                        break
                else:
                    break
            else:
                for i in play_items:
                    i.name = remove_start_string(i.name, substr)


        #
        # sort all items
        #

        def _sortfunc(m):
            return lambda l, o: cmp(l.sort(m), o.sort(m))

        sorttype = self['cfg:sort']

        # sort directories by name
        dir_items.sort(_sortfunc(sorttype))

        # sort playlist by name or delete if they should not be displayed
        if self.menu_type and not self.menu_type in \
               config.add_playlist_items.split(','):
            pl_items = []
        else:
            pl_items.sort(_sortfunc(sorttype))

        play_items.sort(_sortfunc(sorttype))
        if self['cfg:reverse']:
            play_items.reverse()

        #
        # final settings
        #

        # FIXME: update num items
        # len(play_items), len(pl_items), len(dir_items)

        # add all playable items to the playlist of the directory
        # to play one files after the other
        if self['cfg:isplaylist']:
            self.set_playlist(play_items)

        # build a list of all items
        items = dir_items + pl_items + play_items

        # random playlist
        if self.menu_type and self.menu_type in \
               config.add_random_playlist and len(play_items) > 1:
            pl = Playlist(_('Random playlist'), play_items, self,
                          random=True, type=self.media_type)
            pl.autoplay = True
            items = [ pl ] + items


        #
        # action
        #

        if self.item_menu is not None:
            # we could update it
            if self.item_menu:
                # still in the stack
                self.item_menu.set_items(items)
                return
            # weakref is gone
            self.query = None
            return

        # normal menu build
        item_menu = menu.Menu(self.name, items, type = self.menu_type)
        item_menu.autoselect = self['cfg:autoplay_single_item']
        self.get_menustack().pushmenu(item_menu)
        self.item_menu = weakref(item_menu)


    def get_configure_items(self):
        # variables for 'configure' submenu
        # FIXME: put this outside the code somehow
        return [
            ('sort', _('Sort'), ('auto', 'name', 'smart', 'filename', 'date' ),
             _('How to sort items.')),
            ('reverse', _('Reverse Sort'), ('auto', 'on', 'off' ),
             _('Show the items in the list in reverse order.')),
            ('autoplay_single_item', _('Autoplay Single Item'), ('auto', 'on', 'off' ),
             _('Don\'t show directory if only one item exists and auto select it.')),
            ('autoplay_items', _('Autoplay Items'), ('auto', 'on', 'off' ),
             _('Autoplay the whole directory as playlist when it contains only files.')),
            ('use_metadata', _('Use Tag Names'), ('auto', 'on', 'off' ),
             _('Use the names from the media files tags as display name.')),
            ('isplaylist', _('Is Playlist'), ('auto', 'on', 'off' ),
             _('Handle the directory as playlist and play the next item when one is done.')) ,
            ('hide_played', _('Hide Played Items'), ('auto', 'on', 'off' ),
             _('Hide items already played.'))]
