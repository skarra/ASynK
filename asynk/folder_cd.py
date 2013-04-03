##
## Created       : Wed Apr 03 12:59:03 IST 2013
## Last Modified : Wed Apr 03 17:21:46 IST 2013
##
## Copyright (C) 2013 Sriram Karra <karra.etc@gmail.com>
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

from   folder         import Folder

class CDContactsFolder(Folder):
    def __init__ (self, db, fid, gn, root_path):
        Folder.__init__(self, db)

        self.set_itemid(fid)
        self.set_name(gn)
        self.set_root_path(root_path)
        self.set_type(Folder.CONTACT_t)
        self.reset_contacts()

    ##
    ## Internal and helper functions
    ##        

    def __str__ (self):
        ret = 'Contacts'

        return ('%s.\tName: %s;\tGID: %s;\t' % (ret, self.get_name(),
                                                self.get_itemid()))

    def get_batch_size (self):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def prep_sync_lists (self, destid, sl, last_sync_stop=None, limit=0):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def get_itemids (self, pname, destid):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def find_item (self, itemid):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def find_items (self, itemids):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def batch_create (self, src_sl, src_dbid, items):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def batch_update (self, src_sl, src_dbid, items):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def writeback_sync_tags (self, pname, items):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def bulk_clear_sync_flags (self, label_re=None):
        """See the documentation in folder.Folder"""

        raise NotImplementedError


    ##
    ## Internal and helper functions
    ##        

    def reset_contacts (self):
        self.contacts = {}

    def get_contacts (self):
        return self.contacts    

    def get_root_path (self):
        return self._get_prop('root_path')

    def set_root_path (self, root_path):
        self._set_prop('root_path', root_path)
