# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# configure.py - Configure video playing
# -----------------------------------------------------------------------------
# $Id$
#
# This file defines some configure actions for a VideoItem.
#
# Note: The functions are not bound to a class, so the item passed by the
# menu stack is not the VideoItem that should be changed. To resolve that
# problem, all functions get the VideoItem as parameter, the first parameter
# 'selected' is the item in the menu that is selected, a simple item.
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002-2004 Krister Lagerstrom, Dirk Meyer, et al.
#
# First Edition: Dirk Meyer <dmeyer@tzi.de>
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

__all__ = [ 'get_items', 'get_menu' ]

# freevo imports
from menu import *


def play_movie(selected, item, mplayer_options=None):
    """
    play the movie (again)
    """
    item.get_menustack().delete_menu()
    item.play(mplayer_options=mplayer_options)


def set_variable(selected, item, variable, value):
    """
    Set a variable for the item.
    """
    setattr(item, variable, value)
    item.get_menustack().delete_menu()
    item.get_menustack().refresh()


def start_chapter(selected, item, mplayer_options):
    """
    Handle chapter selection.
    """
    item.get_menustack().delete_menu()
    play_movie(selected, item, mplayer_options)


def start_subitem(selected, item, pos):
    """
    Handle subitem selection.
    """
    item.conf_select_this_item = item.subitems[pos]
    item.get_menustack().delete_menu()
    play_movie(selected, item)


def audio_selection(selected, item):
    """
    Submenu for audio selection.
    """
    menu_items = []
    for a in item.info['audio']:
        if not a.has_key('id') or a['id'] in ('', None):
            a['id'] = item.info['audio'].index(a) + 1
        if not a.has_key('language') or not a['language']:
            a['language'] = _('Stream %s') % a['id']
        if not a.has_key('channels') or not a['channels']:
            a['channels'] = 2 # wild guess :-)
        else:
            continue
        name = '%s (channels=%s)' % (a['language'], a['channels'])
        action = ActionItem(name, item, set_variable)
        action.parameter(item, 'selected_audio', a['id'])
        menu_items.append(action)
    item.pushmenu(Menu(_('Audio Menu'), menu_items, theme=item.skin_fxd))


def subtitle_selection(selected, item):
    """
    Submenu for subtitle selection.
    """
    action = ActionItem(_('no subtitles'), item, set_variable)
    action.parameter(item, 'selected_subtitle', -1)
    menu_items = [ action ]
    for s in range(len(item.info['subtitles'])):
        action = ActionItem(item.info['subtitles'][s], item, set_variable)
        action.parameter(item, 'selected_subtitle', s)
        menu_items.append(action)
    item.pushmenu(Menu(_('Subtitle Menu'), menu_items, theme=item.skin_fxd))


def chapter_selection(selected, item):
    """
    Submenu for chapter selection.
    """
    menu_items = []
    if isinstance(item.info['chapters'], int):
        for c in range(1, item.info['chapters']):
            a = ActionItem(_('Play chapter %s') % c, item, start_chapter)
            a.parameter(item, ' -chapter %s' % c)
            menu_items.append(a)
    elif item.info['chapters']:
        for c in item.info['chapters']:
            a = ActionItem(c.name, item, start_chapter)
            a.parameter(item, ' -ss %s' % c.pos)
            menu_items.append(a)
    item.pushmenu(Menu(_('Chapter Menu'), menu_items, theme=item.skin_fxd))


def subitem_selection(selected, item):
    """
    Submenu for subitem selection.
    """
    menu_items = []
    for pos in range(len(item.subitems)):
        a = ActionItem(_('Play chapter %s') % (pos+1), item, start_subitem)
        a.parameter(item, pos)
        menu_items.append(a)
    item.pushmenu(Menu(_('Chapter Menu'), menu_items, theme=item.skin_fxd))


def toggle(selected, item, name, variable):
    """
    Basic toggle function.
    """
    item[variable] = not item[variable]
    # replace item
    selected.replace(add_toggle(item, name, variable))
    # update menu
    item.get_menustack().refresh()


def add_toggle(item, name, var):
    """
    Add a 'toggle' item.
    """
    if item[var]:
        action = ActionItem(_('Turn off %s') % name, item, toggle)
    else:
        action = ActionItem(_('Turn on %s') % name, item, toggle)
    action.parameter(item, name, var)
    return action


def get_items(item):
    """
    Return possible configure ActionItems.
    """
    items = []

    if item.filename or (item.mode in ('dvd', 'vcd') and \
                         item.player_rating >= 20):
        if item.info.has_key('audio') and len(item.info['audio']) > 1:
            a = ActionItem(_('Audio selection'), item, audio_selection)
            a.parameter(item)
            items.append(a)
        if item.info.has_key('subtitles') and len(item.info['subtitles']) > 1:
            a = ActionItem(_('Subtitle selection'), item, subtitle_selection)
            a.parameter(item)
            items.append(a)
        if item.info.has_key('chapters') and item.info['chapters'] > 1:
            a = ActionItem(_('Chapter selection'), item, chapter_selection)
            a.parameter(item)
            items.append(a)
    if item.subitems:
        # show subitems as chapter
        a = ActionItem(_('Chapter selection'), item, subitem_selection)
        a.parameter(item)
        items.append(a)

    items.append(add_toggle(item, _('deinterlacing'), 'deinterlace'))
    return items


def get_menu(item):
    """
    Return a complete menu for configure options.
    """
    p = ActionItem(_('Play'), play_movie)
    p.parameter(item)
    return Menu(_('Config Menu'), get_items(item) + [ p ], theme=item.skin_fxd)
