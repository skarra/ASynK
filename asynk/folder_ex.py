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


import logging, re
from   abc            import ABCMeta, abstractmethod
from   folder         import Folder
from   contact_ex     import EXContact
from   pyews.ews      import mapitags
from   pyews.utils    import pretty_eid
from   pyews.ews.data import ews_pt, ews_pid
from   pyews.ews.data import FolderClass
from   pyews.ews.data import MapiPropertyTypeType as mptt
from   pyews.ews.item import ExtendedProperty
from   pyews.ews.errors import EWSMessageError

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
        self.reset_items()

        self.custom_eprops_xml = self._init_custom_eprops_xml()

    ##
    ## Implementation of some abstract methods inherted from Folder
    ##

    def get_batch_size (self):
        return 100

    def prep_sync_lists (self, destid, sl, updated_min=None, cnt=0):
        """See the documentation in folder.Folder"""

        pname = sl.get_pname()
        conf  = self.get_config()
        oldi  = conf.get_itemids(pname)

        db1id = conf.get_profile_db1(pname)
        if db1id != self.get_dbid():
            oldi = {v:k for k, v in oldi.iteritems()}

        logging.info('Querying Exchange for status of Contact Entries...')
        stag = conf.make_sync_label(pname, destid)

        if not updated_min:
            updated_min = conf.get_last_sync_stop(pname)
            ## The updated_min timestamp is of the form
            ## 2014-05-03T09:58:34.20Z; Exchange does not use such a granual
            ## timestamp. So we will strip the .20 from this string
            updated_min = updated_min[0:19] + 'Z'

        ex_items = self.get_ews().FindItems(self.get_fobj(), ids_only=True)
        ex_itemids = [x.itemid.value for x in ex_items]

        for ex_item in ex_items:
            eid = ex_item.itemid.value
            if eid in oldi:
                if ex_item.last_modified_time.value > updated_min:
                    logging.debug('Modified Exchange Contact: %20s %s',
                                  ex_item.display_name.value, pretty_eid(eid))
                    sl.add_mod(eid, oldi[eid])
                else:
                    logging.debug('Unmod   Exchange Contact: %20s %s',
                                  ex_item.display_name.value, pretty_eid(eid))
                    sl.add_unmod(eid)
            else:
                logging.debug('New      Exchange Contact: %20s %s',
                              ex_item.display_name.value, pretty_eid(eid))
                sl.add_new(eid)

        for oldid in oldi.keys():
            if not oldid in ex_itemids:
                logging.debug('Del      Exchange Contact: %s',
                              pretty_eid(oldid))
                sl.add_del(oldid, oldi[oldid])

        logging.debug('Total New   : %5d', len(sl.news))
        logging.debug('Total Mod   : %5d', len(sl.mods))
        logging.debug('Total Del   : %5d', len(sl.dels))
        logging.debug('Total Unmod : %5d', len(sl.unmods))

    def get_itemids (self, pname, destid):
        ret = {}
        stag = self.get_config().make_sync_label(pname, destid)
        for locid, con in self.get_items().iteritems():
            if stag in con.get_sync_tags():
                t, remid = con.get_sync_tags(stag)[0]
                ret.update({locid : remid})

        return ret

    def del_itemids (self, itemids):
        """Delete the specified contacts from this folder if they exist. The
        return value is a pair of (success, [failed entrie]). success is true
        if and only all items were deleted successfully."""

        resp = self.get_ews().DeleteItems(itemids)
        if resp.has_errors():
            return False, [itemids[i] for i in resp.errors.keys()]

        return True, []

    def find_item (self, itemid):
        """
        Fetch specified item from the server. The Exchange service searches
        and returns this from anywhere so items need to be
        """

        cons = self.find_items([itemid])
        return cons[0] if cons is not None else None

    def find_items (self, itemids):
        logging.info('folder_ex:find_items() - fetching items...')
        try:
            ews = self.get_ews()
            ews_items = ews.GetItems(itemids,
                                     eprops_xml=self.custom_eprops_xml)
        except EWSMessageError as e:
            logging.info('Error from Server looking for items: %s', e)
            return None

        fid = self.get_itemid()
        if ews_items is not None and len(ews_items) > 0:
            ## FIXME: Need to fix this when we add suppport for additional
            ## item types. For now we just assume we only get back contact
            ## types - which is true as of April 2014
            items = [EXContact(self, x) for x in ews_items]
            ret =  [x for x in items if x.get_parent_folder_id() == fid]
            return ret
        else:
            return None

    def batch_create (self, sync_list, src_dbid, items):
        """See the documentation in folder.Folder"""

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = sync_list.get_pname()

        src_sync_tag = c.make_sync_label(pname, src_dbid)
        dst_sync_tag = c.make_sync_label(pname, my_dbid)

        ex_cons = []
        for item in items:
            con_itemid = item.get_itemid_from_synctags(pname, 'ex')
            exc = EXContact(self, con=item, con_itemid=con_itemid)
            rid = item.get_itemid()
            exc.update_sync_tags(src_sync_tag, rid)

            self.add_item(exc)

            ews_con = exc.init_ews_con_from_props()
            ex_cons.append(ews_con)

        self.get_ews().CreateItems(self.get_fobj().Id, ex_cons)

        for i, item in enumerate(items):
            exc = ex_cons[i]
            item.update_sync_tags(dst_sync_tag, exc.itemid.value)

        ## FIXME: need to get error and fix it
        return True

    def batch_update (self, sync_list, src_dbid, items):
        """See the documentation in folder.Folder"""

        ## FIXME: We will assume that the change keys are up to date... for
        ## now.

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = src_sl.get_pname()

        src_sync_tag = c.make_sync_label(pname, src_dbid)
        dst_sync_tag = c.make_sync_label(pname, my_dbid)

        ## FIXME: Most of this stuff has to do with sync tags and we should be
        ## doing away with this shit.
        ews_cons = []
        for item in items:
            con = x.init_ews_con_from_props()
            con.update_sync_tags(src_sync_tag, item.get_itemid())

            ews_cons.append(con)

        self.service.UpdateItems(ews_cons)

        ## FIXME: Need proper error handling
        return True

    def writeback_sync_tags (self, pname, items):
        logging.info('Writing sync state to Exchange server...')

        ews_cons = [x.init_ews_con_from_props() for x in items]
        self.get_ews().UpdateItems(ews_cons)

        logging.info('Writing sync state to Exchange server...done')

        ## FIXME: Need proper error handling
        return True

    def bulk_clear_sync_flags (self, label_re=None):
        """See the documentation in folder.Folder."""

        raise NotImplementedError

    def del_all_entries (self):
        itemids = self._refresh_itemids()
        self.get_ews().DeleteItems(itemids)

    ##
    ## Some internal methods
    ##

    def _init_custom_eprops_xml (self):
        xmls = []

        guid = self.get_config().get_ex_guid()
        pid  = self.get_config().get_ex_cus_pid()
        pname = self.get_config().get_ex_stags_pname()

        ## The property containing the ASynK Custom data
        eprop = ExtendedProperty(psetid=guid, pid=pid,
                                 ptype=mptt[mapitags.PT_UNICODE])
        xmls.append(eprop.write_to_xml_get())

        ## The property containing the ASynK sync tags data
        eprop = ExtendedProperty(psetid=guid, pname=pname,
                                 ptype=mptt[mapitags.PT_UNICODE])
        xmls.append(eprop.write_to_xml_get())

        ## This property is not returned by default with older exchange
        ## versions ...
        ptag  = ews_pid(mapitags.PR_PERSONAL_HOME_PAGE)
        ptype = ews_pt(mapitags.PR_PERSONAL_HOME_PAGE)
        eprop = ExtendedProperty(ptag=ptag, ptype=ptype)
        xmls.append(eprop.write_to_xml_get())

        return xmls

    def _refresh_items (self):
        self.reset_items()

        ews = self.get_ews()
        fobj = self.get_fobj()
        ews_cons = ews.FindItems(fobj, eprops_xml=self.custom_eprops_xml)

        for econ in ews_cons:
            ## FIXME: This needs to be fixed if and when we support additional
            ## Item types.
            con = EXContact(folder=self, ews_con=econ)
            self.add_item(con)

    def _refresh_itemids (self):
        """
        Get a list of all the Itemids in the folder from the server
        """

        ews = self.get_ews()
        fobj = self.get_fobj()
        ews_cons = ews.FindItems(fobj, eprops_xml=self.custom_eprops_xml,
                                 ids_only=True)

        return [ews_con.itemid.value for ews_con in ews_cons]

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

    def get_ews (self):
        return self.get_db().get_ews()

    def reset_items (self):
        self.items = {}

    def get_items (self):
        return self.items

    def add_item (self, item):
        self.items.update({item.get_itemid() : item})

class EXContactsFolder(EXFolder):
    def __init__ (self, db, fobj):
        EXFolder.__init__(self, db, fobj.Id, fobj.DisplayName, fobj)
        self.set_type(Folder.CONTACT_t)

    ##
    ## Inherited methods
    ##

    def print_key_stats (self):
        print 'Contacts Folder Name: ', self.get_name()

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

        for iid, con in self.get_contacts().iteritems():
            if name is None:
                ret.append(con)
            else:
                if (re.search(name, unicode(con.get_firstname()))
                    or re.search(name, unicode(con.get_name()))
                    or re.search(name, unicode(con.get_lastname()))):
                    ret.append(con)
            i += 1

            if cnt == i:
                break

        return ret

    def print_contacts (self, cnt=0, name=None):
        cons = self.find_contacts_by_name(cnt, name)
        for con in cons:
            logging.debug('%s', unicode(con))

        logging.debug('Printed %d contacts from folder %s', len(cons),
                      self.get_name())
