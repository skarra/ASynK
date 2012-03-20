## 
## Created       : Tue Mar 13 14:26:01 IST 2012
## Last Modified : Mon Mar 19 13:38:36 IST 2012
##
## Copyright (C) 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

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

from abc import ABCMeta, abstractmethod

class GoutInvalidPropValueError(Exception):
    pass

class PIMDB:
    __metaclass__ = ABCMeta

    def __init__ (self, config):
        self.config = config

        self.folders      = {'contacts':[],'tasks':[],'notes':[],'appts':[],}
        self.sync_folders = {'contacts':[],'tasks':[],'notes':[],'appts':[],}
        self.def_folder   = {'contacts'  : None, 'tasks'     : None,
                             'notes'     : None, 'appts' : None,}

        ## sync_lists are essentially, data structures used at the itme of
        ## sync, and are used to compile list of items that need to be created
        ## at the destination, and which need to be over written, etc.
        self.sync_lists   = {'contacts':{},'tasks':{},'notes':{},'appts':{},}

        self.dbid = ''

    @abstractmethod
    def get_dbid (self):
        """Should return a two letter identifier to uniquely identify the type
        of PIM Datbase. Examples are 'gc' for Google Contacts, 'ol' for MS
        Outlook, and 'bb' for Emacs BBDB. This id is used, among other things,
        to store the source identification in the remote database, track sync
        status between different databases in the application status, etc."""

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

    ##
    ## Now on to the non-abstract methods
    ##

    def get_config (self):
        return self.config

    def get_contacts_folders (self):
        return self.folders['contacts']

    def get_tasks_folders (self):
        return self.folders['tasks']

    def get_notes_folders (self):
        return self.folders['notes']

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
            ret.append(self.CONTACT_t)

        if self.has_tasks():
            ret.append(self.TASK_t)

        if self.has_notes():
            ret.append(self.NOTE_t)

        if self.has_apptss():
            ret.append(self.APPT_t)

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

    def get_def_folder (self, key):
        return self.def_folder[key]

    def set_def_folder (self, key, value):
        self.def_folder[key] = value

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
