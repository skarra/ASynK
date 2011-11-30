#!/usr/bin/python
## 
## utils.py
##
## Created       : Tue Jul 26 06:54:41  2011
## Last Modified : Tue Nov 29 18:05:38 IST 2011
## 
## Copyright (C) 2011 by Sriram Karra <karra.etc@gmail.com>
## All rights reserved.
## 
## Licensed under the GPL v3
## 

import pywintypes

def yyyy_mm_dd_to_pytime (date_str):
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return pywintypes.Time(dt.timetuple())

def pytime_to_yyyy_mm_dd (pyt):
    return ('%04d-%02d-%02d' % (pyt.year, pyt.month, pyt.day))

def get_link_rel (links, rel):
    """From a Google data entry links array, fetch the link with the
    specifirf 'rel' attribute. examples of values for 'rel' could be:
    self, edit, etc."""

    for link in links:
        if link.rel == rel:
            return link.href

    return None

def get_event_rel (events, rel):
    """From a Google data entry events array, fetch and return the first event
    with the specified 'rel' attribute. examples of values for 'rel' could be:
    anniversary, etc."""

    for event in events:
        if event.rel == rel:
            return event.when

    return None

from   datetime import tzinfo, timedelta, datetime
import time as _time

# A class capturing the platform's idea of local time.

ZERO = timedelta(0)
STDOFFSET = timedelta(seconds = -_time.timezone)
if _time.daylight:
    DSTOFFSET = timedelta(seconds = -_time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET

class LocalTimezone(tzinfo):

    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def tzname(self, dt):
        return _time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, -1)
        stamp = _time.mktime(tt)
        tt = _time.localtime(stamp)
        return tt.tm_isdst > 0

localtz = LocalTimezone()

def utc_time_to_local_ts (t):
    """Convert a time object which is in UTC into a timestamp in local
    timezone"""

    utc_ts  = int(t)
    utc_off = localtz.utcoffset(datetime.now())
    d = datetime.fromtimestamp(utc_ts) + utc_off

    return _time.mktime(d.timetuple())
