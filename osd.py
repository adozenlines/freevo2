#if 0 /*
# -----------------------------------------------------------------------
# osd.py - Low level graphics routines
#
# This is the class for using the SDL OSD functions. It will eventually
# replace the current osd.py
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.22  2002/09/24 03:21:46  gsbarbieri
# Changed stringsize() to _stringsize(). The stringsize() is still avaiable,
# but now it uses the charsize() to cache values.
# charsize() use dictionaries to store calculated values. charsize() actually
# stores everything (char or strings) in the cache structure, but please make
# the correct use of it, only pass chars to it. To get string's size, please
# use stringsize().
#
# Revision 1.21  2002/09/21 10:12:11  dischi
# Moved osd.popup_box to skin.PopupBox. A popup box should be part of the
# skin.
#
# Revision 1.20  2002/09/08 18:26:03  krister
# Applied Andrew Drummond's MAME patch. It seems to work OK on X11, but still needs some work before it is ready for prime-time...
#
# Revision 1.19  2002/09/07 06:16:51  krister
# Cleanup.
#
# Revision 1.18  2002/09/01 05:15:55  krister
# Switched to the new freely distributable fonts.
#
# Revision 1.17  2002/09/01 04:12:04  krister
# Added error checking for font rendering.
#
# Revision 1.16  2002/08/31 17:18:29  dischi
# added function to delete a bitmap from cache
#
# Revision 1.15  2002/08/21 04:58:26  krister
# Massive changes! Obsoleted all osd_server stuff. Moved vtrelease and matrox stuff to a new dir fbcon. Updated source to use only the SDL OSD which was moved to osd.py. Changed the default TV viewing app to mplayer_tv.py. Changed configure/setup_build.py/config.py/freevo_config.py to generate and use a plain-text config file called freevo.conf. Updated docs. Changed mplayer to use -vo null when playing music. Fixed a bug in music playing when the top dir was empty.
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
#endif

import socket, time, sys, os

# Configuration file. Determines where to look for AVI/MP3 files, etc
import config

# The PyGame Python SDL interface.
import pygame
from pygame.locals import *

# Set to 1 for debug output
DEBUG = 0

help_text = """\
h       HELP
z       Toggle Fullscreen
F1      SLEEP
HOME    MENU
g       GUIDE
ESCAPE  EXIT
UP      UP
DOWN    DOWN
LEFT    LEFT
RIGHT   RIGHT
SPACE   SELECT
RETURN  SELECT
F2      POWER
F3      MUTE
PLUS    VOL+
MINUS   VOL-
c       CH+
v       CH-
1       1
2       2
3       3
4       4
5       5
6       6
7       7
8       8
9       9
0       0
d       DISPLAY
e       ENTER
_       PREV_CH
o       PIP_ONOFF
w       PIP_SWAP
i       PIP_MOVE
F4      TV_VCR
r       REW
p       PLAY
f       FFWD
u       PAUSE
s       STOP
F6      REC
PERIOD  EJECT
F10     Screenshot
"""


cmds_sdl = {
    K_F1          : 'SLEEP',
    K_HOME        : 'MENU',
    K_g           : 'GUIDE',
    K_ESCAPE      : 'EXIT',
    K_UP          : 'UP',
    K_DOWN        : 'DOWN',
    K_LEFT        : 'LEFT',
    K_RIGHT       : 'RIGHT',
    K_SPACE       : 'SELECT',
    K_RETURN      : 'SELECT',
    K_F2          : 'POWER',
    K_F3          : 'MUTE',
    K_PLUS        : 'VOL+',
    K_MINUS       : 'VOL-',
    K_c           : 'CH+',
    K_v           : 'CH-',
    K_1           : '1',
    K_2           : '2',
    K_3           : '3',
    K_4           : '4',
    K_5           : '5',
    K_6           : '6',
    K_7           : '7',
    K_8           : '8',
    K_9           : '9',
    K_0           : '0',
    K_d           : 'DISPLAY',
    K_e           : 'ENTER',
    K_UNDERSCORE  : 'PREV_CH',
    K_o           : 'PIP_ONOFF',
    K_w           : 'PIP_SWAP',
    K_i           : 'PIP_MOVE',
    K_F4          : 'TV_VCR',
    K_r           : 'REW',
    K_p           : 'PLAY',
    K_f           : 'FFWD',
    K_u           : 'PAUSE',
    K_s           : 'STOP',
    K_F6          : 'REC',
    K_PERIOD      : 'EJECT'
    }

# Module variable that contains an initialized OSD() object
_singleton = None

def get_singleton():
    global _singleton

    # One-time init
    if _singleton == None:
        _singleton = SynchronizedObject(OSD())
        
    return _singleton

        
class Font:

    filename = ''
    ptsize = 0
    font = None


class OSD:

    _started = 0
    
    # The colors
    # XXX Add more
    COL_RED = 0xff0000
    COL_GREEN = 0x00ff00
    COL_BLUE = 0x0000ff
    COL_BLACK = 0x000000
    COL_WHITE = 0xffffff
    COL_SOFT_WHITE = 0xEDEDED
    COL_MEDIUM_YELLOW = 0xFFDF3E
    COL_SKY_BLUE = 0x6D9BFF
    COL_DARK_BLUE = 0x0342A0
    COL_ORANGE = 0xFF9028
    COL_MEDIUM_GREEN = 0x54D35D
    COL_DARK_GREEN = 0x038D11

    stringsize_cache = { }


    def __init__(self):

        self.fontcache = []
        self.stringcache = []
        self.bitmapcache = []
        
        self.default_fg_color = self.COL_BLACK
        self.default_bg_color = self.COL_WHITE

        self.width = config.CONF.width
        self.height = config.CONF.height

        # Initialize the PyGame modules.
        pygame.init()

        # The mixer module must not be running, it will
        # prevent sound from working.
        try:
            pygame.mixer.quit()
        except NotImplementedError, MissingPygameModule:
            pass # Ok, we didn't have the mixer module anyways

        self.screen = pygame.display.set_mode((self.width, self.height), 0, 32)

        help = ['z = Toggle Fullscreen']
        help += ['Arrow Keys = Move']
        help += ['Spacebar = Select']
        help += ['Escape = Stop/Prev. Menu']
        help += ['h = Help']
        help_str = '    '.join(help)
        pygame.display.set_caption('Freevo' + ' '*7 + help_str)
        icon = pygame.image.load('icons/freevo_app.png').convert()
        pygame.display.set_icon(icon)
        
        self.clearscreen(self.COL_BLACK)
        self.update()

        if config.OSD_SDL_EXEC_AFTER_STARTUP:
            os.system(config.OSD_SDL_EXEC_AFTER_STARTUP)

        self.sdl_driver = pygame.display.get_driver()

        pygame.mouse.set_visible(0)
        self.mousehidetime = time.time()
        
        self._started = 1
        self._help = 0  # Is the helpscreen displayed or not
        self._help_saved = pygame.Surface((self.width, self.height), 0, 32)
        self._help_last = 0

        # Remove old screenshots
        os.system('rm -f /tmp/freevo_ss*.bmp')
        self._screenshotnum = 1
        

    def _cb(self):

        if not pygame.display.get_init():
            return None

        # Check if mouse should be visible or hidden
        mouserel = pygame.mouse.get_rel()
        mousedist = (mouserel[0]**2 + mouserel[1]**2) ** 0.5

        if mousedist > 4.0:
            pygame.mouse.set_visible(1)
            self.mousehidetime = time.time() + 1.0  # Hide the mouse in 2s
        else:
            if time.time() > self.mousehidetime:
                pygame.mouse.set_visible(0)
        
        event = pygame.event.poll()
        if event.type == NOEVENT:
            return None

        if event.type == KEYDOWN:
            if event.key == K_h:
                self._helpscreen()
            elif event.key == K_z:
                pygame.display.toggle_fullscreen()
            elif event.key == K_F10:
                # Take a screenshot
                pygame.image.save(self.screen,
                                  '/tmp/freevo_ss%s.bmp' % self._screenshotnum)
                self._screenshotnum += 1
            elif event.key in cmds_sdl.keys():
                # Turn off the helpscreen if it was on
                if self._help:
                    self._helpscreen()
                    
                return cmds_sdl[event.key]

    
    def _send(arg1, *arg, **args): # XXX remove
        pass

    
    def shutdown(self):
        pygame.quit()

    def restartdisplay(self):
        pygame.display.init()
        self.width = config.CONF.width
        self.height = config.CONF.height
        self.screen = pygame.display.set_mode((self.width, self.height), 0, 32)

    def stopdisplay(self):
        pygame.display.quit()

    def clearscreen(self, color=None):
        if not pygame.display.get_init():
            return None

        if color == None:
            color = self.default_bg_color
        self.screen.fill(self._sdlcol(color))
        

    def setpixel(self, x, y, color):
        pass # XXX Not used anywhere


    # Bitmap buffers in Freevo:
    #
    # There are 4 different bitmap buffers in the system.
    # 1) The load bitmap buffer
    # 2) The zoom bitmap buffer
    # 3) The OSD drawing buffer
    # 4) The screen (fb/x11/sdl) buffer
    #
    # Drawing operations (text, line, etc) operate on the
    # OSD drawing buffer, and are copied to the screen buffer
    # using update().
    #
    # The drawbitmap() operation is time-consuming for larger
    # images, which is why the load, zoom, and draw operations each
    # have their own buffer. This can speed up things if the
    # application is pipelined to preload/prezoom the bitmap
    # where the next bitmap file is known in advance, or the same
    # portions of the same bitmap is zoomed repeatedly.
    # 

    # Caches a bitmap in the OSD without displaying it.
    def loadbitmap(self, filename):
        self._getbitmap(filename)
    

    # Loads and zooms a bitmap and return the surface. A cache is currently
    # missing, but maybe we don't need it, it's fast enough.
    def zoombitmap(self, filename, scaling=None, bbx=0, bby=0, bbw=0, bbh=0, rotation = 0):
        if not pygame.display.get_init():
            return None

        image = self._getbitmap(filename)

        if not image: return

        if bbx or bby or bbw or bbh:
            imbb = pygame.Surface((bbw, bbh), 0, 32)
            imbb.blit(image, (0, 0), (bbx, bby, bbw, bbh))
            image = imbb
            
        if scaling:
            w, h = image.get_size()
            w = int(w*scaling)
            h = int(h*scaling)
            if rotation:
                image = pygame.transform.rotozoom(image, rotation, scaling)
            else:
                image = pygame.transform.scale(image, (w, h))

        elif rotation:
            image = pygame.transform.rotate(image, rotation)

        return image

    
        
    # Draw a bitmap on the OSD. It is automatically loaded into the cache
    # if not already there. The loadbitmap()/zoombitmap() functions can
    # be used to "pipeline" bitmap loading/drawing.
    def drawbitmap(self, filename, x=0, y=0, scaling=None,
                   bbx=0, bby=0, bbw=0, bbh=0, rotation = 0):
        if not pygame.display.get_init():
            return None
        image = self.zoombitmap(filename, scaling, bbx, bby, bbw, bbh, rotation)
        if not image: return
        self.screen.blit(image, (x, y))


    def bitmapsize(self, filename):
        if not pygame.display.get_init():
            return None
        image = self._getbitmap(filename)
        if not image: return 0,0
        return image.get_size()


    def drawline(self, x0, y0, x1, y1, width=None, color=None):
        if not pygame.display.get_init():
            return None
        if width == None:
            width = 1

        if color == None:
            color = self.default_fg_color

        args1 = str(x0) + ';' + str(y0) + ';'
        args2 = str(x1) + ';' + str(y1) + ';' + str(width) + ';' + str(color)
        self._send('drawline;' + args1 + args2)


    def drawbox(self, x0, y0, x1, y1, width=None, color=None, fill=0):
        if not pygame.display.get_init():
            return None

        # Make sure the order is top left, bottom right
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        
        if color == None:
            color = self.default_fg_color
            
        if width == None:
            width = 1

        if width == -1 or fill:
            r,g,b,a = self._sdlcol(color)
            w = x1 - x0
            h = y1 - y0
            box = pygame.Surface((w, h), 0, 32)
            box.fill((r,g,b))
            box.set_alpha(a)
            self.screen.blit(box, (x0, y0))
        else:
            r = (x0, y0, x1-x0, y1-y0)
            c = self._sdlcol(color)
            pygame.draw.rect(self.screen, c, r, width)
            

    def drawstring(self, string, x, y, fgcolor=None, bgcolor=None,
                   font=None, ptsize=0, align='left'):

        if not pygame.display.get_init():
            return None

        # XXX Krister: Workaround for new feature that is only possible in the new
        # XXX SDL OSD, line up columns delimited by tabs. Here the tabs are just
        # XXX replaced with spaces
        s = string.replace('\t', '   ')  

        if DEBUG: print 'drawstring (%d;%d) "%s"' % (x, y, s)
        
        if fgcolor == None:
            fgcolor = self.default_fg_color
        if font == None:
            font = config.OSD_DEFAULT_FONTNAME

        if not ptsize:
            ptsize = config.OSD_DEFAULT_FONTSIZE

        ptsize = int(ptsize / 0.7)  # XXX pygame multiplies by 0.7 for some reason

        if DEBUG: print 'FONT: %s %s' % (font, ptsize)
        
        ren = self._renderstring(s, font, ptsize, fgcolor, bgcolor)
        
        # Handle horizontal alignment
        w, h = ren.get_size()
        tx = x # Left align is default
        if align == 'center':
            tx = x - w/2
        elif align == 'right':
            tx = x - w
            
        self.screen.blit(ren, (tx, y))


    # Render a string to an SDL surface. Uses a cache for speedup.
    def _renderstring(self, string, font, ptsize, fgcolor, bgcolor):

        if not pygame.display.get_init():
            return None

        f = self._getfont(font, ptsize)

        if not f:
            print 'Couldnt get font: "%s", size: %s' % (font, ptsize)
            return
        
        for i in range(len(self.stringcache)):
            csurf, cstring, cfont, cfgcolor, cbgcolor = self.stringcache[i]
            if (f == cfont and string == cstring and fgcolor == cfgcolor
                and bgcolor == cbgcolor):
                # Move to front of FIFO
                del self.stringcache[i]
                self.stringcache.append((csurf, cstring, cfont, cfgcolor, cbgcolor))
                return csurf

        # Render string with anti-aliasing
        if bgcolor == None:
            try:
                surf = f.render(string, 1, self._sdlcol(fgcolor))
            except:
                print 'FAILED: str="%s" col="%s"' % (string, fgcolor)
                raise
        else:
            surf = f.render(string, 1, self._sdlcol(fgcolor), self._sdlcol(bgcolor))

        # Store the surface in the FIFO
        self.stringcache.append((surf, string, f, fgcolor, bgcolor))
        if len(self.stringcache) > 100:
            del self.stringcache[0]

        return surf

    # Return a (width, height) tuple for the given char, font, size. Use CACHE to speed up things
    # Gustavo: This function make use of dictionaries to cache values, so we don't have to calculate them all the time
    def charsize(self, char, font=None, ptsize=0):
        if self.stringsize_cache.has_key(font):
            if self.stringsize_cache[font].has_key(ptsize):
                if not self.stringsize_cache[font][ptsize].has_key(char):
                    self.stringsize_cache[font][ptsize][char] = self._stringsize(char,font,ptsize)
            else:
                self.stringsize_cache[font][ptsize] = {}
                self.stringsize_cache[font][ptsize][char] = self._stringsize(char,font,ptsize)
        else:
            self.stringsize_cache[font] = {}
            self.stringsize_cache[font][ptsize] = {}
            self.stringsize_cache[font][ptsize][char] = self._stringsize(char,font,ptsize)
        return self.stringsize_cache[font][ptsize][char]


    # Return a (width, height) tuple for the given string, font, size
    # Gustavo: use the charsize() to speed up things
    def stringsize(self, string, font=None, ptsize=0):
        size_w = 0
        size_h = 0
        for i in range(len(string)):
            size_w_tmp, size_h_tmp = self.charsize(string[i], font, ptsize)
            size_w += size_w_tmp
            if size_h_tmp > size_h:
                size_h = size_h_tmp
                
        return (size_w, size_h)
    

    # Return a (width, height) tuple for the given string, font, size
    # Gustavo: Don't use this function directly. Use stringsize(), it is faster (use cache)
    def _stringsize(self, string, font=None, ptsize=0):
        if not pygame.display.get_init():
            return None

        if not ptsize:
            ptsize = config.OSD_DEFAULT_FONTSIZE

        ptsize = int(ptsize / 0.7)  # XXX pygame multiplies with 0.7 for some reason

        f = self._getfont(font, ptsize)

        if string:
            return f.size(string)
        else:
            return (0, 0)
        

    def update(self):

        if not pygame.display.get_init():
            return None

        pygame.display.flip()


    def _getfont(self, filename, ptsize):
        if not pygame.display.get_init():
            return None

        for font in self.fontcache:
            if font.filename == filename and font.ptsize == ptsize:
                return font.font

        if DEBUG: print 'OSD: Loading font "%s"' % filename
        font = pygame.font.Font(filename, ptsize)
        f = Font()
        f.filename = filename
        f.ptsize = ptsize
        f.font = font
        
        self.fontcache.append(f)

        return f.font

        
    def _getbitmap(self, filename):
        if not pygame.display.get_init():
            return None

        if not os.path.isfile(filename):
            print 'Bitmap file "%s" doesnt exist!' % filename
            return None
        
        for i in range(len(self.bitmapcache)):
            fname, image = self.bitmapcache[i]
            if fname == filename:
                # Move to front of FIFO
                del self.bitmapcache[i]
                self.bitmapcache.append((fname, image))
                return image

        try:
            if DEBUG: print 'Trying to load file "%s"' % filename
            tmp = pygame.image.load(filename)  # XXX Cannot load everything
            image = tmp.convert_alpha()  # XXX Cannot load everything
        except:
            print 'SDL image load problem!'
            return None

        # FIFO for images
        self.bitmapcache.append((filename, image))
        if len(self.bitmapcache) > 30:
            del self.bitmapcache[0]

        return image

    def _deletefromcache(self, filename):
        for i in range(len(self.bitmapcache)):
            fname, image = self.bitmapcache[i]
            if fname == filename:
                del self.bitmapcache[i]
        
    def _helpscreen(self):
        if not pygame.display.get_init():
            return None

        self._help = {0:1, 1:0}[self._help]
        
        if self._help:
            if DEBUG: print 'Help on'
            # Save current display
            self._help_saved.blit(self.screen, (0, 0))
            self.clearscreen(self.COL_WHITE)
            lines = help_text.split('\n')

            row = 0
            col = 0
            for line in lines:
                x = 55 + col*250
                y = 50 + row*30

                ks = line[:8]
                cmd = line[8:]
                
                print '"%s" "%s" %s %s' % (ks, cmd, x, y)
                fname = 'skins/fonts/bluehigh.ttf'
                if ks: self.drawstring(ks, x, y, font=fname, ptsize=14)
                if cmd: self.drawstring(cmd, x+80, y, font=fname, ptsize=14)
                row += 1
                if row >= 15:
                    row = 0
                    col += 1

            self.update()
        else:
            if DEBUG: print 'Help off'
            self.screen.blit(self._help_saved, (0, 0))
            self.update()

        
    # Convert a 32-bit TRGB color to a 4 element tuple for SDL
    def _sdlcol(self, col):
        a = 255 - ((col >> 24) & 0xff)
        r = (col >> 16) & 0xff
        g = (col >> 8) & 0xff
        b = (col >> 0) & 0xff
        c = (r, g, b, a)
        return c
            


s = ("/hdc/krister_mp3/mp3/rage_against_the_machine-the_battle_of_los_angeles" +
       "-1999-bkf/02-Rage_Against_the_Machine-Guerilla_Radio-BKF.mp3")
#
# Simple test...
#
if __name__ == '__main__':
    osd = OSD()
    osd.clearscreen()
    osd.drawstring(s, 10, 10, font='skins/fonts/bluehigh.ttf', ptsize=14)
    osd.update()
    time.sleep(5)


#
# synchronized objects and methods.
# By Andr� Bj�rby
# From http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65202
# 
from types import *
def _get_method_names (obj):
    if type(obj) == InstanceType:
        return _get_method_names(obj.__class__)
    
    elif type(obj) == ClassType:
        result = []
        for name, func in obj.__dict__.items():
            if type(func) == FunctionType:
                result.append((name, func))

        for base in obj.__bases__:
            result.extend(_get_method_names(base))

        return result


class _SynchronizedMethod:

    def __init__ (self, method, obj, lock):
        self.__method = method
        self.__obj = obj
        self.__lock = lock

    def __call__ (self, *args, **kwargs):
        self.__lock.acquire()
        try:
            #print 'Calling method %s from obj %s' % (self.__method, self.__obj)
            return self.__method(self.__obj, *args, **kwargs)
        finally:
            self.__lock.release()


class SynchronizedObject:
    
    def __init__ (self, obj, ignore=[], lock=None):
        import threading

        self.__methods = {}
        self.__obj = obj
        lock = lock and lock or threading.RLock()
        for name, method in _get_method_names(obj):
            if not name in ignore:
                self.__methods[name] = _SynchronizedMethod(method, obj, lock)

    def __getattr__ (self, name):
        try:
            return self.__methods[name]
        except KeyError:
            return getattr(self.__obj, name)



