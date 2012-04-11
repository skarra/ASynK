##
## Created       : Wed May 18 13:16:17 IST 2011
## Last Modified : Wed Apr 11 19:08:53 IST 2012
##
## Copyright (C) 2011, 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

## This is an implementation of the Outlook PIMDB by extending the PIMDB
## abstract base class

import os, os.path, string, sys, logging, time, traceback
from   datetime      import datetime

import iso8601, base64
import win32com.client, pywintypes, winerror
from   win32com.mapi import mapi, mapitags, mapiutil

import utils
from   pimdb         import PIMDB, GoutInvalidPropValueError
from   folder        import Folder
from   folder_ol     import OLContactsFolder, OLTasksFolder, OLNotesFolder

MOD_FLAG = mapi.MAPI_BEST_ACCESS

class MessageStores:
    """A container for all the message stores avaialble through the default
    MAPI Login. It is a simple wrapper around a set of MessageStore objects
    that makes available easy retrieval through either name, or the outlook
    entry id.

    There is no direct equivalent in any of the other DB
    implementations. Hence this is not really 'exported' outside this file.
    """

    def __init__ (self, ol):
        self.ol = ol

        self._store_by_eid  = {}
        self._store_by_name = {}
        self._default_store = None

        self._populate_stores()

    def get_default_store (self):
        return self._default_store

    def get (self, name=None, eid=None):
        """Fetch the MessageStore object for the specified entry id or the
        name. The behaviour is undefined if both eid and name are specified in
        the function call. If both name and eid are omitted in the function
        call, the MessageStore object for the default message store is
        returned.
        """
        if eid:
            return self._store_by_eid[eid]
        
        if name:
            return self._store_by_name[name]

        return self.get_default_store()

    def get_stores (self):
        """Return an array of all the MessageStore objects."""

        return self._store_by_eid.values()

    ## This get and put stuff needs to be brought in line with the rest of the
    ## code conventions

    def put (self, eid, name, default, store):
        self._store_by_eid[eid]   = store
        self._store_by_name[name] = store
        if default:
            self._default_store   = store

    def _populate_stores (self):
        """Walk through the message store table in Outlook, extract some key
        properties of each store and keep track of them for later use."""

        messagestorestable = self.ol.get_olsession().GetMsgStoresTable(0)

        # This is where we need to add columns if we want to extract and store
        # more information per Store
        messagestorestable.SetColumns((mapitags.PR_ENTRYID,
                                       mapitags.PR_DISPLAY_NAME_A,
                                       mapitags.PR_DEFAULT_STORE),0)

        i = 1
        msgstores = []
        while True:
            rows = messagestorestable.QueryRows(1, 0)
            # if this is the last row then stop
            if len(rows) != 1:
                break
            row = rows[0]

            (eid_tag, eid), (name_tag, name), (def_store_tag, def_store) = row
            if True: #def_store:
                # There is a real problem with OpenMsgStore() on non-default
                # message stores. We do not know how to process these
                # suckers - it just hangs. So for now, we just get ignore
                # everything except the first
                try:
                    logging.debug('Msgstore #%2d: %s - Default. Processing.',
                                  i, name)
                    store = MessageStore(self.ol, eid, name, def_store)
                    self.put(eid=eid, name=name, store=store,
                             default=def_store)
                except Exception, e:
                    logging.debug('Error in opening message store. Skipping.')
                    logging.debug('Full Exception as here: %s',
                                  traceback.format_exc())
            else:
                logging.debug('Msgstore #%2d: %s - skipped non-default one',
                              i, name)
            i += 1

    def __str__ (self):
        for name, store in self._store_by_name().itermsitems():
            ret += str(store) + '\n'

        return ret

class MessageStore:
    """A wrapper around an Outlook message store. This is not meant to be an
    comprehensive wrapper around all the MAPI routines and variables. This is
    just a convenience class to localize all store related data and the few
    stor access mapi routines. More routines and properties will be added here
    as they are needed in the applicatione.

    Note that a Message store is what really contains multiple folders inside
    them, and within Folders we have items of different kinds. As there is no
    direct equivalent of this in other PIM databases, we are not exporting
    this stuff outside of this file.
    """

    def __init__ (self, ol, eid, name, default):
        self.ol      = ol
        self.eid     = eid
        self.set_name(name)
        self.default = default
        self.obj     = None

        self.folders      = {'contacts':[],'tasks':[],'notes':[],'appts':[],}
        self.sync_folders = {'contacts':[],'tasks':[],'notes':[],'appts':[],}
        self.def_folder   = {'contacts'  : None, 'tasks'     : None,
                             'notes'     : None, 'appts' : None,}

        # This should really be done 'lazily' but let's go with the flow for
        # now... FIXME
        self._populate_folders()

#        self.tasks_folders[0].print_key_stats()

    def get_obj (self):
        if self.obj:
            return self.obj

        self.obj = self.ol.get_olsession().OpenMsgStore(0, self.eid, None,
                                                        (mapi.MDB_NO_DIALOG |
                                                         MOD_FLAG))
        return self.obj

    def get_name (self):
        return self.name

    def set_name (self, name):
        self.name = name
        return name

    def get_folders (self, ftype=None):
        """Return all the folders of specified type. ftype should be one of
        the valid folder types. If none is specifiedfor ftype, then the entire
        dictionary is returned as is. If ftype is an invalid type, then this
        routine returns None"""
        
        if ftype and not (ftype in Folder.valid_types):
            return None

        ftypename = Folder.type_names[ftype]
        return self.folders[ftypename] if ftype else self.folders

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

    def get_folders (self, ftype=None):
        """Return all the folders of specified type. ftype should be one of
        the valid folder types. If none is specifiedfor ftype, then the entire
        dictionary is returned as is. If ftype is an invalid type, then this
        routine returns None"""
        
        if ftype and not (ftype in Folder.valid_types):
            return None

        ftypename = Folder.type_names[ftype]
        return self.folders[ftypename] if ftype else self.folders

    def get_def_folder (self, ftype=None):
        """Return the default folder for the  message store. ftype has to be
        oneo f the values from Folder.valid_types. If it is none, the default
        contacts folder is returned"""
        
        if not ftype:
           ftype = Folder.CONTACT_t

        return self.def_folder[Folder.type_names[ftype]]

    def get_def_contacts_folder (self):
        return self.get_def_folder(Folder.CONTACT_t)

    def get_inbox (self, msgstore):
        inbox_id, c = msgstore.GetReceiveFolder("IPM.Note", 0)
        inbox       = msgstore.OpenEntry(inbox_id, None, MOD_FLAG)

        return inbox

    def check_tag_error (self, tag):
        if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
            raise TypeError('got PT_ERROR: %16x' % tag)
        elif mapitags.PROP_TYPE(tag) == mapitags.PT_BINARY:
            pass

    def get_folder_obj (self, tag, inbox):
        """Return a tuple (entry_id, display_name, folder_obj) corresponding
        to specific tag."""
        hr, props = inbox.GetProps((tag), 0)
        (tag0, eid)  = props[0]

        # check for errors
        self.check_tag_error(tag0)

        name = self.get_entry_name(eid)
        f    = self.get_obj().OpenEntry(eid, None, MOD_FLAG)

        return (eid, name, f)

    def _populate_folders (self):
        msgstore = self.get_obj()
        inbox    = self.get_inbox(msgstore)

        logging.debug('Building Folder list for Message Store: %s...',
                      self.name)

        try:
            (eid, name, f) = self.get_folder_obj(Folder.PR_IPM_CONTACT_ENTRYID,
                                                 inbox)
            cf = OLContactsFolder(self.ol, eid, name, f, self)
            self.add_to_folders(cf)
        except TypeError, e:
            logging.debug('No Contacts Folder for store: %s. (Ex: %s)',
                          self.name, e)

        try:
            (eid, name, f) = self.get_folder_obj(Folder.PR_IPM_NOTE_ENTRYID,
                                                 inbox)
            nf = OLNotesFolder(self.ol, eid, name, f, self)
            self.add_to_folders(nf)
        except TypeError, e:
            logging.debug('No Notes Folder for store: %s. (Ex: %s)',
                          self.name, e)

        try:
            (eid, name, f) = self.get_folder_obj(Folder.PR_IPM_TASK_ENTRYID,
                                                 inbox)
            tf = OLTasksFolder(self.ol, eid, name, f, self)
            self.add_to_folders(tf)
        except TypeError, e:
            logging.debug('No Tasks Folder for store: %s. (Ex: %s)',
                         self.name, e)

        ## FIXME: We will have to do the above jig and dance for these
        ## Calendars at some point.
        ## folder types as well.

    def get_ol_item (self, entryid):
        return self.get_obj().OpenEntry(entryid, None, MOD_FLAG)

    def get_entry_name (self, entryid):
        item      = self.get_ol_item(entryid)
        hr, props = item.GetProps([mapitags.PR_DISPLAY_NAME], mapi.MAPI_UNICODE)
        tag, name = props[0] if props else (None, '')

        return name

    def __str__ (self):
        ret = 'Message Store: %s. Total Folders: %d\n' % (self.name,
                                                          len(self.folders))
        for folder in self.folders:
            ret += '\t' + str(folder) + '\n'

        return ret

class OLPIMDB(PIMDB):

    def __init__ (self, config):
        PIMDB.__init__(self, config)
        self.mapi_initialize()
        self.set_msgstores(MessageStores(self))
        self.set_folders()
        self.set_def_folders()
        self.set_sync_folders()

    def __del__ (self):
        logging.debug('Destroying mapi session...')
        self.session.Logoff(0, 0, 0)

    ##
    ## First implementation of the abstract methods of PIMDB.
    ##

    def get_dbid (self):
        """See the documentation in class PIMDB"""

        return 'ol'

    def get_msgstores (self):
        return self.msgstores

    def set_msgstores (self, ms):
        self.msgstores = ms
        return ms

    def list_folders (self):
        i = 1
        for t in Folder.valid_types:
            for f in self.get_folders(t):
                logging.info(' %2d: %s', i, str(f))
                i += 1
                             

    def new_folder (self, fname, type):
        """Create a new folder of specified type and return an id. The folder
        will not contain any items"""

        raise NotImplementedError

    def get_olsession (self):
        """Return a reference to the Outlook MAPI session."""

        return self._get_att('olsession')

    def set_olsession (self, olsession):
        return self._set_att('olsession', olsession)

    def del_folder (self, itemid):
        """Get rid of the specified folder."""

        raise NotImplementedError

    def set_folders (self):
        """See the documentation in class PIMDB"""

        ## This copies all the folders from the underlying message stores into
        ## the current object for easy referencing
        logging.debug('OLPIMDB.set_folders(): Begin')

        for store in self.get_msgstores().get_stores():
            logging.debug('\tProcessing store: %s',
                          store.get_name())
            for ftype in Folder.valid_types:
                for f in store.get_folders(ftype):
                    logging.debug('\t\tAdded Folder %s of type %s',
                                  f.get_name(), Folder.type_names[f.get_type()])
                    self.add_to_folders(f)         

        logging.debug('OLPIMDB.set_folders(): Done.')

    def set_def_folders (self):
        """See the documentation in class PIMDB"""

        self.def_folder['contacts'] = self.folders['contacts'][0]
   
    def set_sync_folders (self):
        """See the documentation in class PIMDB"""

        ## FIXME: This is obviously a hack and will need to be fixed. All the
        ## folders can be synched, and it should really be left to the user...

        self.sync_folders['contacts'].append(self.folders['contacts'][0])

    def prep_for_sync (self, dbid):
        pass

    ##
    ## Now the non-abstract methods and internal methods
    ##

    def mapi_initialize (self):
        logging.info('Initalizing MAPI...')
        mapi.MAPIInitialize(None)
        logging.info('Initalizing MAPI...done')
        flags = (mapi.MAPI_EXTENDED | mapi.MAPI_USE_DEFAULT | MOD_FLAG)

        logging.info('Opening default profile in MAPI...')
        self.set_olsession(mapi.MAPILogonEx(0, "", None, flags))
        logging.info('Opening default profile in MAPI...done')
