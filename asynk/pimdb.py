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
## This file defines an abstract base PIM Database class essentially as a way
## of documenting what this application considers as a normalized PIM
## container.
##
## FIXME: The description below is muddled and needs to be fixed.
## 
## The generic PIM Database is flexibly modeled to deal with the PIM stores we
## are interseted in. Of the lot, Outlook is the most generic. The
## Outlook/MAPI model is, very roughly speaking, is as follows: A outlook
## profile can have multiple message stores. Each message store has multiple
## folders. Each folder can contain messages of one of four important types:
## Contacts, Tasks, Notes, Appointment entries. Each message is just a bag of
## (type, value) property couples. Certain property types are mandatory for
## certain message types.
##
## Now, the PIMDB model below excludes direct support for MessageStores as
## such concepts do not directly exist in other systems. In the general case,
## there is a DB that eventually contain folders of one of four types. The End.
##

import logging
from   abc      import ABCMeta, abstractmethod
from   folder   import Folder

class GoutInvalidPropValueError(Exception):
    pass

class PIMDB:
    __metaclass__ = ABCMeta

    def __init__ (self, config):
        self.atts = {}

        self.set_config(config)

        self.folders      = {'contacts':[],'tasks':[],'notes':[],'appts':[],}
        self.sync_folders = {'contacts':[],'tasks':[],'notes':[],'appts':[],}
        self.def_folder   = {'contacts'  : None, 'tasks' : None,
                             'notes'     : None, 'appts' : None,}

        ## sync_lists are essentially, data structures used at the itme of
        ## sync, and are used to compile list of items that need to be created
        ## at the destination, and which need to be over written, etc.
        self.sync_lists   = {'contacts':{},'tasks':{},'notes':{},'appts':{},}

        self.set_db_config()
        self.set_email_domains()
        self.set_postal_map()
        self.set_notes_map()
        self.set_phones_map()

    @abstractmethod
    def get_dbid (self):
        """Should return a two letter identifier to uniquely identify the type
        of PIM Datbase. Examples are 'gc' for Google Contacts, 'ol' for MS
        Outlook, and 'bb' for Emacs BBDB. This id is used, among other things,
        to store the source identification in the remote database, track sync
        status between different databases in the application status, etc."""

        raise NotImplementedError

    @abstractmethod
    def new_folder (self, fname, type, storeid=None):
        """Create a new folder of specified type and return an id. The folder
        will not contain any items"""

        raise NotImplementedError

    @abstractmethod
    def del_folder (self, itemid, store=None):
        """Get rid of the specified folder."""

        raise NotImplementedError

    @abstractmethod
    def set_folders (self):
        """Each implementation should initialize the folders set in the DB
        fields when this routine is called."""

        raise NotImplementedError

    @abstractmethod
    def set_def_folders (self):
        """Each implementation should set the default folders for all support
        folder/message types in its stores"""

        raise NotImplementedError
   
    @abstractmethod
    def set_sync_folders (self):
        """Each implementation should set the folders it wants to be made
        available for synching. 

        TODO: In future we should provide support for setting synch folders
        specific to a destination pimdb, and for the user to be able to set it
        through the config file."""

        raise NotImplementedError

    @abstractmethod
    def prep_for_sync (self, dbid, pname, dr):
        """This routine will be invoked at the time sync is initialized. dbid
        is the id of the other PIMDB to which sync is being set up. Please
        note that the sync direction could be anything. (Perhaps eventually we
        will pass that or something, but it can be read from the config file
        anyway..."""

        raise NotImplementedError

    ##
    ## Now on to the non-abstract methods
    ##

    def _get_att (self, key):
        return self.atts[key]

    def _set_att (self, key, val):
        self.atts[key] = val
        return val

    def get_config (self):
        return self._get_att('config')

    def set_config (self, config):
        return self._set_att('config', config)

    def get_db_config (self):
        return self._get_att('db_config')

    def set_db_config (self):
        dbc = self.get_config().get_db_config(self.get_dbid())
        return self._set_att('db_config', dbc)

    def get_email_domains (self):
        return self._get_att('email_domains')

    def set_email_domains (self):
        dbc = self.get_db_config()
        if dbc:
            try:
                ed = dbc['email_domains']
                return self._set_att('email_domains', ed)
            except KeyError, e:
                logging.debug('PIMDB %s does not have email_domains.',
                              self.get_dbid())

        return self._set_att('email_domains', None)

    def get_postal_map (self):
        return self._get_att('postal_map')

    def set_postal_map (self):
        dbc = self.get_db_config()
        if dbc:
            try:
                ed = dbc['postal_map']
                return self._set_att('postal_map', ed)
            except KeyError, e:
                logging.debug('PIMDB %s does not have postal_map',
                              self.get_dbid())

        return self._set_att('postal_map', None)

    def get_notes_map (self):
        return self._get_att('notes_map')

    def set_notes_map (self):
        dbc = self.get_db_config()
        if dbc:
            try:
                ed = dbc['notes_map']
                return self._set_att('notes_map', ed)
            except KeyError, e:
                logging.debug('PIMDB %s does not have notes_map',
                              self.get_dbid())

        return self._set_att('notes_map', None)

    def get_phones_map (self):
        return self._get_att('phones_map')

    def set_phones_map (self):
        dbc = self.get_db_config()
        if dbc:
            try:
                ed = dbc['phones_map']
                return self._set_att('phones_map', ed)
            except KeyError, e:
                logging.debug('PIMDB %s does not have phones_map',
                              self.get_dbid())

        return self._set_att('phones_map', None)

    def list_folders (self, silent=False):
        """Print details of all folders in the PIMDB. Detail will typically
        include one line per folder, with its name, and any identifier that
        can be used for further referencing."""

        i = 1
        for t in Folder.valid_types:
            for f in self.get_folders(t):
                logging.info(' %2d: %s', i, str(f))
                i += 1

    def get_folders (self, ftype=None):
        """Return all the folders of specified type. ftype should be one of
        the valid folder types. If none is specifiedfor ftype, then the entire
        dictionary is returned as is. If ftype is an invalid type, then this
        routine returns None"""
        
        if ftype and not (ftype in Folder.valid_types):
            return None

        ftypename = Folder.type_names[ftype]
        return self.folders[ftypename] if ftype else self.folders

    def remove_folder_from_lists (self, f, ft):
        if not ft in Folder.valid_types:
            return None

        ftkey = Folder.type_names[ft]
        try:
            self.folders[ftkey].remove(f)
        except ValueError, e:
            logging.debug('Attemped to remove unlisted folder %s of type %s',
                          f.get_name(), f.get_type())

    def set_folders_of_type (self, ftypestr, val):
        self.folders[ftypestr] = val

    def add_to_folders (self, fold):
        ftype = fold.get_type()
        f     = self.get_folders(ftype)

        if not f:
            f = []
            self.set_folders_of_type(Folder.type_names[ftype], f)
        f.append(fold)

        return fold

    def remove_folder (self, fold):
        """Remove a folder from the folder list by name."""

        ftype = fold.get_type()
        f = self.get_folders(ftype)
        f.remove(fold)

    def add_contacts_folder (self, f):
        """Append specified folder f to the list of Contacts folder in the
        PIMDB."""

        self.folders['contacts'].append(f)

    def get_contacts_folders (self):
        """Returns an array of all the Contacts folders in the current PIMDB"""

        return self.folders['contacts']

    def add_tasks_folder (self, f):
        """Append specified folder f to the list of Tasks folders in the
        PIMDB."""

        self.folders['tasks'].append(f)

    def get_tasks_folders (self):
        """Return the list of Tasks folders available in the current PIMDB."""

        return self.folders['tasks']

    def add_notes_folder (self, f):
        self.folders['notes'].append(f)

    def get_notes_folders (self):
        return self.folders['notes']

    def add_appts_folder (self, f):
        self.folders['appts'].append(f)

    def get_appts_folders (self):
        return self.folders['appts']

    def has_contacts (self):
        """Return True if the PIM database has support for contacts. False
        otherwise."""

        cf = self.get_contacts_folders()
        return True if cf and len(cf) > 0 else False

    def has_tasks (self):
        """Return True if the PIM database has support for Tasks. False
        otherwise. For e.g. Outlook implementation will return True, whereas
        BBDB will return False"""

        tf = self.get_tasks_folders()
        return True if tf and len(tf) > 0 else False

    def has_notes (self):
        """Return True if the PIM database has support for Notes. False
        otherwise. For e.g. Outlook implementation will return True, whereas
        BBDB will return False"""

        nf = self.get_notes_folders()
        return True if nf and len(nf) > 0 else False

    def has_appts (self):
        """Return True if the PIM database has support for Appointments. False
        otherwise. For e.g. Outlook implementation will return True, whereas
        BBDB will return False"""

        af = self.get_appts_folders()
        return True if af and len(af) > 0 else False

    def supported_folder_types (self):
        """Return an array of Folder types that are supported by this
        database backend / api."""

        ret = []
        if self.has_contacts():
            ret.append(Folder.CONTACT_t)

        if self.has_tasks():
            ret.append(Folder.TASK_t)

        if self.has_notes():
            ret.append(Folder.NOTE_t)

        if self.has_appts():
            ret.append(Folder.APPT_t)

        return ret

    def def_contacts_folder (self):
        """Returns the default Contacts folder object"""
        return self.def_folder['contacts']

    def def_tasks_folder (self):
        """Returns the default Tasks folder object."""
        return self.def_folder['tasks']

    def def_notes_folder (self):
        """Returns the default Notes folder object."""
        return self.def_folder['notes']

    def def_appts_folder (self):
        """Returns the default Appts folder object."""
        return self.def_folder['appts']

    def get_def_folder (self, ftype=Folder.CONTACT_t):
        """Return the default folder for the  message store. ftype has to be
        oneo f the values from Folder.valid_types. If it is none, the default
        contacts folder is returned"""
        
        return self.def_folder[Folder.type_names[ftype]]

    def set_def_folder (self, key, value):
        self.def_folder[Folder.type_names[key]] = value

    def find_folder (self, itemid):
        """Locate the folder from the folder list. Returns a tuple of (Folder
        object, Folder_type) if folder if found. Folder_type is one of the
        values from Folder.valid_types Returns (None, None) if there
        is no match found."""

        for ftype in Folder.valid_types:
            for f in self.get_folders(ftype):
                if f.get_itemid() == itemid:
                    return (f, ftype)

        return (None, None)

## Fri Mar 16 18:05:33 IST 2012

## Not sure what the sync code wil be and how the following code will be
## useful, if at all. Keep it commented out for now.
    
    # def reset_sync_lists (self, destid, ftypes=['contacts']):
    #     """This routine wil be called to reset any pre-existing state
    #     infomration before computing the fresh changesets for a given folder
    #     type between a specified pair of PIM BDs."""

    #     for ft in ftypes:
    #         self.sync_lists[ft].update({destid:{'new':[], 'mod':{}, 'del':{},}})

    # def prep_sync_lists (self, dest, ftypes=['contacts']):
    #     """This is intended to prepare a list of new and modified entries in
    #     the PIM Database since the last sync to the dest pimdb. By default we
    #     will assume only contacts are being synched"""
        
    #     last_sync_time = self.config.get_last_sync_stop(self.get_dbid(),
    #                                                     dest.get_dbid())

    #     for ftype in ftypes:
    #         for folder in self.sync_folders[ftype]:
    #             lists = folder.prep_sync_lists(destid, last_sync_time)
    #             self.sync_lists[ft].update({destid : lists})

## FIXME: This file needs extensive unit testing. There's quite a bit of
## pseudo-repititive codet hat has been produced by manual cop-n-paste, which
## is a certain recipe for silly typo errors that will not get flagged until
## run time...
##
## We might just get this 'unit tested' along with the implementation of the
## Outlook PIMDB.
