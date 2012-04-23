#!/usr/bin/env python
##
## ol_wrapper.py
##
## Created	 : Wed May 18 13:16:17 IST 2011
## Last Modified : Mon Mar 26 14:49:36 IST 2012
##
## Copyright 2011 Sriram Karra <karra.etc@gmail.com>
## All Rights Reserved
##
## Licensed under the GPL v3
## 

import os, os.path, sys, traceback

DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('../Gout')))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib')]

sys.path = EXTRA_PATHS + sys.path

import win32com.client
import pywintypes
from   win32com.mapi import mapi
from   win32com.mapi import mapitags
from   win32com.mapi import mapiutil
import winerror

import iso8601, base64

from   gc_wrapper import get_udp_by_key
from   ol_contact import Contact
import utils

import sys, logging, os, os.path, time
from   datetime import datetime

DEBUG = 0

MOD_FLAG = mapi.MAPI_BEST_ACCESS

# class PropTags:
#     """This Singleton class represents a set of all the possible mapi property
#     tags. In general the mapitags module has pretty usable constants
#     defined. However MAPI compllicates things with 'Named Properties' - which
#     are not static, but have to be generated at runtime (not sure what all
#     parameters change it...). This class includes all the mapitags properties
#     as well as a set of hand selected named properties that are relevant for
#     us here."""

#     PSETID_Address_GUID = '{00062004-0000-0000-C000-000000000046}'
#     PSETID_Task_GUID    = '{00062003-0000-0000-c000-000000000046}'

#     def __init__ (self, def_cf, config):
#         self.name_hash = {}
#         self.valu_hash = {}

#         # We use the def_cf to lookup named properties. I suspect this will
#         # have to be changed when we start supporting multiple profiles and
#         # folders...
#         self.def_cf = def_cf
#         self.config = config

#         # Load up all available properties from mapitags module

#         for name, value in mapitags.__dict__.iteritems():
#             if name[:3] == 'PR_':
#                 # Store both the full ID (including type) and just the ID.
#                 # This is so PR_FOO_A and PR_FOO_W are still
#                 # differentiated. Note that in the following call, the value
#                 # hash will only contain the full ID.
#                 self.put(name=name, value=mapitags.PROP_ID(value))
#                 self.put(name=name, value=value)

#         # Now Add a bunch of named properties that we are specifically
#         # interested in.

#         self.put(name='GOUT_PR_FILE_AS', value=self.get_file_as_prop_tag())

#         self.put(name='GOUT_PR_EMAIL_1', value=self.get_email_prop_tag(1))
#         self.put(name='GOUT_PR_EMAIL_2', value=self.get_email_prop_tag(2))
#         self.put(name='GOUT_PR_EMAIL_3', value=self.get_email_prop_tag(3))

#         self.put(name='GOUT_PR_GCID', value=self.get_gid_prop_tag())

#         self.put('GOUT_PR_TASK_DUE_DATE', self.get_task_due_date_tag())
#         self.put('GOUT_PR_TASK_STATE',    self.get_task_state_tag())
#         self.put('GOUT_PR_TASK_RECUR',    self.get_task_recur_tag())
#         self.put('GOUT_PR_TASK_COMPLETE', self.get_task_complete_tag())
#         self.put('GOUT_PR_TASK_DATE_COMPLETED',
#                  self.get_task_date_completed_tag())

#     def valu (self, name):
#         return self.name_hash[name]

#     def name (self, valu):
#         return self.valu_hash[valu]

#     ## The rest of the methods below are internal to the class.

#     def put (self, name, value):
#         self.name_hash[name]  = value
#         self.valu_hash[value] = name

#     # Routines to construct the property tags for named property. Intended to
#     # be used only once in the constructor

#     def get_email_prop_tag (self, n):
#         """MAPI is crappy.

#         Email addresses of the EX type do not conatain an SMTP address
#         value for their PR_EMAIL_ADDRESS property tag. While the desired
#         smtp address is present in the system the property tag that will
#         help us fetch it is not a constant and will differ from system
#         to system, and from PST file to PST file. The tag has to be
#         dynamically generated.

#         The routine jumps through the requisite hoops and appends those
#         property tags to the supplied fields array. The augmented fields
#         array is then returned.
#         """
#         if n <= 1:
#             try:
#                 return self.valu('GOUT_PR_EMAIL_1')
#             except KeyError, e:
#                 prop_name = [(self.PSETID_Address_GUID, 0x8084)]
#                 prop_type = mapitags.PT_UNICODE
#                 prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)
#                 return (prop_type | prop_ids[0])

#         prev_tag      = self.get_email_prop_tag(n-1)
#         prev_tag_id   = mapitags.PROP_ID(prev_tag)
#         prev_tag_type = mapitags.PROP_TYPE(prev_tag)

#         return mapitags.PROP_TAG(prev_tag_type, prev_tag_id+1)        

#     def get_gcid_prop_tag (self):
#         prop_name = [(self.config.get_gc_guid(),
#                       self.config.get_gc_id())]
#         prop_type = mapitags.PT_UNICODE
#         prop_ids  = self.def_cf.GetIDsFromNames(prop_name, 0)

#         return (prop_type | prop_ids[0])

#     def get_file_as_prop_tag (self):
#         prop_name = [(self.PSETID_Address_GUID, 0x8005)]
#         prop_type = mapitags.PT_UNICODE
#         prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)

#         return (prop_type | prop_ids[0])        

#     def get_task_due_date_tag (self):
#         prop_name = [(self.PSETID_Task_GUID, 0x8105)]
#         prop_type = mapitags.PT_SYSTIME
#         prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)

#         return (prop_type | prop_ids[0])        

#     def get_task_date_completed_tag (self):
#         prop_name = [(self.PSETID_Task_GUID, 0x810f)]
#         prop_type = mapitags.PT_SYSTIME
#         prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)

#         return (prop_type | prop_ids[0])        

#     def get_task_state_tag (self):
#         prop_name = [(self.PSETID_Task_GUID, 0x8113)]
#         prop_type = mapitags.PT_LONG
#         prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)

#         return (prop_type | prop_ids[0])        

#     def get_task_complete_tag (self):
#         prop_name = [(self.PSETID_Task_GUID, 0x811c)]
#         prop_type = mapitags.PT_BOOLEAN
#         prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)

#         return (prop_type | prop_ids[0])        

#     def get_task_recur_tag (self):
#         prop_name = [(self.PSETID_Task_GUID, 0x8126)]
#         prop_type = mapitags.PT_BOOLEAN
#         prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)

#         return (prop_type | prop_ids[0])        

# class MessageStores:
#     """A container for all the message stores avaialble through the default
#     MAPI Login. It is a simple wrapper around a set of MessageStore objects
#     that makes available easy retrieval through either name, or the outlook
#     entry id."""

#     def __init__ (self, ol):
#         self.ol = ol

#         self._store_by_eid  = {}
#         self._store_by_name = {}
#         self._default_store = None

#         self._populate_stores()

#     def get_default_store (self):
#         return self._default_store

#     def get (self, name=None, eid=None):
#         """Fetch the MessageStore object for the specified entry id or the
#         name. The behaviour is undefined if both eid and name are specified in
#         the function call. If both name and eid are omitted in the function
#         call, the MessageStore object for the default message store is
#         returned.
#         """
#         if eid:
#             return self._store_by_eid[eid]
        
#         if name:
#             return self._store_by_name[name]

#         return self.get_default_store()

#     def put (self, eid, name, default, store):
#         self._store_by_eid[eid]   = store
#         self._store_by_name[name] = store
#         if default:
#             self._default_store   = store

#     def _populate_stores (self):
#         """Walk through the message store table in Outlook, extract some key
#         properties of each store and keep track of them for later use."""

#         messagestorestable = self.ol.session.GetMsgStoresTable(0)

#         # This is where we need to add columns if we want to extract and store
#         # more information per Store
#         messagestorestable.SetColumns((mapitags.PR_ENTRYID,
#                                        mapitags.PR_DISPLAY_NAME_A,
#                                        mapitags.PR_DEFAULT_STORE),0)

#         i = 1
#         msgstores = []
#         while True:
#             rows = messagestorestable.QueryRows(1, 0)
#             # if this is the last row then stop
#             if len(rows) != 1:
#                 break
#             row = rows[0]

#             (eid_tag, eid), (name_tag, name), (def_store_tag, def_store) = row
#             if def_store:
#                 # There is a real problem with OpenMsgStore() on non-default
#                 # message stores. We do not know how to process these
#                 # suckers - it just hangs. So for now, we just get ignore
#                 # everything except the first 
#                 logging.debug('Processing Msgstore #%2d: %s', i, name)
#                 store = MessageStore(self.ol, eid, name, def_store)
#                 self.put(eid=eid, name=name, store=store, default=def_store)
#             else:
#                 logging.debug('Msgstore #%2d: %s - skipped non-default one',
#                               i, name)
#             i += 1

#     def __str__ (self):
#         for name, store in self._store_by_name().itermsitems():
#             ret += str(store) + '\n'

#         return ret

# class MessageStore:
#     """A wrapper around an Outlook message store. This is not meant to be an
#     comprehensive wrapper around all the MAPI routines and variables. This is
#     just a convenience class to localize all store related data and the few
#     stor access mapi routines. More routines and properties will be added here
#     as they are needed in the application.

#     The actual outlook store entry is opened lazily - when required."""

#     def __init__ (self, ol, eid, name, default):
#         self.ol      = ol
#         self.eid     = eid
#         self.name    = name
#         self.default = default
#         self.obj     = None

#         self.folders       = None

#         # This should really be done 'lazily' but let's go with the flow for
#         # now... FIXME
#         self._populate_folders()

# #        self.tasks_folders[0].print_key_stats()

#     def get_obj (self):
#         if self.obj:
#             return self.obj

#         # Open it.
#         self.obj = self.ol.session.OpenMsgStore(0, self.eid, None,
#                                                 (mapi.MDB_NO_DIALOG |
#                                                   MOD_FLAG))

#         return self.obj

#     def get_default_contacts_folder (self):
#         # Somewhat of a hack. There might be more than one contacts folder
#         # inside the store... FIXME
#         if self.contacts_folders and len(self.contacts_folders) > 0:
#             return self.contacts_folders[0]

#         return None

#     def get_inbox (self, msgstore):
#         inbox_id, c = msgstore.GetReceiveFolder("IPM.Note", 0)
#         inbox       = msgstore.OpenEntry(inbox_id, None, MOD_FLAG)

#         return inbox

#     def check_tag_error (self, tag):
#         if mapitags.PROP_TYPE(tag) == mapitags.PT_ERROR:
#             raise TypeError('got PT_ERROR: %16x' % tag)
#         elif mapitags.PROP_TYPE(tag) == mapitags.PT_BINARY:
#             pass

#     def get_folder_obj (self, tag, inbox):
#         """Return a tuple (entry_id, display_name, folder_obj) corresponding
#         to specific tag."""
#         hr, props = inbox.GetProps((tag), 0)
#         (tag0, eid)  = props[0]

#         # check for errors
#         self.check_tag_error(tag0)

#         name = self.get_entry_name(eid)
#         f    = self.get_obj().OpenEntry(eid, None, MOD_FLAG)

#         return (eid, name, f)

#     def _populate_folders (self):
#         if self.folders:
#             return self.folders

#         self.folders          = []
#         self.contacts_folders = []
#         self.notes_folders    = []
#         self.tasks_folders    = []

#         msgstore = self.get_obj()
#         inbox    = self.get_inbox(msgstore)

#         logging.debug('Building Folder list for Message Store: %s...',
#                       self.name)

#         try:
#             (eid, name, f) = self.get_folder_obj(Folder.PR_IPM_CONTACT_ENTRYID,
#                                                  inbox)
#             cf = ContactsFolder(eid, name, f, self.ol.config, self)
#             self.folders.append(cf)
#             self.contacts_folders.append(cf)
#         except TypeError, e:
#             logging.debug('Actual exception: %s', e)
#             logging.info('No Contacts Folder for message store: %s',
#                          self.name)

#         try:
#             (eid, name, f) = self.get_folder_obj(Folder.PR_IPM_NOTE_ENTRYID,
#                                                  inbox)
#             nf = NotesFolder(eid, name, f, self.ol.config, self)
#             self.folders.append(nf)
#             self.notes_folders.append(nf)
#         except TypeError, e:
#             logging.debug('Actual exception: %s', e)
#             logging.info('No Notes Folder for message store: %s',
#                          self.name)

#         try:
#             (eid, name, f) = self.get_folder_obj(Folder.PR_IPM_TASK_ENTRYID,
#                                                  inbox)
#             tf = TasksFolder(eid, name, f, self.ol.config, self)
#             self.folders.append(tf)
#             self.tasks_folders.append(tf)
#         except TypeError, e:
#             logging.debug('Actual exception: %s', e)
#             logging.info('No Tasks Folder for message store: %s',
#                          self.name)

#     def bulk_clear_gcid_flag (self):
#         """Clear any gcid tags that are stored in Outlook. This is
#         essentially for use while developin and debugging, when we want
#         to make it appear like contact entries were never synched to
#         google. This rolls back some sync related state on the outlook
#         end.

#         Need to explore if there is a faster way than iterating through
#         entries after a table lookup.
#         """
#         logging.info('Querying MAPI for all data needed to clear flag')

#         ctable = self.get_contents()
#         ctable.SetColumns((self.prop_tags.valu('GOUT_PR_GCID'),
#                              mapitags.PR_ENTRYID),
#                              0)
#         logging.info('Data obtained from MAPI. Clearing one at a time')

#         cnt = 0
#         i   = 0
#         store = self.get_default_msgstore()
#         hr = ctable.SeekRow(mapi.BOOKMARK_BEGINNING, 0)

#         while True:
#             rows = ctable.QueryRows(1, 0)
#             # if this is the last row then stop
#             if len(rows) != 1:
#                 break
    
#             (gid_tag, gid), (entryid_tag, entryid) = rows[0]

#             i += 1
#             if mapitags.PROP_TYPE(gid_tag) != mapitags.PT_ERROR:
#                 entry = store.OpenEntry(entryid, None, MOD_FLAG)
#                 hr, ps = entry.DeleteProps([gid_tag])
#                 entry.SaveChanges(mapi.KEEP_OPEN_READWRITE)

#                 cnt += 1

#         logging.info('Num entries cleared: %d. i = %d', cnt, i)
#         return cnt

#     def get_ol_item (self, entryid):
#         return self.get_obj().OpenEntry(entryid, None, MOD_FLAG)

#     def get_entry_name (self, entryid):
#         item      = self.get_ol_item(entryid)
#         hr, props = item.GetProps([mapitags.PR_DISPLAY_NAME], mapi.MAPI_UNICODE)
#         tag, name = props[0] if props else (None, '')

#         return name

#     def __str__ (self):
#         ret = 'Message Store: %s. Total Folders: %d\n' % (self.name,
#                                                           len(self.folders))
#         for folder in self.folders:
#             ret += '\t' + str(folder) + '\n'

#         return ret

# class Outlook:
#     def __init__ (self, config):
#         self.config = config

#         logging.debug('Initalizing MAPI...')
#         # initialize and log on
#         mapi.MAPIInitialize(None)
#         flags = (mapi.MAPI_EXTENDED | mapi.MAPI_USE_DEFAULT |
#                  MOD_FLAG)

#         logging.debug('Opening default profile in MAPI...')
#         self.session = mapi.MAPILogonEx(0, "", None, flags)

#         self.msgstores = MessageStores(self)

#     def __del__ (self):
#         logging.debug('Destroying mapi session...')
#         self.session.Logoff(0, 0, 0)

#     def get_default_msgstore (self):
#         return self.msgstores.get_default_store()

#     def get_default_contacts_folder (self):
#         defstore = self.get_default_msgstore()
#         return defstore.get_default_contacts_folder()

class Folder:
    PR_IPM_CONTACT_ENTRYID = 0x36D10102
    PR_IPM_NOTE_ENTRYID    = 0x36D30102
    PR_IPM_TASK_ENTRYID    = 0x36D40102

    def __init__ (self, entryid, name, folder_obj, folder_type, config, store):
        self.entryid     = entryid
        self.name        = name
        self.folder_obj  = folder_obj
        self.type        = folder_type
        self.config      = config
        self.store       = store

        self.prop_tags = PropTags(self.folder_obj, self.config)
        self.def_cols  = (self.get_contents().QueryColumns(0) +
                          (self.prop_tags.valu('GOUT_PR_GCID'),))

    # def get_obj (self):
    #     return self.folder_obj

    # def get_contents (self):
    #     return self.folder_obj.GetContentsTable(mapi.MAPI_UNICODE)

    # def del_entries (self, eids):
    #     """eids should be a list of EntryIDs - in binary format, as used by
    #     the MAPI routines."""

    #     num = len(eids)
    #     cf  = self.folder_obj
    #     if num:
    #         logging.debug('Deleting %d entries (after replacement) in Outlook: ',
    #                       num)
    #         hr = cf.DeleteMessages(eids, 0, None, 0)
    #         cf.SaveChanges(mapi.KEEP_OPEN_READWRITE)

    # def reset_sync_lists (self):
    #     self.con_all = {}
    #     self.con_new = []
    #     self.con_mod = {}
        
    # def get_con_new (self):
    #     return self.con_new

    # def get_con_mod (self):
    #     return self.con_mod

    # def del_dict_items (self, d, l, keys=True):
    #     """Delete all the elements in d that match the elements in list
    #     l. If 'keys' is True the match is done on the keys of d, else
    #     match is done on the values of d"""
        
    #     # Don't you love python - all the compactness of Perl less all
    #     # the chaos
    #     if keys:
    #         d = dict([(x,y) for x,y in d.iteritems() if not x in l])
    #     else:
    #         d = dict([(x,y) for x,y in d.iteritems() if not y in l])

    #     return d

    # def del_con_mod_by_keys (self, ary):
    #     """Remove all entries in thr con_mod dictionary whose keys
    #     appear in the 'ary' list."""

    #     self.con_mod = self.del_dict_items(self.con_mod, ary)

    # def prep_ol_contact_lists (self, cnt=0):
    #     """Prepare three lists of the contacts in the local OL.

    #     1. dictionary of all Google IDs => PR_ENTRYIDs
    #     2. List of entries created after the last sync
    #     3. List of entries modified after the last sync
    #     """

    #     logging.info('Querying MAPI for status of Contact Entries')
    #     ctable = self.get_contents()
    #     ctable.SetColumns((self.prop_tags.valu('GOUT_PR_GCID'),
    #                        mapitags.PR_ENTRYID,
    #                        mapitags.PR_LAST_MODIFICATION_TIME),
    #                       0)

    #     i   = 0
    #     old = 0
    #     self.reset_sync_lists()

    #     synct_str = self.config.get_last_sync_start()
    #     synct_sto = self.config.get_last_sync_stop()
    #     synct     = iso8601.parse(synct_sto)
    #     logging.debug('Last Start iso str : %s', synct_str)
    #     logging.debug('Last Stop  iso str : %s', synct_sto)
    #     logging.debug('Current Time       : %s', iso8601.tostring(time.time()))

    #     logging.info('Data obtained from MAPI. Processing...')

    #     while True:
    #         rows = ctable.QueryRows(1, 0)
    #         #if this is the last row then stop
    #         if len(rows) != 1:
    #             break
    
    #         (gid_tag, gid), (entryid_tag, entryid), (tt, modt) = rows[0]
    #         self.con_all[entryid] = gid

    #         if mapitags.PROP_TYPE(gid_tag) == mapitags.PT_ERROR:
    #             # Was not synced for whatever reason.
    #             self.con_new.append(entryid)
    #         else:
    #             if mapitags.PROP_TYPE(tt) == mapitags.PT_ERROR:
    #                 print 'Somethin wrong. no time stamp. i=', i
    #             else: 
    #                 if utils.utc_time_to_local_ts(modt) <= synct:
    #                     old += 1
    #                 else:
    #                     self.con_mod[entryid] = gid

    #         i += 1
    #         if cnt != 0 and i >= cnt:
    #             break

    #     logging.debug('==== OL =====')
    #     logging.debug('num processed : %5d', i)
    #     logging.debug('num total     : %5d', len(self.con_all.items()))
    #     logging.debug('num new       : %5d', len(self.con_new))
    #     logging.debug('num mod       : %5d', len(self.con_mod))
    #     logging.debug('num old unmod : %5d', old)

    def print_prop (self, tag, value):
        prop_type = mapitags.PROP_TYPE(tag)
        prop_id   = mapitags.PROP_ID(tag)
    
        if prop_type & mapitags.MV_FLAG:
            print "Tag: 0x%16x (Multi Value); Value: %s" % (long(tag), value)
        else:
            print "Tag: %s; Value: %s" % (mapiutil.GetPropTagName(tag), value)

    def print_all_props (self, contact):
        for t, v in contact:
            print_prop(t, v)

    def print_entries (self, folder, cnt=-1, fields=None):
        """Print property tag and value for each entry in the contents table
        of the curren folder. The logical name for the property will be
        printed if it can be converted into a string using the mapiutil
        routine. Otherwise a hex representation is printed"""

        ctable = folder.GetContentsTable(mapi.MAPI_UNICODE)
        ctable.SetColumns(self.def_cols, 0)

        i = 0

        while True:
            rows = ctable.QueryRows(1, 0)
            #if this is the last row then stop
            if len(rows) != 1:
                break

            if fields is None:
                self.print_all_props(rows[0])
            else:
                # Just print what is in the fields. To be impl.
                pass

            i += 1

            if i >= cnt and cnt > 0:
                break

        print 'num processed: ', i

        return

    def all_entries (self):
        """Return an array of entries in the current folder along with the
        corresponding google IDs in a format that can be directly written to
        the app_state.json file. The value from this for all folders will be
        written to the file as an array field."""

        ret = {'folder' : self.name,
               'store'  : self.store.name}
        entries = []

        ctable = self.get_contents()
        ctable.SetColumns((self.prop_tags.valu('GOUT_PR_GCID'),
                           mapitags.PR_ENTRYID), 0)

        while True:
            rows = ctable.QueryRows(1, 0)
            #if this is the last row then stop
            if len(rows) != 1:
                break
    
            (gid_tag, gid), (entryid_tag, entryid) = rows[0]

            if mapitags.PROP_TYPE(entryid_tag) == mapitags.PT_ERROR:
                logging.error('all_entries(): Error returned while iterating')
                gid = entryid = None
            else:
                entryid = base64.b64encode(entryid)
                if mapitags.PROP_TYPE(gid_tag) == mapitags.PT_ERROR:
                    # Was not synced for whatever reason.
                    logging.debug(('Folder:all_contents(): Prepped unsynched ' +
                                    'items for b64encoded entryid: %s'),
                                    entryid)
                    gid = None

            entries.append({'eid' : entryid,
                             'gcid' : gid})

        ret.update({'entries' : entries,
                     'entrycnt' : len(entries)})
        return ret

#     def is_contacts_folder (self):
#         return True if self.type == Folder.PR_IPM_CONTACT_ENTRYID else False

#     def is_notes_folder (self):
#         return True if self.type == Folder.PR_IPM_NOTE_ENTRYID else False

#     def is_tasks_folder (self):
#         return True if self.type == Folder.PR_IPM_TASK_ENTRYID else False

#     def __str__ (self):
#         if self.type == Folder.PR_IPM_CONTACT_ENTRYID:
#             ret = 'Contacts'
#         elif self.type == Folder.PR_IPM_NOTE_ENTRYID:
#             ret = 'Notes'
#         elif self.type == Folder.PR_IPM_TASK_ENTRYID:
#             ret = 'Tasks'

#         return ('%s.\tName: %s;\tEID: %s;\tStore: %s' % (
#             ret, self.name, base64.b64encode(self.entryid),
#             self.store.name))

# class ContactsFolder(Folder):
#     def __init__ (self, entryid, name, obj, config, store):
#         Folder.__init__(self, entryid, name, obj,
#                         Folder.PR_IPM_CONTACT_ENTRYID, config,
#                         store)

# class NotesFolder(Folder):
#     def __init__ (self, entryid, name, obj, config, store):
#         Folder.__init__(self, entryid, name, obj,
#                         Folder.PR_IPM_NOTE_ENTRYID, config,
#                         store)

# class TasksFolder(Folder):
#     def __init__ (self, entryid, name, obj, config, store):
#         Folder.__init__(self, entryid, name, obj,
#                         Folder.PR_IPM_TASK_ENTRYID, config,
#                         store)

#     def print_key_stats (self):
#         total       = 0
#         recurring   = 0
#         expired     = 0
#         completed   = 0

#         ctable = self.get_obj().GetContentsTable(mapi.MAPI_UNICODE)
#         ctable.SetColumns(self.def_cols, 0)

#         while True:
#             rows = ctable.QueryRows(1, 0)
#             #if this is the last row then stop
#             if len(rows) != 1:
#                 break

#             total += 1

#             props = dict(rows[0])

#             try:
#                 entryid = props[mapitags.PR_ENTRYID]
#             except AttributeError, e:
#                 entryid = 'Not Available'

#             try:
#                 subject = props[mapitags.PR_SUBJECT_W]
#             except AttributeError, e:
#                 subject = 'Not Available'

#             try:
#                 complete = props[self.prop_tags.valu('GOUT_PR_TASK_COMPLETE')]
#                 if complete:
#                     completed += 1
#             except KeyError, e:
#                 complete = 'Not Available'

#             try:
#                 tag = self.prop_tags.valu('GOUT_PR_TASK_RECUR')
#                 recurr_status = props[tag]
#                 if recurr_status:
#                     recurring += 1
#             except KeyError, e:
#                 recurr_status = 'Not Available'

#             try:
#                 tag = self.prop_tags.valu('GOUT_PR_TASK_STATE')
#                 state = props[tag]
#             except KeyError, e:
#                 state = 'Not Available'

#             try:
#                 tag = self.prop_tags.valu('GOUT_PR_TASK_DUE_DATE')
#                 duedate = utils.pytime_to_yyyy_mm_dd(props[tag])
#             except KeyError, e:
#                 duedate = 'Not Available'


#             if complete:
#                 continue

#             print 'Task #%3d: Heading: %s' % (total, subject)
#             print '\tEntryID   : ', base64.b64encode(entryid)
#             print '\tCompleted : ', complete
#             print '\tRecurring : ', recurr_status
#             print '\tState     : ', state
#             print '\tDue Date  : ', duedate
#             print '\n'

#         print '===== Summary Status for Task Folder: %s ======' % self.name
#         print '\tTotal Tasks count : %4d' % total
#         print '\tRecurring count   : %4d' % recurring
#         print '\tExpired count     : %4d' % expired
#         print '\tCompleted count   : %4d' % completed

# def main (argv=None):
#     from state import Config
#     logging.debug('Getting started... Reading Config File...')
#     config = Config('../app_state.json')
    
#     ol     = Outlook(config)

# if __name__ == "__main__":    
#     logging.getLogger().setLevel(logging.DEBUG)
#     try:
#         main()
#     except Exception, e:
#         print 'Caught Exception... Hm. Need to cleanup.'
#         print 'Full Exception as here:', traceback.format_exc()
