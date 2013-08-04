##
## Created : Wed May 18 13:16:17 IST 2011
##
## Copyright (C) 2011, 2012, 2013 Sriram Karra <karra.etc@gmail.com>
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
from   folder_ol     import OLFolder,      OLContactsFolder
from   folder_ol     import OLTasksFolder, OLNotesFolder

MOD_FLAG = mapi.MAPI_BEST_ACCESS

class MessageStores:
    """A container for all the message stores avaialble through the default
    MAPI Login. It is a simple wrapper around a set of MessageStore objects
    that makes available easy retrieval through either name, or the outlook
    entry id.

    NOTE: Outlook is unique in that the same login/authentication allows us to
    access multiple physical MessageStores. This is unlike BBDB and Google. So
    there is no equivalent of this class in the other PIMDB implementations.
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

        self.set_del_items_eid()

        logging.info('Looking for PIM folders in message store: %s...',
                     self.get_name())

        # self.enumerate_all_folders()
        self._populate_folders()
        logging.info('Looking for PIM folders in message store: %s...done',
                     self.get_name())

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

    def set_del_items_eid (self):
        store = self.get_obj()
        hr, ps = store.GetProps((mapitags.PR_IPM_WASTEBASKET_ENTRYID))
        tav, val = ps[0]
        
        self.del_items_eid = val

    def get_del_items_eid (self):
        return self.del_items_eid

    def get_root_folder_obj (self):
        """Return the root folder object of the current messages store."""
        msgstore = self.get_obj()
        return(msgstore.OpenEntry(None, None, MOD_FLAG))

    def get_ipm_subtree_eid (self):
        msgstore = self.get_obj()
        hr, ps   = msgstore.GetProps((mapitags.PR_IPM_SUBTREE_ENTRYID))
        if winerror.FAILED(hr):
            logging.error('Could not get subtree entryid for store: %s. '
                          'Error: 0x%x', self.get_name(),
                          winerror.HRESULT_CODE(hr))
            return None
        tag, eid = ps[0]

        return eid

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
    
    ## Unused for now...
    def enumerate_all_folders (self, folder_eid=None, depth='  '):
        """Walk through the entire folder hierarchy of the message store and
        print one line per folder with some critical information. 

        This is a recursive function. If you want to start enumerating at the
        root folder of the current message store, invoke this routine without
        any arguments. The defaults will ensure the root folder if fetched and
        folders will be recursively enumerated.
        """

        msgstore = self.get_obj()
        folder   = msgstore.OpenEntry(folder_eid, None, MOD_FLAG)
        htable = folder.GetHierarchyTable((mapi.CONVENIENT_DEPTH |
                                           mapi.MAPI_UNICODE))

        htable.SetColumns((mapitags.PR_ENTRYID, mapitags.PR_DISPLAY_NAME,
                           mapitags.PR_FOLDER_TYPE, mapitags.PR_SUBFOLDERS,
                           mapitags.PR_CONTENT_COUNT, mapitags.PR_DEPTH), 0)

        hr  = htable.SeekRow(mapi.BOOKMARK_BEGINNING, 0)
        cnt = 0
        while True:
            rows = htable.QueryRows(1, 0)
            if len(rows) != 1:
                logging.debug('\tbreaking... %d', len(rows))
                break

            ((eidt, eid), (dnt, dn), (ftt, ft), (sft, sf), (cct, cc),
             (dt, d)) = rows[0]
            cnt += 1

            if mapitags.PROP_TYPE(eidt) != mapitags.PT_ERROR:
                logging.debug('%sEID: %s Name: %-25s Type: %2d Has Sub: %5s '
                              'Depth: %2d Count: %d', depth,
                              base64.b64encode(eid), dn, ft, sf, d, cc)
                if sf:
                    self.enumerate_all_folders(folder_eid = eid,
                                              depth=(depth+'  '))
            else:
                logging.error('H, error in enumeraate! :-)')
        
    def enumerate_ipm_folders (self):
        """Walk through all the folders in the IPM subtree of the message
        store and print one line per folder with some critical information.
        For more information on what a IPM Subtree is, look here:
        http://msdn.microsoft.com/en-us/library/cc815825.aspx """

        msgstore = self.get_obj()
        hr, ps   = msgstore.GetProps((mapitags.PR_IPM_SUBTREE_ENTRYID))
        if winerror.FAILED(hr):
            logging.error('Could not get subtree entryid for store: %s. '
                          'Error: 0x%x', self.get_name(),
                          winerror.HRESULT_CODE(hr))
            return
        tag, ipm_eid = ps[0]

        folder   = msgstore.OpenEntry(ipm_eid, None, MOD_FLAG)
        self.enumerate_all_folders(ipm_eid)

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

    def _populate_folders (self, fid=None, depth="  "):
        """Recurse through the entire folder hierarchy of the message store and
        collect the folders that we are interested in and populate the current
        MessageStore's folders object."""

        msgstore = self.get_obj()
        if not fid:
            fid = self.get_ipm_subtree_eid()
            if not fid:
                return

        folder   = msgstore.OpenEntry(fid, None, MOD_FLAG)

        htable = folder.GetHierarchyTable((mapi.CONVENIENT_DEPTH |
                                           mapi.MAPI_UNICODE))

        htable.SetColumns((mapitags.PR_ENTRYID, mapitags.PR_DISPLAY_NAME,
                           mapitags.PR_FOLDER_TYPE, mapitags.PR_SUBFOLDERS,
                           mapitags.PR_CONTENT_COUNT, mapitags.PR_DEPTH), 0)

        hr  = htable.SeekRow(mapi.BOOKMARK_BEGINNING, 0)
        cnt = 0
        while True:
            rows = htable.QueryRows(1, 0)
            if len(rows) != 1:
                break

            ((eidt, eid), (dnt, dn), (ftt, ft), (sft, sf), (cct, cc),
             (dt, d)) = rows[0]
            cnt += 1

            if mapitags.PROP_TYPE(eidt) != mapitags.PT_ERROR:
                logging.debug('%sEID: %s Name: %-25s Type: %2d Has Sub: %5s '
                              'Depth: %2d Count: %d', depth,
                              base64.b64encode(eid), dn, ft, sf, d, cc)

                if ft == mapi.FOLDER_GENERIC:
                    ftype, f = OLFolder.get_folder_type(msgstore, eid)

                    if ftype == Folder.CONTACT_t:
                        ff = OLContactsFolder(self.ol, eid, dn, f, self)
                    elif ftype == Folder.TASK_t:
                        ff = OLTasksFolder(self.ol, eid, dn, f, self)
                    elif ftype == Folder.NOTE_t:
                        ff = OLNotesFolder(self.ol, eid, dn, f, self)
                    elif ftype == Folder.APPT_t:
                        ff = None
                        logging.info('Appointments not supported. Ignoring.')
                    else:
                        ff = None

                    if ff:
                        self.add_to_folders(ff)
                if sf and eid != self.get_del_items_eid():
                    self._populate_folders(fid=eid, depth=(depth+'  '))
            else:
                logging.error('Hm, Error... cnt: %2d', cnt)

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
        self.get_olsession().Logoff(0, 0, 0)

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

    def new_folder (self, fname, ftype, storeid=None):
        """Create a new folder of specified type and return an id. The folder
        will not contain any items. If storeid is None the folder is
        created in the default message store.

        type has to be one of the Folder.valid_types

        """

        if not ftype in Folder.valid_types:
            logging.error('Cannot create folder of type: %s', ftype)
            return None

        if not storeid:
            store = self.get_default_msgstore()
        else:
            store = self.get_msgstore(storeid)

        ipm_eid = store.get_ipm_subtree_eid()
        if not ipm_eid:
            logging.debug('IPM subtree EID not found. Cannot create folder.')
            return None

        try:
            folder = store.get_obj().OpenEntry(ipm_eid, None, MOD_FLAG)
        except Exception, e:
            logging.error('Unable to open store: %s. Error: %s',
                          store.get_name(), str(e))
            return None

        cclass = OLFolder.get_cclass_from_ftype(ftype)
        try:
            nf = folder.CreateFolder(mapi.FOLDER_GENERIC, fname, 'Comment',
                                     None, 0)
            folder.SaveChanges(0)
        except Exception, e:
            logging.error('Failed to create new folder %s. CreateFolder '
                          'returned  error code: %s', fname,
                          str(e))
            return None

        hr, ps = nf.SetProps([(mapitags.PR_CONTAINER_CLASS, cclass)])
        if winerror.FAILED(hr):
            logging.error('Failed to Set Container class for newly created '
                          'folder %s. Hm. tough luck... Delete the sucker '
                          'manually from Outlook. Sorry for the bother. '
                          'Error Code retruned by SetProps: 0x%x',fname,
                          winerror.HRESULT_CODE(hr))
            return None
        
        hr, ps = nf.GetProps((mapitags.PR_ENTRYID))
        if winerror.FAILED(hr):
            logging.error('Failed to get Entry_ID for newly created '
                          'folder %s. Hm. tough luck... Delete the sucker '
                          'manually from Outlook. Sorry for the bother. '
                          'Error Code retruned by SetProps: 0x%x',fname,
                          winerror.HRESULT_CODE(hr))
            return None

        tag, val = ps[0]
        val = base64.b64encode(val)
        logging.info('Successfully created group. ID: %s', val)
        return val

    def show_folder (self, gid):
        logging.info('%s: Not Implemented', 'pimd_ol:show_folder()')

    def get_olsession (self):
        """Return a reference to the Outlook MAPI session."""

        return self._get_att('olsession')

    def set_olsession (self, olsession):
        return self._set_att('olsession', olsession)

    def del_folder (self, itemid, store=None):
        """Get rid of the specified folder."""

        logging.info('Operation del-folder is not implemented for Outlook '
                     'as the underlying MAPI library we use does not implement '
                     'the required MAPI routines. Sorry, dude.')
        # return

        logging.info('Folder %s will only be emptied. It will not be deleted '
                     'completely as I don''t know how to do that.', itemid)

        eid = base64.b64decode(itemid)

        msgstores = self.get_msgstores()
        for msgstore in msgstores.get_stores():
            store = msgstore.get_obj()
            logging.debug('\tStore %s: Trying to open', msgstore.get_name())
            try:
                folder = store.OpenEntry(eid, None, MOD_FLAG)
                logging.debug('\tStore %s: Success!', msgstore.get_name())
            except Exception, e:
                logging.debug('\tStore %s: Not found. Error: %s',
                              msgstore.get_name(), str(e))
                continue

            try:
                folder.EmptyFolder(0, None, 0)
                logging.info('Successfully emptied folder: %s', itemid)
            except Exception, e:
                logging.error('Folder %s could not be emptied. Error: %s %s',
                              itemid, str(e), traceback.format_exc())
            break

        ## FIXME: The following commented out code may be required as and when
        ## pywin32 implements a DeleteFolder() operation. Just keep this
        ## around as comments till an unspecified later time.

        # peid = None
        # msgstores = self.get_msgstores()
        # for msgstore in msgstores.get_stores():
        #     store = msgstore.get_obj()
        #     logging.debug('\tStore %s: Trying to open', msgstore.get_name())
        #     try:
        #         folder = store.OpenEntry(eid, None, MOD_FLAG)
        #         logging.debug('\tStore %s: Success!', msgstore.get_name())
        #         hr, ps = folder.GetProps((mapitags.PR_PARENT_ENTRYID))
        #         tag, peid = ps[0]
        #         break
        #     except Exception, e:
        #         logging.debug('\tStore %s: Not found. Error: %s',
        #                       msgstore.get_name(), str(e))
        # if peid:
        #     try:
        #         folder = store.OpenEntry(peid, None, MOD_FLAG)
        #     except Exception, e:
        #         logging.error("OLPIMDB:del_folder(): could not open parent")
        #         return

        #     hr = folder.EmptyFolder(eid, 0, None)
        #     if winerror.FAILED(hr):
        #         logging.error('DeleteFolder failed with code: 0x%x',
        #                       winerror.HRESULT_CODE(hr))
        #     else:
        #         logging.info('Successfully emptied folder: %s', itemid)
        # else:
        #     logging.debug('Oops, could not trace the sucker. Not emptied')
            

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

    def get_default_msgstore (self):
        stores = self.get_msgstores()
        return stores.get_default_store()
        
    def get_msgstore (self, eid):
        return self.get_msgstore().get(eid=eid)

    def prep_for_sync (self, dbid, pname, dr):
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
