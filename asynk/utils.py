## 
## Created : Tue Jul 26 06:54:41 IST 2011
## 
## Copyright (C) 2011, 2012, 2013 by Sriram Karra <karra.etc@gmail.com>
## 
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero GPL (GNU AGPL) as published by the
## Free Software Foundation, version 3 of the License
##
## ASynK is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
## FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
## License for more details.
##
## You should have a copy of the license in the doc/ directory of ASynK.  If
## not, see <http://www.gnu.org/licenses/>.
##

import iso8601, logging, os, re, xml.dom.minidom

time_start = "1980-01-01T00:00:00.00+00:00"

def yyyy_mm_dd_to_pytime (date_str):
    ## FIXME: Temporary hack to ensure we have a yyyy-mm-dd format. Google
    ## allows the year to be skipped. Outlook creates a problem. We bridge the
    ## gap by inserting '1887' (birth year of Srinivasa Ramanujan)

    import pywintypes

    res = re.search('--(\d\d)-(\d\d)', date_str)
    if res:
        date_str = '1887-%s-%s' % (res.group(1), res.group(2))

    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return pywintypes.Time(dt.timetuple())

def pytime_to_yyyy_mm_dd (pyt):
    if pyt.year == 1887:
        ## Undo the hack noted above.
        return ('--%02d-%02d' % (pyt.month, pyt.day))
    else:
        return ('%04d-%02d-%02d' % (pyt.year, pyt.month, pyt.day))

## Some Global Variables to get started
asynk_ver = 'v2.3.1+'

def asynk_ver_str ():
    return 'ASynK %s' % asynk_ver

def asynk_ts_to_iso8601 (ts):
    """The text timestamps in ASynK will be stored in a format that is readily
    usable by BBDB. Frequently there is a need to parse it into other formats,
    and as an intermediate step we would like to convert it into iso8601
    format to leverage the libraries available for handling iso8601. This
    routine converts a text string in the internal ASynK (BBDB) text format,
    into iso8601 format with Zone Specifier."""

    ## FIXME: All of these assume the timestamps are in UTC. Bad things can
    ## happen if some other timezone is provided.
    try:
        ## Eliminate the case where the input string is already in iso8601
        ## format... 
        iso8601.parse(ts)
        return ts
    except ValueError, e:
        return re.sub(r'(\d\d\d\d-\d\d-\d\d) (\d\d:\d\d:\d\d).*$',
                      r'\1T\2Z', ts)

def asynk_ts_parse (ts):
    """For historical reasons (IOW Bugs), ASynK versions have stored created
    and modified timestamps in two distinct text representations. This routine
    is a wrapper to gracefully handle both cases, convert it into a iso
    string, and then parse it into a python datetime object, which is returned
    """

    return iso8601.parse(asynk_ts_to_iso8601(ts))

def touch (fn):
    """Equivalent of the Unix 'touch' command."""

    with open(fn, 'a'):
        os.utime(fn, None)

def abs_pathname (config, fname):
    """If fname is an absolute path then it is returned as is. If it starts
    with a ~ then expand the path as per Unix conventions and finally if it
    appears to be a relative path, the application root is prepended to the
    name and an absolute OS-specific path string is returned."""

    app_root = config.get_app_root()
    if fname[0] == '~':
        return os.path.expanduser(fname)

    if fname[0] != '/' and fname[1] != ':' and fname[2] != '\\':
        return os.path.join(app_root, fname)

    return fname

def chompq (s):
    """Remove any leading and trailing quotes from the passed string."""
    if len(s) < 2:
        return s

    if s[0] == '"' and s[len(s)-1] == '"':
        return s[1:len(s)-1]
    else:
        return s

def unchompq (s):
    if s:
        return '"' + unicode(s) + '"'
    else:
        return '""'

## The follow is a super cool implementation of enum equivalent in
## Python. Taken with a lot of gratitude from this post on Stackoverflow:
## http://stackoverflow.com/a/1695250/987738
##
## It is used like so: Numbers = enum(ONE=1, TWO=2, THREE='three')
## and, Numbers = enum('ZERO', 'ONE', 'TWO') # for auto initialization
def enum(*sequential, **named):
	enums = dict(zip(sequential, range(len(sequential))), **named)
	return type('Enum', (), enums)

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

def del_files_older_than (abs_dir, days):
    """Delete all files in abs_dir/ that were modified more than 'days' days
    or earlier."""

    now = _time.time()

    for f in os.listdir(abs_dir):
        fi = os.path.join(abs_dir, f)
        if os.stat(fi).st_mtime < now - days * 86400:
            if os.path.isfile(fi):
                logging.debug('Deleting File: %s...', f)
                os.remove(fi)

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

def utc_time_to_local_ts (t, ret_dt=False):
    """Convert a Pytime object which is in UTC into a timestamp in local
    timezone.

    If dt is True, then a datetime object is returned, else (this is the
    default), an integer representing time since the epoch is returned."""

    utc_off = localtz.utcoffset(datetime.now())
    try:
        utc_ts  = int(t)
        dt = datetime.fromtimestamp(utc_ts)
    except ValueError, e:
        ## Pytimes earlier than the epoch are a pain in the rear end. 
        dt = datetime(year=t.year,
                      month=t.month,
                      day=t.day,
                      hour=t.hour,
                      minute=t.minute,
                      second=t.second)

    d = dt + utc_off
    if ret_dt:
        return d
    else:
        return _time.mktime(d.timetuple())

def classify_email_addr (addr, domains):
    """Return a tuple of (home, work, other) booleans classifying if the
    specified address falls within one of the domains."""

    res = {'home' : False, 'work' : False, 'other' : False}

    for cat in res.keys():
        try:
            for domain in domains[cat]:
                if re.search((domain + '$'), addr):
                    res[cat] = True
        except KeyError, e:
            logging.warning('Invalid email_domains specification.')

    return (res['home'], res['work'], res['other'])

##
## Some XML parsing and manipulation routines
##

def pretty_xml (x):
    x = xml.dom.minidom.parseString(x).toprettyxml()
    lines = x.splitlines()
    lines = [s for s in lines if not re.match(s.strip(), '^\s*$')]
    return os.linesep.join(lines)

def find_first_child (root, tag, ret='text'):
    """
    Look for the first child of root with specified tag and return it. If
    ret is 'text' then the value of the node is returned, else, the node
    is returned as an element.
    """

    for child in root.iter(tag):
        if ret == 'text':
            return child.text
        else:
            return child

    return None

GNS0_NAMESPACE="http://www.w3.org/2005/Atom"
GNS1_NAMESPACE="http://schemas.google.com/g/2005"
GNS2_NAMESPACE="http://schemas.google.com/contact/2008"
GNS3_NAMESPACE="http://schemas.google.com/gdata/batch"

def unQName (name):
    res = re.match('{.*}(.*)', name)
    return name if res is None else res.group(1)

def QName (namespace, name):
    return '{%s}%s' % (namespace, name)

def QName_GNS0 (name):
    return QName(GNS0_NAMESPACE, name)

def QName_GNS1 (name):
    return QName(GNS1_NAMESPACE, name)

def QName_GNS2 (name):
    return QName(GNS2_NAMESPACE, name)

def QName_GNS3 (name):
    return QName(GNS3_NAMESPACE, name)
