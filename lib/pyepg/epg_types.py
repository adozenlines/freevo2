# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# epg_types.py - This file contains the types for the Freevo Electronic
#                Program Guide module.
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.1  2004/07/26 12:45:56  dischi
# first draft of pyepg (not integrated in Freevo)
#
# Revision 1.20  2004/07/10 12:33:41  dischi
# header cleanup
#
# Revision 1.19  2004/07/01 22:49:49  rshortt
# Unicode fix.
#
# Revision 1.18  2004/06/22 01:07:49  rshortt
# Move stuff into __init__() and fix a bug for twisted's serialization.
#
# Revision 1.17  2004/03/05 20:49:11  rshortt
# Add support for searching by movies only.  This uses the date field in xmltv
# which is what tv_imdb uses and is really acurate.  I added a date property
# to TvProgram for this and updated findMatches in the record_client and
# recordserver.
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


import sys
import copy
import time, os, string
import config


# Cache variables for last GetPrograms()
cache_last_start = None
cache_last_stop = None
cache_last_chanids = None
cache_last_result = None
cache_last_time = 0



class TvProgram:

    def __init__(self):
        self.channel_id = ''
        self.title      = ''
        self.desc       = ''
        self.sub_title  = ''
        self.start      = 0.0
        self.stop       = 0.0
        self.ratings    = {}
        self.advisories = []
        self.categories = []
        self.date       = None

        # Due to problems with Twisted's marmalade this should not be changed
        # to a boolean type. 
        self.scheduled  = 0


    def __str__(self):
        bt = time.localtime(self.start)   # Beginning time tuple
        et = time.localtime(self.stop)    # End time tuple
        begins = '%s-%02d-%02d %02d:%02d' % (bt[0], bt[1], bt[2], bt[3], bt[4])
        ends   = '%s-%02d-%02d %02d:%02d' % (et[0], et[1], et[2], et[3], et[4])

        s = '%s to %s  %3s %s' % (begins, ends, self.channel_id, self.title)
        return s


    def __cmp__(self, other):
        """
        compare function, return 0 if the objects are identical, 1 otherwise
        """
        if not other:
            return 1
        return self.title != other.title or \
               self.start != other.start or \
               self.stop  != other.stop or \
               self.channel_id != other.channel_id


    def getattr(self, attr):
        """
        return the specific attribute as string or an empty string
        """
        if attr == 'start':
            return Unicode(time.strftime(config.TV_TIMEFORMAT, time.localtime(self.start)))
        if attr == 'stop':
            return Unicode(time.strftime(config.TV_TIMEFORMAT, time.localtime(self.stop)))
        if attr == 'date':
            return Unicode(time.strftime(config.TV_DATEFORMAT, time.localtime(self.start)))
        if attr == 'time':
            return self.getattr('start') + u' - ' + self.getattr('stop')
        if hasattr(self, attr):
            return getattr(self,attr)
        return ''



class TvChannel:
    def __init__(self):
        self.id          = ''
        self.displayname = ''
        self.tunerid     = ''
        self.logo        = ''
        self.programs    = []
        self.times       = None

        
    def Sort(self):
        # Sort the programs so that the earliest is first in the list
        f = lambda a, b: cmp(a.start, b.start)
        self.programs.sort(f)
        

    def __str__(self):
        s = 'CHANNEL ID   %-20s' % self.id
        
        if self.programs:
            s += '\n'
            for program in self.programs:
                s += '   ' + String(program) + '\n'
        else:
            s += '     NO DATA\n'

        return s
    
        
class TvGuide:
    def __init__(self):
        # These two types map to the same channel objects
        self.chan_dict   = {}   # Channels mapped using the id
        self.chan_list   = []   # Channels, ordered
        self.EPG_VERSION = config.EPG_VERSION
        self.timestamp   = 0.0




    def AddChannel(self, channel):
        if not self.chan_dict.has_key(channel.id):
            # Add the channel to both the dictionary and the list. This works
            # well in Python since they will both point to the same object!
            self.chan_dict[channel.id] = channel
            self.chan_list.append(channel)

        
    def AddProgram(self, program):
        # The channel must be present, or the program is
        # silently dropped
        if self.chan_dict.has_key(program.channel_id):
            p = self.chan_dict[program.channel_id].programs
            if len(p) and p[-1].start < program.stop and p[-1].stop > program.start:
                # the tv guide is corrupt, the last entry has a stop time higher than
                # the next start time. Correct that by reducing the stop time of
                # the last entry
                if config.DEBUG > 1:
                    print 'wrong stop time: %s' % \
                          String(self.chan_dict[program.channel_id].programs[-1])
                self.chan_dict[program.channel_id].programs[-1].stop = program.start
                
            if len(p) and p[-1].start == p[-1].stop:
                # Oops, something is broken here
                self.chan_dict[program.channel_id].programs = p[:-1]
            self.chan_dict[program.channel_id].programs += [program]


    # Get all programs that occur at least partially between
    # the start and stop timeframe.
    # If start is None, get all programs from the start.
    # If stop is None, get all programs until the end.
    # The chanids can be used to select only certain channel id's,
    # all channels are returned otherwise
    #
    # The return value is a list of channels (TvChannel)
    def GetPrograms(self, start = None, stop = None, chanids = None):
        if start == None:
            start = 0
        if stop == None:
            stop = 2147483647   # Year 2038

        # Return a cached version?
        global cache_last_start, cache_last_stop, cache_last_chanids
        global cache_last_time, cache_last_result
        if (cache_last_start == start and cache_last_stop == stop and
            cache_last_chanids == chanids and
            time.time() < cache_last_time):
            if config.DEBUG > 1:
                a = cache_last_time - time.time()
                print 'epg: Returning cached results, valid for %1.1f secs.' % a
            return cache_last_result[:]  # Return a copy
        
        channels = []
        for chan in self.chan_list:
            if chanids and (not chan.id in chanids):
                continue

            # Copy the channel info
            c = TvChannel()
            c.id = chan.id
            c.displayname = chan.displayname
            c.tunerid = chan.tunerid
            c.logo = chan.logo
            c.times = chan.times
            # Copy the programs that are inside the indicated time bracket
            f = lambda p, a=start, b=stop: not (p.start > b or p.stop < a)
            c.programs = filter(f, chan.programs)

            channels.append(c)

        # Update cache variables
        cache_last_start = start
        cache_last_stop = stop
        if chanids:
            cache_last_chanids = chanids[:]
        else:
            cache_last_chanids = None
        cache_last_timeout = time.time() + 20
        cache_last_result = channels[:] # Make a copy in case the caller modifies it
        if config.DEBUG > 1:
            print 'epg: Returning new results'
            
        return channels
            
            
    def Sort(self):
        # Sort all channel programs in time order
        for chan in self.chan_list:
            chan.Sort()
        

    def __str__(self):
        s = 'XML TV Guide\n'

        for chan in self.chan_list:
            s += String(chan)

        return s
        
