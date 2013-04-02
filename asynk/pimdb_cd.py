##
## Created       : Tue Apr 02 13:00:12 IST 2013
## Last Modified : Tue Apr 02 19:29:23 IST 2013
##
## Copyright (C) 2013 by Sriram Karra <karra.etc@gmail.com>
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
## ####
##

from   state        import Config
from   pimdb        import PIMDB
from   caldavclientlibrary.client.account import CalDAVAccount

import logging, re, urlparse

class CDPIMDB(PIMDB):
    """GC object is a wrapper for a Google Contacts stream API."""

    def __init__ (self, config, uri, user, pw):
        """If 'server' dooes not start with a http:// or a https:// it is
        assumed to be equivalent to http:// """

        PIMDB.__init__(self, config)
        self.set_user(user)
        self.set_pw(pw)
        self.parse_uri(uri)
        self.cd_init()
        self.set_folders()

    ##
    ## First implementation of the abstract methods of PIMDB.
    ##

    def get_dbid (self):
        """See the documentation in class PIMDB"""

        return 'cd'

    def new_folder (self, fname, ftype=None, storeid=None):
        """See the documentation in class PIMDB"""

        raise NotImplementedError

    def del_folder (self, itemid, store=None):
        """Get rid of the specified folder."""

        raise NotImplementedError

    def set_folders (self):
        """See the documentation in class PIMDB"""

        pass

    def set_def_folders (self):
        """See the documentation in class PIMDB"""

        raise NotImplementedError
   
    def set_sync_folders (self):
        """See the documentation in class PIMDB"""

        raise NotImplementedError

    def prep_for_sync (self, dbid, pname, dr):
        """See the documentation in class PIMDB"""

        raise NotImplementedError

    ##
    ## Now the non-abstract methods and internal methods
    ##

    ## Note: I learnt of the setter, and @property and @property.setter
    ## decorations well after I started developing ASynK. So for the sake of
    ## consitency across the code base we will use explicit get_ and set_
    ## methods

    def get_server (self):
        return self.server

    def set_server (self, server):
        self.server = server

    def get_path (self):
        return self.path

    def set_path (self, path):
        self.path = path if path else '/'

    def get_user (self):
        return self.user

    def set_user (self, user):
        self.user = user

    def get_pw (self):
        return self.pw

    def set_pw (self, pw):
        self.pw = pw

    def get_session (self):
        return self.session

    def set_session (self, sess):
        self.session = sess

    def get_def_headers (self):
        return self.def_headers

    def set_def_headers (self, d):
        self.def_headers = d

    def get_settings (self):
        return self.settings

    def set_settings (self, s):
        self.settings = s

    ##
    ## Other internal and non-static methods
    ##

    def parse_uri (self, uri):
        if not uri.startswith('^http'):
            uri = 'http://' + uri
        splits = urlparse.urlsplit(uri)
        self.set_server(splits.scheme + "://" + splits.netloc)
        self.set_path(splits.path)

    def cd_init (self):
        sf  = self.get_server()
        ssl = sf.startswith('https://')
        server = sf[8:] if ssl else sf[7:]
        accnt  = CalDAVAccount(server, ssl=ssl, user=self.get_user(),
                              pswd=self.get_pw(), root=self.get_path(),
                              principal=None, logging=False)
