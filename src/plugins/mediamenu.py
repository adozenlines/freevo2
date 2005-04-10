# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# mediamenu.py - Basic menu for all kinds of media
# -----------------------------------------------------------------------------
# $Id$
#
# This plugin can create submenus for the different kind of media plugins.
#
# First edition: Dirk Meyer <dmeyer@tzi.de>
# Maintainer:    Dirk Meyer <dmeyer@tzi.de>
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002-2004 Krister Lagerstrom, Dirk Meyer, et al.
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

# python imports
import os
import copy
import logging

# freevo imports
import config

import plugin
import plugins.rom_drives

from event import *
from item import Item
from directory import DirItem
from mainmenu import MainMenuItem
from menu import Menu
from mediadb import FileListing
from gui import ProgressBox

# get logging object
log = logging.getLogger()


class PluginInterface(plugin.MainMenuPlugin):
    """
    Plugin to integrate a mediamenu (video/audio/image/games) into
    the Freevo main menu. This plugin is auto-loaded when you activate
    the 'video', 'audio', 'image' or 'games' plugin.
    """
    def __init__(self, type=None, force_text_view=False):
        plugin.MainMenuPlugin.__init__(self)
        self.type = type
        self.force_text_view = force_text_view or \
                               config.GUI_MEDIAMENU_FORCE_TEXTVIEW


    def items(self, parent):
        return [ MainMenuItem('', action=MediaMenu().main_menu,
                              arg=(self.type,self.force_text_view),
                              type='main', parent=parent,
                              skin_type = self.type) ]



class MediaMenu(Item):
    """
    This is the main menu for audio, video and images. It displays the default
    directories and the ROM_DRIVES
    """

    def __init__(self):
        Item.__init__(self)
        self.type = 'mediamenu'

        # init the style how to handle discs
        if config.HIDE_UNUSABLE_DISCS:
            # set the disc types to be shown
            self.dir_types = {
                'audio': [ 'dir', 'audiocd', 'audio', 'empty_cdrom' ],
                'video': [ 'dir', 'video', 'vcd', 'dvd', 'empty_cdrom' ],
                'image': [ 'dir', 'empty_cdrom' ],
                'games': [ 'dir', 'empty_cdrom' ],
                }
        else:
            # show all discs in all mediamenus
            self.dir_types = {}
            for type in ('audio', 'video', 'image', 'games'):
                self.dir_types[type] = [ 'dir', 'audiocd', 'audio', 'video',
                                         'vcd', 'dvd', 'empty_cdrom' ]


    def main_menu_generate(self):
        """
        generate the items for the main menu. This is needed when first
        generating the menu and if something changes by pressing the EJECT
        button
        """
        # copy the "normal" items and add plugin data
        items = copy.copy(self.normal_items)

        if self.display_type:
            # get display type based plugins
            plugins_list = plugin.get('mainmenu_%s' % self.display_type)
        else:
            # no plugins
            plugins_list = []

        # get the dir_type
        dir_type = self.dir_types.get( self.display_type, [] )

        # add all plugin data
        for p in plugins_list:
            if isinstance( p, plugins.rom_drives.rom_items ):
                # do not show media from other menus
                for i in p.items( self ):
                    if i.type in dir_type:
                        items.append(i)
            else:
                items += p.items( self )
        return items


    def main_menu(self, arg=None, menuw=None):
        """
        display the (IMAGE|VIDEO|AUDIO|GAMES) main menu
        """
        self.display_type, force_text_view = arg
        title = _('Media')

        self.menuw = menuw

        if self.display_type == 'video':
            title = _('Movie')
        if self.display_type == 'audio':
            title = _('Audio')
        if self.display_type == 'image':
            title = _('Image')
        if self.display_type == 'games':
            title = _('Games')

        menutitle = _('%s Main Menu') % title

        if self.display_type:
            items = getattr(config, '%s_ITEMS' % self.display_type.upper())
        else:
            items = []

        files = []
        additional_data = {}

        # add default items
        for item in items:
            try:
                # split the list on dir/file, title and add_args
                add_args = None
                if isstring(item):
                    # only a filename is given
                    title, filename = u'', item
                else:
                    # title and filename are given
                    (title, filename) = item[:2]
                    if len(item) > 2:
                        # ... and add_args
                        add_args = item[2:]

                # is the dir / file reachable?
                reachable = 1
                pos = filename.find(':/')
                if pos > 0:
                    # it is an url
                    if filename.find(':/') < filename.find('/'):
                        hostname = filename[0:pos]
                        filename = filename[pos+1:]
                        try:
                            alive = config.HOST_ALIVE_CHECK % hostname
                            if os.system(alive) != 0:
                                reachable = 0
                        except Exception, e:
                            log.exception('Error parsing %s' % filename)
                            raise e
                if reachable:
                    if vfs.isdir(filename):
                        # directory
                        files.append(filename)
                        additional_data[filename] = ( title, add_args, True )
                    else:
                        if not vfs.isfile(filename) and \
                               filename.startswith(os.getcwd()):
                            # file is in share dir
                            filename = filename[len(os.getcwd()):]
                            if filename[0] == '/':
                                filename = filename[1:]
                            filename = vfs.join(config.SHARE_DIR, filename)
                        # add files
                        files.append(filename)
                        additional_data[filename] = ( title, [], False )
            except:
                log.exception('Error parsing %s' % str(item))

        # check and update the listing
        listing = FileListing(files)
        if listing.num_changes > 10:
            text = _('Scanning menu, be patient...')
            popup = ProgressBox(text, full=listing.num_changes)
            popup.show()
            listing.update(popup.tick)
            popup.destroy()
        elif listing.num_changes:
            listing.update()

        # Generate the media menu, we need to create a new listing (that sucks)
        # But with the listing we have, the order will be mixed up.
        self.normal_items = []
        for f in files:
            listing = FileListing([f])
            if listing.num_changes > 0:
                # this shouldn't happen, but just in case
                listing.update()

            # get additional_data for the file
            title, add_args, is_dir = additional_data[f]
            if is_dir:
                # directory
                for item in listing.get_dir():
                    d = DirItem(item, self, name = title,
                                display_type = self.display_type,
                                add_args = add_args)
                    self.normal_items.append(d)
            else:
                # normal file
                for p in plugin.mimetype(self.display_type):
                    items = p.get(self, listing)
                    if title:
                        for i in items:
                            i.name = title
                    self.normal_items += items

        # generate all other items
        items = self.main_menu_generate()

        # autoselect one item
        if len(items) == 1:
            items[0](menuw=menuw)
            return

        type = '%s main menu' % self.display_type
        item_menu = Menu(menutitle, items, item_types = type, umount_all=1,
                         reload_func = self.reload)
        item_menu.skin_force_text_view = force_text_view
        menuw.pushmenu(item_menu)


    def reload(self):
        """
        Reload the menu. maybe a disc changed or some other plugin.
        """
        menu = self.menuw.menustack[1]

        sel = menu.choices.index(menu.selected)
        new_choices = self.main_menu_generate()
        if not menu.selected in new_choices:
            if len(new_choices) <= sel:
                menu.selected = new_choices[-1]
            else:
                menu.selected = new_choices[sel]
        menu.choices = new_choices
        return menu


    def eventhandler(self, event = None, menuw=None):
        """
        Eventhandler for the media main menu. The menu must be regenerated
        when a disc in a rom drive changes
        """
        if plugin.isevent(event):
            if not menuw:
                # nothing to do when no menuw is shown
                return False

            menu = menuw.menustack[1]

            sel = menu.choices.index(menu.selected)
            menuw.menustack[1].choices = self.main_menu_generate()
            if not menu.selected in menu.choices:
                if len( menu.choices ) > sel:
                    menu.selected = menu.choices[sel]
                elif menu.choices:
                    menu.selected = menu.choices[ -1 ]
                else:
                    menu.selected = None

            if menu == menuw.menustack[-1] and menuw.visible:
                menuw.refresh()
            # others may need this event, too
            return False

        # give the event to the next eventhandler in the list
        return Item.eventhandler(self, event, menuw)
