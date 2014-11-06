##
## Created: Sun Oct 05 21:35:37 IST 2014
##
## Copyright (C) 2014 Sriram Karra <karra.etc@gmail.com>
##
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero General Public License as published by the
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
####
##
## The classes in this file represent different "collection" types. A
## collection in ASynK is a folder of contacts uniquely specified by a tuple
## (DB ID, Store ID, Folder ID)
##

from abc import ABCMeta, abstractmethod
from   pimdb_bb         import BBPIMDB

class Collection:
    def __init__ (self, config=None, dbid=None, stid=None,
                  fid=None, pname=None):
        self.config = config

        self.dbid = dbid
        self.stid = stid
        self.fid  = fid
        self.pname = pname

    @abstractmethod
    def login (self):
        """Returns a PIMDB object of the right type after logging in to the
        appropriate store and authenticating oneself. For e.g. In case of a
        Google Contacts Store, this will login to the right server and
        estabish a connection."""

        pass

    def get_db (self):
        return self.db

    def set_db (self, db):
        self.db = db

    def get_dbid (self):
        return self.dbid

    def set_dbid (self, dbid):
        self.dbid = dbid

    def get_stid (self):
        return self.stid

    def set_stid (self, stid):
        self.stid = stid

    def get_fid (self, cd_fix=False):
        fid = self.fid
        if cd_fix and self.get_dbid() == 'cd' and fid[-1] != '/':
            fid += '/'
        return fid

    def set_fid (self, fid):
        self.fid = fid

    def all_set (self):
        return (self.get_dbid() is not None and
                self.get_stid() is not None and
                self.get_fid()  is not None)

    def __eq__ (self, other):
        return (self.get_dbid() == other.get_dbid() and
                self.get_stid() == other.get_stid() and
                self.get_fid()  == other.get_fid())

    def repr (self):
        return str({'dbid' : self.dbid,
                    'stid' : self.stid,
                    'foid' : self.fid })

class BBCollection(Collection):
    def __init__ (self, config=None, stid=None, fid=None, pname=None):
        Collection.__init__(self, config=config, dbid='bb', stid=stid,
                            fid=fid, pname=pname)

    def login (self):
        if self.get_stid() is not None:
            bbfn = self.get_stid()
        else:
            bbfn = '~/.bbdb'

        if not bbfn:
            raise AsynkError('No BBDB Store provided. Unable to initialize.')

        bb   = BBPIMDB(self.config, bbfn)
        self.set_db(bb)

        return bb

class CDCollection(Collection):
    def __init__ (self, config=None, stid=None, fid=None, pname=None):
        Collection.__init__(self, config=config, dbid='cd', stid=stid, fid=fid,
                            pname=pname)

class EXCollection(Collection):
    def __init__ (self, config=None, stid=None, fid=None, pname=None):
        Collection.__init__(self, config=config, dbid='ex', stid=stid, fid=fid,
                            pname=pname)

class GCCollection(Collection):
    def __init__ (self, config=None, stid=None, fid=None, pname=None):
        Collection.__init__(self, config=config, dbid='gc', stid=stid, fid=fid,
                            pname=pname)

class OLCollection(Collection):
    def __init__ (self, config=None, stid=None, fid=None, pname=None):
        Collection.__init__(self, config=config, dbid='ol', stid=stid, fid=fid,
                            pname=pname)

collection_id_to_class = {
    'bb' : BBCollection,
    'cd' : CDCollection,
    'ex' : EXCollection,
    'gc' : GCCollection,
    'ol' : OLCollection
    }
