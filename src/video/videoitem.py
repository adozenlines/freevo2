# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# videoitem.py - Item for video objects
# -----------------------------------------------------------------------
# $Id$
#
# This file contains a VideoItem. A VideoItem can not only hold a simple
# video file, it can also store variants of the same video and subitems
# if the video is splitted into several files. DVD and VCD are also
# VideoItems.
#
# Notes:
#
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.152  2004/11/13 15:54:12  dischi
# small bugfix
#
# Revision 1.151  2004/10/22 18:43:54  dischi
# make sure aspect is a string
#
# Revision 1.150  2004/09/14 20:07:04  dischi
# restructure and add docs
#
# Revision 1.149  2004/08/28 17:18:07  dischi
# fix multiple files in one video when replaying
#
# Revision 1.148  2004/08/27 14:23:39  dischi
# VideoItem is now based on MediaItem
#
# Revision 1.147  2004/08/24 16:42:44  dischi
# Made the fxdsettings in gui the theme engine and made a better
# integration for it. There is also an event now to let the plugins
# know that the theme is changed.
#
# Revision 1.146  2004/08/01 10:46:34  dischi
# remove menuw hiding, add some test code
#
# Revision 1.145  2004/07/26 18:10:19  dischi
# move global event handling to eventhandler.py
#
# Revision 1.144  2004/07/21 11:34:59  dischi
# disable one track auto-play for dvd
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


import os
import copy

import config
import util
import eventhandler
import menu
import configure
import plugin
import util.videothumb
import util.mediainfo

from gui   import PopupBox, AlertBox, ConfirmBox
from item  import MediaItem, FileInformation
from event import *

from database import tv_show_informations, discset_informations


class VideoItem(MediaItem):
    def __init__(self, url, parent, info=None, parse=True):
        self.autovars = [ ('deinterlace', 0) ]
        MediaItem.__init__(self, 'video', parent)
        self.set_url(url, info=parse)

        if info:
            self.info.set_variables(info)

        self.variants          = []         # if this item has variants
        self.subitems          = []         # more than one file/track to play
        self.current_subitem   = None
        self.media_id          = ''

        self.subtitle_file     = {}         # text subtitles
        self.audio_file        = {}         # audio dubbing

        self.mplayer_options   = ''
        self.tv_show           = False

        self.video_width       = 0
        self.video_height      = 0

        self.selected_subtitle = None
        self.selected_audio    = None
        self.elapsed           = 0
        
        self.possible_player   = []

        # find image for tv show and build new title
        if config.VIDEO_SHOW_REGEXP_MATCH(self.name) and not \
               self.network_play and config.VIDEO_SHOW_DATA_DIR:
            show_name = config.VIDEO_SHOW_REGEXP_SPLIT(self.name)
            if show_name[0] and show_name[1] and show_name[2] and show_name[3]:
                self.name = show_name[0] + u" " + show_name[1] + u"x" + \
                            show_name[2] + u" - " + show_name[3]
                image = util.getimage((config.VIDEO_SHOW_DATA_DIR + \
                                       show_name[0].lower()))
                if self.filename and not image:
                    image = util.getimage(os.path.dirname(self.filename)+'/'+ \
                                          show_name[0].lower())
                if image:
                    self.image = image
                if tv_show_informations.has_key(show_name[0].lower()):
                    tvinfo = tv_show_informations[show_name[0].lower()]
                    self.info.set_variables(tvinfo[1])
                    if not self.image:
                        self.image = tvinfo[0]
                    self.skin_fxd = tvinfo[3]
                    self.mplayer_options = tvinfo[2]
                self.tv_show       = True
                self.show_name     = show_name
                self.tv_show_name  = show_name[0]
                self.tv_show_ep    = show_name[3]
                
        # extra infos in discset_informations
        if parent and parent.media:
            fid = parent.media.id + \
                  self.filename[len(os.path.join(parent.media.mountdir,"")):]
            if discset_informations.has_key(fid):
                self.mplayer_options = discset_informations[fid]

        
    def set_url(self, url, info=True):
        """
        Sets a new url to the item. Always use this function and not set 'url'
        directly because this functions also changes other attributes, like
        filename, mode and network_play
        """
        MediaItem.set_url(self, url, info)
        if url.startswith('dvd://') or url.startswith('vcd://'):
            self.network_play = False
            self.mimetype = self.url[:self.url.find('://')].lower()
            if self.url.find('/VIDEO_TS/') > 0:
                # dvd on harddisc
                self.filename = self.url[5:self.url.rfind('/VIDEO_TS/')]
                self.info     = util.mediainfo.get(self.filename)
                self.files    = FileInformation()
                self.name     = self.info['title:filename']
                if not self.name:
                    self.name = util.getname(self.filename)
                self.files.append(self.filename)
            elif self.url.rfind('.iso') + 4 == self.url.rfind('/'):
                # iso
                self.filename = self.url[5:self.url.rfind('/')]
            else:
                self.filename = ''
                
        elif url.endswith('.iso') and self.info['mime'] == 'video/dvd':
            self.mimetype = 'dvd'
            self.mode     = 'dvd'
            self.url      = 'dvd' + self.url[4:] + '/'
            
        if not self.image or (self.parent and self.image == self.parent.image):
           image = vfs.getoverlay(self.filename + '.raw')
           if os.path.exists(image):
               self.image = image
               self.files.image = image

        if config.VIDEO_INTERLACING and self.info['interlaced'] \
               and not self['deinterlace']:
            # force deinterlacing
            self['deinterlace'] = 1
               
        
    def id(self):
        """
        Return a unique id of the item. This id should be the same when the
        item is rebuild later with the same informations
        """
        ret = self.url
        if self.subitems:
            for s in self.subitems:
                ret += s.id()
        if self.variants:
            for v in self.variants:
                ret += v.id()
        return ret


    def __getitem__(self, key):
        """
        return the specific attribute
        """
        if key == 'geometry' and self.info['width'] and self.info['height']:
            return '%sx%s' % (self.info['width'], self.info['height'])

        if key == 'aspect' and self.info['aspect']:
            aspect = str(self.info['aspect'])
            return aspect[:aspect.find(' ')].replace('/', ':')
            
        if key == 'runtime':
            length = None

            if self.info['runtime'] and self.info['runtime'] != 'None':
                length = self.info['runtime']
            elif self.info['length'] and self.info['length'] != 'None':
                length = self.info['length']
            if not length and hasattr(self, 'length'):
                length = self.length
            if not length:
                return ''

            if isinstance(length, int) or isinstance(length, float) or \
                   isinstance(length, long):
                length = str(int(round(length) / 60))
            if length.find('min') == -1:
                length = '%s min' % length
            if length.find('/') > 0:
                length = length[:length.find('/')].rstrip()
            if length.find(':') > 0:
                length = length[length.find(':')+1:]
            if length == '0 min':
                return ''
            return length

        return MediaItem.__getitem__(self, key)

    
    def sort(self, mode=None):
        """
        Returns the string how to sort this item
        """
        if mode == 'date' and self.mode == 'file' and \
               os.path.isfile(self.filename):
            return u'%s%s' % (os.stat(self.filename).st_ctime,
                              Unicode(self.filename))
        if self.name.find(u"The ") == 0:
            return self.name[4:]
        return self.name


    def _set_next_available_subitem(self):
        """
        select the next available subitem. Loops on each subitem and checks if
        the needed media is really there.
        If the media is there, sets self.current_subitem to the given subitem
        and returns 1.
        If no media has been found, we set self.current_subitem to None.
          If the search for the next available subitem did start from the
            beginning of the list, then we consider that no media at all was
            available for any subitem: we return 0.
          If the search for the next available subitem did not start from the
            beginning of the list, then we consider that at least one media
            had been found in the past: we return 1.
        """
        if hasattr(self, 'conf_select_this_item'):
            # XXX bad hack, clean me up
            self.current_subitem = self.conf_select_this_item
            del self.conf_select_this_item
            return True
            
        cont = 1
        from_start = 0
        si = self.current_subitem
        while cont:
            if not si:
                # No subitem selected yet: take the first one
                si = self.subitems[0]
                from_start = 1
            else:
                pos = self.subitems.index(si)
                # Else take the next one
                if pos < len(self.subitems)-1:
                    # Let's get the next subitem
                    si = self.subitems[pos+1]
                else:
                    # No next subitem
                    si = None
                    cont = 0
            if si:
                if (si.media_id or si.media):
                    # If the file is on a removeable media
                    if util.check_media(si.media_id):
                        self.current_subitem = si
                        return 1
                    elif si.media and util.check_media(si.media.id):
                        self.current_subitem = si
                        return 1
                else:
                    # if not, it is always available
                    self.current_subitem = si
                    return 1
        self.current_subitem = None
        return not from_start


    def _get_possible_player(self):
        """
        return a list of possible player for this item
        """
        possible_player = []
        for p in plugin.getbyname(plugin.VIDEO_PLAYER, True):
            rating = p.rate(self) * 10
            if config.VIDEO_PREFERED_PLAYER == p.name:
                rating += 1
            if hasattr(self, 'force_player') and p.name == self.force_player:
                rating += 100
            possible_player.append((rating, p))
        possible_player.sort(lambda l, o: -cmp(l[0], o[0]))
        return possible_player
    
        
    # ------------------------------------------------------------------------
    # actions:


    def actions(self):
        """
        return a list of possible actions on this item.
        """
        self.possible_player = self._get_possible_player()

        if not self.possible_player:
            self.player = None
            self.player_rating = 0
            return []

        self.player_rating, self.player = self.possible_player[0]

        # For DVD and VCD check if the rating is >= 20. If it is and the url
        # ends with '/', the user should get the DVD/VCD menu from the player.
        # If not, we need to show the title menu.
        if self.url.startswith('dvd://') and self.url[-1] == '/':
            if self.player_rating >= 20:
                items = [ (self.play, _('Play DVD')),
                          ( self.dvd_vcd_title_menu, _('DVD title list') ) ]
            else:
                items = [ ( self.dvd_vcd_title_menu, _('DVD title list') ),
                          (self.play, _('Play default track')) ]
                    
        elif self.url == 'vcd://':
            if self.player_rating >= 20:
                items = [ (self.play, _('Play VCD')),
                          ( self.dvd_vcd_title_menu, _('VCD title list') ) ]
            else:
                items = [ ( self.dvd_vcd_title_menu, _('VCD title list') ),
                          (self.play, _('Play default track')) ]
        else:
            items = [ (self.play, _('Play')) ]
            if len(self.possible_player) > 1:
                items.append((self.play_alternate,
                              _('Play with alternate player')))

        # Network play can get a larger cache
        if self.network_play:
            items.append((self.play_max_cache, _('Play with maximum cache')))

        # Add the configure stuff (e.g. set audio language)
        items += configure.get_items(self)

        # If there are variants, make it possible to show them. This is
        # always the default action then.
        if self.variants and len(self.variants) > 1:
            items = [ (self.show_variants, _('Show variants')) ] + items

        # Add thumbnail option
        if self.mode == 'file' and not self.variants and \
               not self.subitems and \
               (not self.image or not self.image.endswith('raw')):
            items.append((self.create_thumbnail, _('Create Thumbnail'),
                          'create_thumbnail'))
        return items


    def show_variants(self, arg=None, menuw=None):
        """
        show a list of variants in a menu
        """
        m = menu.Menu(self.name, self.variants, reload_func=None,
                      theme=self.skin_fxd)
        m.item_types = 'video'
        menuw.pushmenu(m)


    def dvd_vcd_title_menu(self, arg=None, menuw=None):
        """
        Generate special menu for DVD/VCD/SVCD content
        """
        # delete the submenu that got us here
        menuw.delete_submenu(False)
        
        # build a menu
        items = []
        for title in range(len(self.info['tracks'])):
            i = copy.copy(self)
            i.parent = self
            i.set_url(self.url + str(title+1), False)
            i.info = copy.copy(self.info)
            # copy the attributes from mmpython about this track
            i.info.mmdata = self.info.mmdata['tracks'][title]
            i.info.set_variables(self.info.get_variables())
            i.info_type       = 'track'
            i.possible_player = []
            i.files           = None
            i.name            = Unicode(_('Play Title %s')) % (title+1)
            items.append(i)

        moviemenu = menu.Menu(self.name, items, umount_all = 1,
                              theme=self.skin_fxd)
        moviemenu.item_types = 'video'
        menuw.pushmenu(moviemenu)


    def create_thumbnail(self, arg=None, menuw=None):
        """
        create a thumbnail as image icon
        """
        pop = PopupBox(text=_('Please wait....'))
        pop.show()
        util.videothumb.snapshot(self.filename)
        pop.destroy()
        if menuw.menustack[-1].selected != self:
            menuw.back_one_menu()


    def play_max_cache(self, arg=None, menuw=None):
        """
        play and use maximum cache with mplayer
        """
        self.play(menuw=menuw, arg='-cache 65536')

        
    def play_alternate(self, arg=None, menuw=None):
        """
        play and use maximum cache with mplayer
        """
        self.play(menuw=menuw, arg=arg, alternateplayer=True)


    def play(self, arg=None, menuw=None, alternateplayer=False):
        """
        play the item.
        """
        # set the current_item of the parent to this one
        # to make playlists possible
	if self.parent:
            self.parent.current_item = self

        # make sure we have a menuw and a self.menuw. This bad code
        # is needed because of all the subitems and variants and they
        # can be called without a menuw sometimes.
        if menuw:
            self.menuw = menuw
        else:
            menuw = self.menuw
            
        if self.variants:
            # if we have variants, play the first one as default
            self.variants[0].play(arg, menuw)
            return

        if self.subitems:
            # if we have subitems (a movie with more than one file),
            # we start playing the first that is physically available
            self.error_in_subitem = 0
            self.last_error_msg   = ''
            self.current_subitem  = None

            result = self._set_next_available_subitem()
            if self.current_subitem: # 'result' is always 1 in this case
                # The media is available now for playing
                # Pass along the options, without loosing the subitem's own
                # options
                if self.current_subitem.mplayer_options:
                    if self.mplayer_options:
                        mo = self.current_subitem.mplayer_options
                        mo += ' ' + self.mplayer_options
                        self.current_subitem.mplayer_options = mo
                else:
                    self.current_subitem.mplayer_options = self.mplayer_options
                # When playing a subitem, the menu must be hidden. If it is
                # not, the playing will stop after the first subitem, since the
                # PLAY_END/USER_END event is not forwarded to the parent
                # videoitem.
                # And besides, we don't need the menu between two subitems.
                self.last_error_msg=self.current_subitem.play(arg, menuw)
                if self.last_error_msg:
                    self.error_in_subitem = 1
                    # Go to the next playable subitem, using the loop in
                    # eventhandler()
                    self.eventhandler(PLAY_END)
                    
            elif not result:
                # No media at all was found: error
                ConfirmBox(text=(_('No media found for "%s".\n')+
                                 _('Please insert the media.')) %
                                 self.name, handler=self.play ).show()
            # done, everything else is handled in 'play' of the subitem
            return

        if self.url.startswith('file://'):
            # normal playback of one file
            file = self.filename
            if self.media_id:
                # This file is on a media with media_id as id. Check
                # if this media is inserted somewere
                mountdir,file = util.resolve_media_mountdir(self.media_id,file)
                if mountdir:
                    # Found, mount the disc
                    util.mount(mountdir)
                else:
                    # Not found, show box so the user can insert the
                    # correct disc. Callback is this function again
                    ConfirmBox(text=(_('No media found for "%s".\n')+
                                     _('Please insert the media.')) % file,
                               handler=self.play ).show()
                    return

            elif self.media:
                # mount 'our' media
                util.mount(os.path.dirname(self.filename))

        elif self.mode in ('dvd', 'vcd') and not self.filename and \
                 not self.media:
            # DVD/VCD playing a no media defined. We need to search if the
            # disc is inserted somewere.
            media = util.check_media(self.media_id)
            if media:
                self.media = media
            else:
                # Not found, show box so the user can insert the
                # correct disc. Callback is this function again
                ConfirmBox(text=(_('No media found for "%s".\n')+
                                 _('Please insert the media.')) % self.url,
                           handler=self.play).show()
                return

        # get the correct player for this item and check the
        # rating if the player can play this item or not
        if not self.possible_player:
            self.possible_player = self._get_possible_player()
        
        if alternateplayer:
            self.possible_player.reverse()

        if not self.possible_player:
            return

        self.player_rating, self.player = self.possible_player[0]
        if self.player_rating < 10:
            AlertBox(text=_('No player for this item found')).show()
            return

        # put together the mplayer options for this file
        mplayer_options = self.mplayer_options.split(' ')
        if not mplayer_options:
            mplayer_options = []
        if arg:
            mplayer_options += arg.split(' ')

        # call all our plugins to let them know we will play
        self.plugin_eventhandler(PLAY, menuw)

        # call the player to play the item
        error = self.player.play(mplayer_options, self)

        if error:
            # If we are a subitem we don't show any error message before
            # having tried all the subitems
            if hasattr(self.parent, 'subitems') and self.parent.subitems:
                return error
            else:
                AlertBox(text=error, handler=self.error_handler).show()


    def error_handler(self):
        """
        error handler if play doesn't work to send the end event and stop
        the player
        """
        eventhandler.post(PLAY_END)
        self.stop()


    def stop(self, arg=None, menuw=None):
        """
        stop playing
        """
        if self.player:
            self.player.stop()


    def eventhandler(self, event, menuw=None):
        """
        eventhandler for this item
        """
        if self.plugin_eventhandler(event):
            return True

        # PLAY_END: do we have to play another file?
        if self.subitems and not self.variants:
            if event == PLAY_END:
                self._set_next_available_subitem()
                # Loop until we find a subitem which plays without error
                while self.current_subitem: 
                    _debug_('playing next item')
                    error = self.current_subitem.play()
                    if error:
                        self.last_error_msg = error
                        self.error_in_subitem = 1
                        self._set_next_available_subitem()
                    else:
                        return True
                if self.error_in_subitem:
                    # No more subitems to play, and an error occured
                    AlertBox(text=self.last_error_msg).show()
                    
            elif event == USER_END:
                pass

        # show configure menu
        if event == MENU:
            if self.player:
                self.player.stop()
            confmenu = configure.get_menu(self, self.menuw)
            self.menuw.pushmenu(confmenu)
            return True
        
        return MediaItem.eventhandler(self, event)
