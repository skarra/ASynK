#!/usr/bin/env python

## Created	 : Tue Jul 19 13:54:53  2011
## Last Modified : Mon Nov 07 16:53:51 IST 2011
##
## Copyright 2011 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

import iso8601
import demjson
import logging, os, time

class Config:

    OUTLOOK = 1
    GOOGLE  = 2

    # There has to be a better way than this...
    sync_strs = [None, 'OUTLOOK', 'GOOGLE', 'TWOWAY']

    def __init__ (self, fn, sync_through=True):
        """If sync_through is True, any change to the configuration is
        immediately written back to the original disk file, otherwise
        the user has to explicitly save to disk."""

        fi = None
        self.fn = os.path.abspath(fn)
        self.sync_through = False

        try:
            fi = open(fn, "r")
        except IOError, e:
            logging.critical('Error! Could not Open file (%s): %s', fn, e)
            return

        st = fi.read()
        self.inp = demjson.decode(st)
        fi.close()

        self.state = self.inp

        self.state['conflict_resolve'] = getattr(
            self, self.inp['conflict_resolve'])

        self.state['sync_dir'] = getattr(
            self, self.inp['sync_dir'])

        self.sync_through = sync_through


    def _get_prop (self, key):
        return self.state[key]

    def _set_prop (self, key, val, sync=True):
        self.state[key] = val
        if self.sync_through and sync:
            self.save()

    def get_gc_guid (self):
        return self._get_prop('GC_GUID')

    def get_gc_id (self):
        return self._get_prop('GC_ID')

    def get_gid (self):
        return self._get_prop('gid')

    def get_cr (self):
        return self._get_prop('conflict_resolve')

    def set_gid (self, val, sync=True):
        return self._set_prop('gid', val, sync)

    def get_gn (self):
        return self._get_prop('gn')

    def get_last_sync_start (self):
        return self._get_prop('last_sync_start')

    def get_curr_time (self):
        return iso8601.tostring(time.time())

    def set_last_sync_start (self, val=None, sync=True):
        if not val:
            val = iso8601.tostring(time.time())
        return self._set_prop('last_sync_start', val, sync)

    def set_gn (self, val, sync=True):
        return self._set_prop('gn', val, sync)

    def get_last_sync_stop (self):
        return self._get_prop('last_sync_stop')

    def set_last_sync_stop (self, val=None, sync=True):
        if not val:
            val = iso8601.tostring(time.time())
        return self._set_prop('last_sync_stop', val, sync)

    def get_resolve (self):
        return self._get_prop('conflict_resolve')

    def set_resolve (self, val, sync=True):
        return self._set_prop('conflict_resolve', val, sync)

    def get_sync_dir (self):
        return self._get_prop('sync_dir')

    def set_sync_dir (self, val, sync=True):
        return self._set_prop('sync_dir', val, sync)

    def save (self, fn=None):
        """fn should be the full absolute path. There is no guarantee
        where it might ge created if you are not careful."""

        if not fn:
            fn = self.fn

        try:
            fi = open(fn, "w")
        except IOError, e:
            logging.critical('Error! Could not Open file (%s): %s', fn, e)
            return

        save = self.get_resolve()
        if save:
            self.set_resolve(self.sync_strs[save], False)

        save = self.get_sync_dir()
        if save:
            self.set_sync_dir(self.sync_strs[save], False)

        fi.write(demjson.encode(self.state))

        if save:
            self.set_resolve(save, False)

        fi.close()
