## 
## Created       : Tue Jul 26 06:54:41 IST 2011
## Last Modified : Sun Apr 08 08:06:22 IST 2012
## 
## Copyright (C) 2011, 2012 by Sriram Karra <karra.etc@gmail.com>
## 
## Licensed under the GPL v3
## 

import re

def chompq (s):
    """Remove any leading and trailing quotes from the passed string."""
    if len(s) < 2:
        return s

    if s[0] == '"' and s[len(s)-1] == '"':
        return s[1:len(s)-1]
    else:
        return s

## The follow is a super cool implementation of enum equivalent in
## Python. Taken with a lot of gratitude from this post on Stackoverflow:
## http://stackoverflow.com/a/1695250/987738
##
## It is used like so: Numbers = enum(ONE=1, TWO=2, THREE='three')
## and, Numbers = enum('ZERO', 'ONE', 'TWO') # for auto initialization
def enum(*sequential, **named):
	enums = dict(zip(sequential, range(len(sequential))), **named)
	return type('Enum', (), enums)


def get_sync_label_from_dbid (config, dbid):
    ret =  (config.get_label_prefix() +
            config.get_label_separator() +
            dbid + config.get_label_separator() + 'id')

    return ret

def get_dbid_from_sync_label (config, label):
    pre = config.get_label_prefix()
    sep = config.get_label_separator()
    reg =  (pre + sep + '([a-z0-9]+)' + sep + 'id')
    res = re.match(reg, label)
    if res:
        return res.group(1)
    else:
        return None

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
