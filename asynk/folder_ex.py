##
## Created : Tue Apr 01 13:31:55 IST 2014
##
## Copyright (C) 2014 Sriram Karra <karra.etc@gmail.com>
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

from   abc            import ABCMeta, abstractmethod
from   folder         import Folder
from   pyews.ews.data import FolderClass

folder_class_map = {
    Folder.CONTACT_t : FolderClass.Contacts,
    Folder.TASK_t    : FolderClass.Tasks,
    Folder.APPT_t    : FolderClass.Calendars,
    Folder.NOTE_t    : FolderClass.Notes
    }

folder_class_inv_map = {}
for key, val in folder_class_map.iteritems():
    folder_class_inv_map.update({val : key})

class EXFolder(Folder):
    """A Folder That directly maps to a folder in MS Exchange"""

    __metaclass__ = ABCMeta

    def __init__ (self, db, entryid, name, fobj):
        Folder.__init__(self, db)

        self.set_entryid(entryid)
        self.set_name(name)
        self.set_fobj(fobj)

    ##
    ## Implementation of some abstract methods inherted from Folder
    ##

    def get_batch_size (self):
        return 100

    def prep_sync_lists (self, destid, sl, synct_sto=None, cnt=0):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def get_itemids (self, pname, destid):
        raise NotImplementedError

    def del_itemids (self, itemids):
        """Delete the specified contacts from this folder if they exist. The
        return value is a pair of (success, [failed entrie]). success is true
        if and only all items were deleted successfully."""

        raise NotImplementedError

    def find_item (self, itemid):
        raise NotImplementedError

    def find_items (self, iids):
        raise NotImplementedError

    def batch_create (self, sync_list, src_dbid, items):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def batch_update (self, sync_list, src_dbid, items):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def writeback_sync_tags (self, pname, items):
        raise NotImplementedError

    def bulk_clear_sync_flags (self, label_re=None):
        """See the documentation in folder.Folder.

        Need to explore if there is a faster way than iterating through
        entries after a table lookup.
        """
        raise NotImplementedError

    def __str__ (self):
        if self.get_type() == Folder.CONTACT_t:
            ret = 'Contacts'
        elif self.get_type() == Folder.NOTE_t:
            ret = 'Notes'
        elif self.get_type() == Folder.TASK_t:
            ret = 'Tasks'
        elif self.get_type() == Folder.APPT_t:
            ret = 'Appointments'
        else:
            ret = 'Other'

        return '%-8s Name: %-15s\tID: %s' % (ret, self.get_name(),
                                             self.get_itemid())

    ##
    ## First some get_ and set_ routines
    ##

    def get_entryid (self):
        return self.get_itemid()

    def set_entryid (self, id):
        return self.set_itemid(id)

    ## fobj is the reference to the pyews.Folder object for this folder.
    def get_fobj (self):
        return self._get_prop('fobj')

    def set_fobj (self, fobj):
        self._set_prop('fobj', fobj)

class EXContactsFolder(EXFolder):
    def __init__ (self, db, fobj):
        EXFolder.__init__(self, db, fobj.Id, fobj.DisplayName, fobj)
        self.set_type(Folder.CONTACT_t)

    def print_key_stats (self):
        print 'Contacts Folder Name: ', self.get_name()
