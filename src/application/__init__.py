# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# application - Application Submodule
# -----------------------------------------------------------------------------
# $Id$
#
# Import information. This module depends on the following freevo.ui modules:
# freevo.ui.event   for the event definitions
# freevo.ui.menu    for the MenuWidget
# freevo.ui.gui     for gui callbacks
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2005-2007 Dirk Meyer, et al.
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

__all__ = [ 'Application', 'get_active', 'get_eventmap', 'signals',
            'STATUS_RUNNING', 'STATUS_STOPPING', 'STATUS_STOPPED', 'STATUS_IDLE',
            'CAPABILITY_TOGGLE', 'CAPABILITY_PAUSE', 'CAPABILITY_FULLSCREEN',
            'MenuWidget', 'TextWindow', 'MessageWindow', 'ConfirmWindow' ]

import sys

from base import Application, STATUS_RUNNING, STATUS_STOPPING, \
     STATUS_STOPPED, STATUS_IDLE, CAPABILITY_TOGGLE, CAPABILITY_PAUSE, \
     CAPABILITY_FULLSCREEN

from handler import handler as _handler
from window import TextWindow, MessageWindow, ConfirmWindow
from menuw import MenuWidget

def get_active():
    """
    Get active application.
    """
    return _handler.get_active()

def get_eventmap():
    """
    Return current eventmap.
    """
    return _handler.eventmap

# signals defined by the application base code
signals = _handler.signals
