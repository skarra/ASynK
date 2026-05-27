##
## Created : Tue Apr 01 13:31:55 IST 2014
## SPDX-FileCopyrightText: 2014-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
##
## Rewritten for Microsoft Graph API, replacing the legacy pyews EWS client.
##

import logging, re
from   abc        import ABCMeta, abstractmethod
from folder       import Folder
from contact_ex   import EXContact, ASYNK_EXTENSION_NAME
from msgraph_client import GraphAPIError

class EXFolder(Folder, metaclass=ABCMeta):
    """A Folder That directly maps to a contact folder in MS Exchange Online,
    accessed via the Microsoft Graph API."""

    def __init__ (self, db, folder_id, display_name):
        Folder.__init__(self, db)

        self.set_itemid(folder_id)
        self.set_name(display_name)
        self.reset_items()

    ##
    ## Implementation of some abstract methods inherited from Folder
    ##

    def get_batch_size (self):
        return 100

    def prep_sync_lists (self, destid, sl, updated_min=None, cnt=0):
        """See the documentation in folder.Folder.

        Uses Graph API delta queries when available, otherwise falls back
        to full comparison against known item IDs."""

        pname = sl.get_pname()
        conf  = self.get_config()
        oldi  = conf.get_itemids(pname)

        db1id = conf.get_profile_db1(pname)
        if db1id != self.get_dbid():
            oldi = {v:k for k, v in oldi.items()}

        logging.info('Querying Exchange for status of Contact Entries...')
        stag = conf.make_sync_label(pname, destid)

        if not updated_min:
            updated_min = conf.get_last_sync_stop(pname)

        ## Fetch all contacts from the folder (IDs + last modified)
        client = self.get_graph_client()
        graph_contacts = client.list_contacts(
            folder_id=self.get_itemid(),
            select='id,lastModifiedDateTime,displayName')

        graph_ids = set()
        for gc in graph_contacts:
            eid = gc.get('id')
            graph_ids.add(eid)
            lmt = gc.get('lastModifiedDateTime')

            if eid in oldi:
                is_modified = True
                if lmt and updated_min:
                    try:
                        import datetime
                        from dateutil.parser import isoparse
                        lmt_dt = isoparse(lmt)
                        um_dt = isoparse(updated_min)
                        # Allow a 5-second clock skew tolerance
                        if lmt_dt <= um_dt + datetime.timedelta(seconds=5):
                            is_modified = False
                    except Exception as e:
                        logging.warning('Could not parse timestamps: %s', e)
                        if lmt <= updated_min:
                            is_modified = False
                else:
                    is_modified = False

                if is_modified:
                    logging.debug('Modified Exchange Contact: %s %s',
                                  gc.get('displayName', ''), eid[:20])
                    sl.add_mod(eid, oldi[eid])
                else:
                    logging.debug('Unmod   Exchange Contact: %s %s',
                                  gc.get('displayName', ''), eid[:20])
                    sl.add_unmod(eid)
            else:
                logging.debug('New      Exchange Contact: %s %s',
                              gc.get('displayName', ''), eid[:20])
                sl.add_new(eid)

        for oldid in list(oldi.keys()):
            if not oldid in graph_ids:
                logging.debug('Del      Exchange Contact: %s',
                              oldid[:20])
                sl.add_del(oldid, oldi[oldid])

        logging.debug('Total New   : %5d', len(sl.news))
        logging.debug('Total Mod   : %5d', len(sl.mods))
        logging.debug('Total Del   : %5d', len(sl.dels))
        logging.debug('Total Unmod : %5d', len(sl.unmods))

    def get_itemids (self, pname, destid):
        ret = {}
        stag = self.get_config().make_sync_label(pname, destid)
        for locid, con in self.get_items().items():
            if stag in con.get_sync_tags():
                t, remid = con.get_sync_tags(stag)[0]
                ret.update({locid : remid})

        return ret

    def del_itemids (self, itemids):
        """Delete the specified contacts from this folder if they exist. The
        return value is a pair of (success, [failed entries]). success is true
        if and only if all items were deleted successfully."""

        client = self.get_graph_client()
        failed = []

        for iid in itemids:
            try:
                client.delete_contact(iid)
            except GraphAPIError as e:
                logging.error('Failed to delete contact %s: %s', iid, e)
                failed.append(iid)

        return (len(failed) == 0), failed

    def find_item (self, itemid):
        """Fetch specified item from the server."""

        cons = self.find_items([itemid])
        return cons[0] if cons is not None and len(cons) > 0 else None

    def find_items (self, itemids):
        """Fetch multiple items from the server by their IDs."""

        logging.info('folder_ex:find_items() - fetching %d items...',
                     len(itemids))

        client = self.get_graph_client()

        try:
            graph_contacts = client.get_contacts(
                itemids, expand='extensions')
        except GraphAPIError as e:
            logging.info('Error from server looking for items: %s', e)
            return None

        if graph_contacts is not None and len(graph_contacts) > 0:
            fid = self.get_itemid()
            items = [EXContact(self, graph_con=gc) for gc in graph_contacts]
            ret = [x for x in items
                   if x.get_parent_folder_id() == fid or fid is None]
            return ret
        else:
            return None

    def batch_create (self, sync_list, src_dbid, items):
        """See the documentation in folder.Folder.

        Creates new contacts in Exchange via Graph API. For each source
        item:
        1. Wrap it as an EXContact (copies all fields via the con= constructor)
        2. Convert to Graph API JSON dict
        3. Create on the server via the Graph API
        4. Write the Open Extension with sync tags and custom overflow data
        5. Update the source item's sync tags with the new Exchange ID
        """

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = sync_list.get_pname()

        src_sync_tag = c.make_sync_label(pname, src_dbid)
        dst_sync_tag = c.make_sync_label(pname, my_dbid)

        client = self.get_graph_client()
        folder_id = self.get_itemid()

        for item in items:
            con_itemid = item.get_itemid_from_synctags(pname, 'ex')
            exc = EXContact(self, con=item, con_itemid=con_itemid)
            rid = item.get_itemid()
            exc.update_sync_tags(src_sync_tag, rid)

            ## Convert to Graph dict and create on server
            graph_dict = exc.to_graph_dict()
            try:
                resp = client.create_contact(folder_id, graph_dict)
            except GraphAPIError as e:
                logging.error('Failed to create contact %s: %s',
                              exc.get_disp_name(), e)
                continue

            new_id = resp.get('id')
            if new_id:
                exc.set_itemid(new_id)
                self.add_item(exc)

                ## Write extension data (sync tags + custom overflow)
                ext_data = exc.get_extension_data()
                if ext_data:
                    try:
                        client.set_extension(new_id, ASYNK_EXTENSION_NAME,
                                             ext_data)
                    except GraphAPIError as e:
                        logging.warning('Failed to write extension for %s: %s',
                                        new_id, e)

                ## Update source item sync tag with the new Exchange ID
                item.update_sync_tags(dst_sync_tag, new_id)

        ## FIXME: need to get error and fix it
        return True

    def batch_update (self, sync_list, src_dbid, items):
        """See the documentation in folder.Folder.

        Updates existing contacts in Exchange via Graph API."""

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = sync_list.get_pname()

        src_sync_tag = c.make_sync_label(pname, src_dbid)
        dst_sync_tag = c.make_sync_label(pname, my_dbid)

        client = self.get_graph_client()

        for item in items:
            con_itemid = item.get_itemid_from_synctags(pname, 'ex')
            if not con_itemid:
                logging.warning('batch_update: no Exchange ID found for %s',
                                item.get_disp_name())
                continue

            exc = EXContact(self, con=item, con_itemid=con_itemid)
            exc.update_sync_tags(src_sync_tag, item.get_itemid())

            graph_dict = exc.to_graph_dict()
            try:
                client.update_contact(con_itemid, graph_dict)
            except GraphAPIError as e:
                logging.error('Failed to update contact %s: %s',
                              con_itemid, e)
                continue

            ## Update extension data
            ext_data = exc.get_extension_data()
            if ext_data:
                try:
                    client.set_extension(con_itemid, ASYNK_EXTENSION_NAME,
                                         ext_data)
                except GraphAPIError as e:
                    logging.warning('Failed to write extension for %s: %s',
                                    con_itemid, e)

        ## FIXME: Need proper error handling
        return True

    def writeback_sync_tags (self, pname, items):
        """Write sync tags back to the Exchange server for all items.
        Uses Open Extensions to store the sync state."""

        logging.info('Writing sync state to Exchange server...')

        client = self.get_graph_client()
        for item in items:
            contact_id = item.get_itemid()
            if not contact_id:
                continue

            ext_data = item.get_extension_data()
            if ext_data:
                try:
                    client.set_extension(contact_id, ASYNK_EXTENSION_NAME,
                                         ext_data)
                except GraphAPIError as e:
                    logging.warning('Failed to write sync tags for %s: %s',
                                    contact_id, e)

        logging.info('Writing sync state to Exchange server...done')

        ## FIXME: Need proper error handling
        return True

    def bulk_clear_sync_flags (self, label_re=None):
        """Clear all sync flags from contacts in this folder.

        This removes the ASynK Open Extension from every contact in the
        folder, effectively resetting the sync state."""

        logging.info('Clearing sync flags from Exchange folder %s...',
                     self.get_name())

        client = self.get_graph_client()
        contacts = client.list_contacts(
            folder_id=self.get_itemid(),
            select='id',
            expand='extensions')

        cleared = 0
        for gc in contacts:
            contact_id = gc.get('id')
            extensions = gc.get('extensions', [])

            for ext in extensions:
                ext_name = ext.get('extensionName', '')
                ext_id   = ext.get('id', '')

                if (ext_name == ASYNK_EXTENSION_NAME or
                    ext_id.endswith(ASYNK_EXTENSION_NAME)):

                    if label_re is not None:
                        ## Only clear matching sync tags, not entire extension
                        stags = ext.get('syncTags', {})
                        import re as re_mod
                        to_remove = [k for k in stags
                                     if re_mod.search(label_re, k)]
                        if to_remove:
                            for k in to_remove:
                                del stags[k]
                            ext['syncTags'] = stags
                            try:
                                client.set_extension(
                                    contact_id, ASYNK_EXTENSION_NAME, ext)
                            except GraphAPIError as e:
                                logging.warning('Could not update ext for '
                                                '%s: %s', contact_id, e)
                            cleared += 1
                    else:
                        ## Delete the entire extension
                        try:
                            client._request(
                                'DELETE',
                                '/me/contacts/%s/extensions/%s' % (
                                    contact_id, ASYNK_EXTENSION_NAME))
                        except GraphAPIError as e:
                            logging.warning('Could not clear ext for '
                                            '%s: %s', contact_id, e)
                        cleared += 1

        logging.info('Cleared sync flags from %d contacts.', cleared)

    def del_all_entries (self):
        """Delete all contacts in this folder."""

        client = self.get_graph_client()
        contacts = client.list_contacts(
            folder_id=self.get_itemid(), select='id')
        itemids = [c.get('id') for c in contacts]

        if itemids:
            client.delete_contacts(itemids)

    ##
    ## Some internal methods
    ##

    def _refresh_items (self):
        """Fetch all contacts from the server and populate the local cache."""

        self.reset_items()
        client = self.get_graph_client()
        graph_contacts = client.list_contacts(
            folder_id=self.get_itemid(),
            expand='extensions')

        for gc in graph_contacts:
            con = EXContact(folder=self, graph_con=gc)
            self.add_item(con)

    def _refresh_itemids (self):
        """Get a list of all the item IDs in the folder from the server."""

        client = self.get_graph_client()
        graph_contacts = client.list_contacts(
            folder_id=self.get_itemid(), select='id')

        return [gc.get('id') for gc in graph_contacts]

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

    def get_graph_client (self):
        """Get the GraphContactsClient from the parent DB."""
        return self.get_db().get_graph_client()

    ## Legacy alias
    def get_ews (self):
        return self.get_graph_client()

    def reset_items (self):
        self.items = {}

    def get_items (self):
        return self.items

    def add_item (self, item):
        self.items.update({item.get_itemid() : item})


class EXContactsFolder(EXFolder):
    def __init__ (self, db, graph_folder):
        """Initialize from a Graph API folder dict (with 'id' and
        'displayName' keys)."""

        folder_id    = graph_folder.get('id', '')
        display_name = graph_folder.get('displayName', '')

        EXFolder.__init__(self, db, folder_id, display_name)
        self.set_type(Folder.CONTACT_t)

    ##
    ## Inherited methods
    ##

    def print_key_stats (self):
        print('Contacts Folder Name: ', self.get_name())

    ##
    ## Others
    ##

    def reset_contacts (self):
        self.reset_items()

    def get_contacts (self):
        return self.get_items()

    def find_contacts_by_name (self, cnt=0, name=None):
        """Return the list of contact objects in current folder that
        have a matching name. If name is None, all contacts objects
        are returned. If cnt is non-zero value then the first cnt
        matching records are returned."""

        logging.debug('Looking for name %s in folder: %s (%d contacts total)',
                        name, self.get_name(), len(self.get_contacts()))

        i = 0
        ret = []

        for iid, con in self.get_contacts().items():
            if name is None:
                ret.append(con)
            else:
                if (re.search(name, str(con.get_firstname()))
                    or re.search(name, str(con.get_name()))
                    or re.search(name, str(con.get_lastname()))):
                    ret.append(con)
            i += 1

            if cnt == i:
                break

        return ret

    def print_contacts (self, cnt=0, name=None):
        cons = self.find_contacts_by_name(cnt, name)
        for con in cons:
            logging.debug('%s', str(con))

        logging.debug('Printed %d contacts from folder %s', len(cons),
                      self.get_name())
