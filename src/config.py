# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# config.py - Handle the configuration files
# -----------------------------------------------------------------------------
# $Id$
#
# Try to find the freevo_config.py config file in the following places:
# 1) ./freevo_config.py               Defaults from the freevo dist
# 2) ~/.freevo/freevo_config.py       The user's private config
# 3) /etc/freevo/freevo_config.py     Systemwide config
# 
# Customize freevo_config.py from the freevo dist and copy it to one
# of the other places where it will not get overwritten by new
# checkouts/installs of freevo.
# 
# The format of freevo_config.py might change, in that case you'll
# have to update your customized version.
#
# Note: this file needs a huge cleanup!!!
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002-2005 Krister Lagerstrom, Dirk Meyer, et al.
#
# First Edition: Krister Lagerstrom <krister-freevo@kmlager.com>
#
# Please see the file doc/CREDITS for a complete list of authors.
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
import sys
import os
import re
import pwd
import logging
import copy

import kaa.strutils
import kaa.popcorn

import freevo.conf

# freevo imports
from freevo.ui import setup, input, plugin

# import event names
from freevo.ui.event import *

# get logging object
log = logging.getLogger('config')

#
# freevo.conf parser
#

class struct(object):
    pass

CONF = struct()
CONF.geometry = '800x600'
CONF.display = 'x11'
CONF.tv = 'ntsc'
CONF.version = 0

for dirname in freevo.conf.cfgfilepath:
    conffile = os.path.join(dirname, 'freevo.conf')
    if os.path.isfile(conffile):
        c = open(conffile)
        for line in c.readlines():
            if line.startswith('#'):
                continue
            if line.find('=') == -1:
                continue
            vals = line.strip().split('=')
            if not len(vals) == 2:
                print 'invalid config entry: %s' % line
                continue
            name, val = vals[0].strip(), vals[1].strip()
            CONF.__dict__[name] = val

        c.close()
        break
else:
    log.critical('freevo.conf not found, please run \'freevo setup\'')
    sys.exit(1)
    
kaa.popcorn.config.load('/etc/freevo/player.conf')
# if started as user add personal config file
if os.getuid() > 0:
    cfgdir = os.path.expanduser('~/.freevo')
    kaa.popcorn.config.load(os.path.join(cfgdir, 'player.conf'))

# save the file again in case it did not exist or the variables changed
kaa.popcorn.config.save()

w, h = CONF.geometry.split('x')
GUI_WIDTH, GUI_HEIGHT = int(w), int(h)

#
# Read the environment set by the start script
#
ICON_DIR  = os.path.join(freevo.conf.SHAREDIR, 'icons')
IMAGE_DIR = os.path.join(freevo.conf.SHAREDIR, 'images')


#
# search missing programs at runtime
#
for program, valname, needed in setup.EXTERNAL_PROGRAMS:
    if not hasattr(CONF, valname) or not getattr(CONF, valname):
        setup.check_program(CONF, program, valname, needed, verbose=0)
    if not hasattr(CONF, valname) or not getattr(CONF, valname):
        setattr(CONF, valname, '')

#
# Load freevo_config.py:
#
FREEVO_CONFIG = os.path.join(freevo.conf.SHAREDIR, 'freevo_config.py')
if os.path.isfile(FREEVO_CONFIG):
    log.info('Loading cfg: %s' % FREEVO_CONFIG)
    execfile(FREEVO_CONFIG, globals(), locals())
    
else:
    log.critical("Error: %s: no such file" % FREEVO_CONFIG)
    sys.exit(1)


#
# Search for local_conf.py:
#

has_config = False
for a in sys.argv:
    if has_config == True:
        has_config = a
    if a == '-c':
        has_config = True
    
for dirname in freevo.conf.cfgfilepath:
    if isinstance(has_config, str):
        overridefile = has_config
    else:
        overridefile = dirname + '/local_conf.py'
    if os.path.isfile(overridefile):
        log.info('Loading cfg overrides: %s' % overridefile)
        execfile(overridefile, globals(), locals())
        break

else:
    locations = ''
    for dirname in freevo.conf.cfgfilepath:
        locations += '  %s\n' % dirname
    log.critical("""local_conf.py not found
Freevo is not completely configured to start

The configuration is based on three files. This may sound oversized, but this
way it's easier to configure. First Freevo loads a file called 'freevo.conf'.
This file will be generated by 'freevo setup'. Use 'freevo setup --help' to get
information about the parameter. Based on the informations in that file, Freevo
will guess some settings for your system. This takes place in a file called
'freevo_config.py'. Since this file may change from time to time, you should
not edit this file. After freevo_config.py is loaded, Freevo will look for a
file called 'local_conf.py'. You can overwrite the variables from
'freevo_config.py' in here. There is an example for 'local_conf.py' called
'local_conf.py.example' in the Freevo distribution.
    
The location of freevo_config.py is %s
Freevo searches for freevo.conf and local_conf.py in the following locations:
%s

Since it's highly unlikly you want to start Freevo without further
configuration, Freevo will exit now.
"""  % (FREEVO_CONFIG, locations))
    sys.exit(0)

#
# force fullscreen when freevo is it's own windowmanager
#
if len(sys.argv) >= 2 and sys.argv[1] == '--force-fs':
    GUI_FULLSCREEN = 1


# make sure USER and HOME are set
os.environ['USER'] = pwd.getpwuid(os.getuid())[0]
os.environ['HOME'] = pwd.getpwuid(os.getuid())[5]

cfgfilepath = freevo.conf.cfgfilepath
