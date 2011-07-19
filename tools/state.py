#!/usr/bin/env python

## Created	 : Tue Jul 19 13:54:53  2011
## Last Modified : Tue Jul 19 13:57:35  2011
##
## Copyright 2011 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

import demjson
import logging

class Config:

    OUTLOOK = 1
    GMAIL   = 2

    def __init__ (self, fn):
        fi = None
        try:
            fi = open(fn, "r")
        except IOError, e:
            logging.critical('Error! Could not Open file (%s): %s', fn, e)
            return

        st = fi.read()
        self.inp = demjson.decode(st)

        self.state = self.inp
        self.state['conflict_resolve'] = getattr(
            self, self.inp['conflict_resolve'])


    def _get_prop (self, key):
        return self.state[key]

    def get_gc_guid (self):
        return self._get_prop('GC_GUID')

    def get_gc_id (self):
        return self._get_prop('GC_ID')

    def get_gid (self):
        return self._get_prop('gid')

    def get_cr (self):
        return self._get_prop('conflict_resolve')

    def get_gn (self):
        return self._get_prop('gn')

    def get_last_sync_start (self):
        return self._get_prop('last_sync_start')

    def get_last_sync_stop (self):
        return self._get_prop('last_sync_stop')
