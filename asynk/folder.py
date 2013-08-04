##
## Created : Tue Mar 13 14:26:01 IST 2012
##
## Copyright (C) 2012, 2013 Sriram Karra <karra.etc@gmail.com>
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
## ####
##
## This file defines an abstract base Contact class essentially as a way of
## documenting what this application considers as a normalized contact
## container.
##

from abc     import ABCMeta, abstractmethod

class ASynKInvalidPropValueError(Exception):
    pass

class Folder:
    __metaclass__ = ABCMeta

    ## We are borrowing the following constants from MAPI to identify our
    ## folder types. I mean, why not...
    CONTACT_t   = PR_IPM_CONTACT_ENTRYID     = 0x36D10102
    NOTE_t      = PR_IPM_NOTE_ENTRYID        = 0x36D30102
    TASK_t      = PR_IPM_TASK_ENTRYID        = 0x36D40102
    APPT_t      = PR_IPM_APPOINTMENT_ENTRYID = 0x36D00102
    UNKNOWN_t   = 0x0

    valid_types = [CONTACT_t, NOTE_t, TASK_t, APPT_t]
    type_names  = { CONTACT_t : 'contacts',
                    NOTE_t    : 'notes',
                    TASK_t    : 'tasks',
                    APPT_t    : 'appts',
                    UNKNOWN_t : 'other',
                    }

    def __init__ (self, db, store=None):
        # Folders have properties that need to persist in the underlying
        # database. We call them 'props'. These are defined and tracked in a
        # single dictionary. Each of the derived classes will, of course, add
        # to this stuff. Please note that there will be a mapping of these
        # property names to a db-specific version that is actually stored.
        self.props = {'itemid'      : None,
                      'type'        : None,
                      'name'        : None,
                      'sync_tags'   : {},
                      'dirty'       : False,
                      }

        # Then there are many class attributes that are needed to work with
        # the programatically in the application, like pointers to the parent
        # Folder and DB object, etc. Such attributes are tracked separately
        # like any other object attributes

        self.set_db(db)
        self.set_store(store)
        self.set_config(db.get_config())

    @abstractmethod
    def __str__ (self):
        raise NotImplementedError

    @abstractmethod
    def get_batch_size (self):
        """When entries are copied during a sync operation, it is frequently
        efficient to do them in batch operations - when the underlying
        database provider supports it. For e.g. it is a huge performance boost
        to use Google Contacts' batch operations. This routine is expected to
        return the size of such a batch operation in general. In practcise
        what this means is that a sync operation will send this many Contact
        entries for processing to the folder / db provider in one go. The
        actual batching and handling, will be done by the underlying code
        anyway."""

        raise NotImplementedError

    @abstractmethod
    def prep_sync_lists (self, destid, sl, last_sync_stop=None, limit=0):
        """Prepare and return a set of list of new, modified and deleted
        entries in the current folder since the last sync to the corresponding
        folder in the destination PIM Database identified by destid.

        The format and stuff returned by this routine will be documented Real
        Soon Now.

        - destid is the two letter PIMDB id
        - sl is an object of type SyncList whose members are populated
        - last_sync_stop was the end of the last sync cycle. It should be a
        iso8601 formatted string - typically read out of the app_state.json
        - limit can be used during debug time to limit the number of messages
        processed/synched. If non-zero, only specified number of
        messages/items will be processed
        """

        raise NotImplementedError

    @abstractmethod
    def get_itemids (self, pname, destid):
        """Return a dictionary of all IDs mapped to specified destid in
        profile pname."""

        raise NotImplementedError

    @abstractmethod
    def find_item (self, itemid):
        """Return an object of some type derived from Item that is specified
        by the given itemid. It is an error for the given itemid to not be
        present."""

        raise NotImplementedError

    @abstractmethod
    def find_items (self, itemids):
        """Return an array of Items whose ids are in the specified array."""

        raise NotImplementedError

    @abstractmethod
    def batch_create (self, src_sl, src_dbid, items):
        """Insert new items into the database. entries is a list of objects
        derived from pimdb.Item. This routine will ensure relevant fields are
        fetched - which will invoke the source db implementation to get the
        properies and use it to create an appropriate Item type object for
        the destination folder and then store it in the folder
        persistently. On successful creation, the other side ID should be
        filled out in the sync tag"""

        raise NotImplementedError

    @abstractmethod
    def batch_update (self, src_sl, src_dbid, items):
        """Update already existing items to new contents. items is a list of
        objects derived from pimdb.Item."""

        raise NotImplementedError

    @abstractmethod
    def writeback_sync_tags (self, pname, items):
        """After a create operation (above), the IDs will need to be written
        on the other side DB. This routine should do that. The operation is
        explicitly separated out because it could be a batch operation by
        itself, for e.g. for Google Contacts"""

        raise NotImplementedError

    @abstractmethod
    def bulk_clear_sync_flags (self, label_re=None):
        """This routine will walk through the folder and delete any local
        storage information that tracks the sync state. For e.g. this includes
        the clearing custom flags / properties for contact entries that
        contain the remote IDs in other databases

        label_re is the regular expression that describes the tag containg the
        remote sync ID. If it is None, the exact behaviour is user defined.
        """

        raise NotImplementedError

    ##
    ## Now the internal helper methods that will be used in the internal
    ## implementetion of the class methods.
    ##

    def _get_prop (self, key):
        return self.props[key]

    def _set_prop (self, key, val):
        self.props[key] = val

    def _append_to_prop (self, key, val):
        """In the particular property value is an array, we would like to
        append individual elements to the property value. this method does
        exactly that."""

        if not self.props[key]:
            self.props[key] = [val]
        else:
            self.props[key].append(val)

    def _update_prop (self, prop, which, val):
        """If a particular property value is a dictionary, we would like to
        update the dictinary with a new mapping or alter an existing
        mapping. This method does exactly that."""

        if not self.props[prop]:
            self.props[prop] = {which : val}
        else:
            self.props[prop].update({which : val})

    ##
    ## Now on to the non-abstract methods
    ##

    def get_itemid (self):
        return self._get_prop('itemid')

    def set_itemid (self, val):
        self._set_prop('itemid', val)

    def get_name (self):
        return self._get_prop('name')

    def set_name (self, name):
        self._set_prop('name', name)

    def get_config (self):
        return self.config

    def set_config (self, config):
        self.config = config

    def get_db (self):
        return self.db

    def set_db (self, db):
        self.db = db

    def get_store (self):
        return self.store

    def set_store (self, store):
        self.store = store

    def get_type (self):
        return self._get_prop('type')

    def set_type (self, t):
        if not t in self.valid_types:
            raise ASynKInvalidPropValueError(
                'Invalid type in Folder:set_type : %s' % t)

        self._set_prop('type', t)

    def get_dbid (self):
        return self.get_db().get_dbid()

    def is_contacts_folder (self):
        return True if self.get_type() == Folder.PR_IPM_CONTACT_ENTRYID else False

    def is_notes_folder (self):
        return True if self.get_type() == Folder.PR_IPM_NOTE_ENTRYID else False

    def is_tasks_folder (self):
        return True if self.get_type() == Folder.PR_IPM_TASK_ENTRYID else False

    def is_appt_folder (self):
        return True if self.get_type() == Folder.PR_IPM_APPOINTMENT_ENTRYID else False

## FIXME: This file needs extensive unit testing. There's quite a bit of
## pseudo-repititive codet hat has been produced by manual cop-n-paste, which
## is a certain recipe for silly typo errors that will not get flagged until
## run time...
