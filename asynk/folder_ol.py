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

import logging, os, re, sys, time, traceback
import iso8601, base64
import utils

from   abc            import ABCMeta, abstractmethod
from   folder         import Folder
from   win32com.mapi  import mapi, mapiutil
from   win32com.mapi  import mapitags as mt
from   contact_ol     import OLContact
import winerror
import asynk_mapitags as amt

class OLFolder(Folder):
    """An Outlook folder directly corresponds to a MAPI Folder entity. This
    class wraps a mapi folder object while implementing the normalized Folder
    methods and accessors defined by Gout.

    This itself is an abstract class, and only its derived classes can be
    instantiated.
    """

    __metaclass__ = ABCMeta

    cclass_ftype_d = {'IPF.Contact'     : Folder.CONTACT_t,
                      'IPF.Task'        : Folder.TASK_t,
                      'IPF.StickyNote'  : Folder.NOTE_t,
                      'IPF.Appointment' : Folder.APPT_t,
                      'IPF.Note'        : Folder.UNKNOWN_t,
                      }
    ftype_cclass_d = {}
    for key, val in cclass_ftype_d.iteritems():
        ftype_cclass_d.update({val : key})

    def __init__ (self, db, entryid, name, fobj, msgstore):
        Folder.__init__(self, db)

        self.set_entryid(entryid)
        self.set_name(name)
        self.set_fobj(fobj)
        self.set_msgstore(msgstore)

        self.set_proptags(PropTags(self, self.get_config()))
        self.reset_def_cols()

    ##
    ## Implementation of some abstract methods inherted from Folder
    ##

    def get_batch_size (self):
        return 100

    def prep_sync_lists (self, destid, sl, synct_sto=None, cnt=0):
        """See the documentation in folder.Folder"""

        pname = sl.get_pname()
        conf  = self.get_config()
        pdb1id = conf.get_profile_db1(pname)
        oldi  = conf.get_itemids(pname)
        stag  = conf.make_sync_label(pname, destid)

        logging.info('Querying MAPI for status of Contact Entries')

        ## Sort the DBIds so dest1 has the 'lower' ID
        dest1 = self.get_db().get_dbid()
        if dest1 > destid:
            dest2 = dest1
            dest1 = destid
        else:
            dest2 = destid

        ctable = self.get_contents()
        stp = self.get_proptags().sync_tags[stag]

        cols = (mt.PR_ENTRYID, mt.PR_LAST_MODIFICATION_TIME,
                mt.PR_DISPLAY_NAME, stp)
        ctable.SetColumns(cols, 0)

        i   = 0

        synct_str = self.get_config().get_last_sync_start(pname)
        if not synct_sto:
            synct_sto = self.get_config().get_last_sync_stop(pname)
        synct     = iso8601.parse(synct_sto)
        logging.debug('Last Start iso str : %s', synct_str)
        logging.debug('Last Stop  iso str : %s', synct_sto)
        logging.debug('Current Time       : %s', iso8601.tostring(time.time()))

        logging.info('Data obtained from MAPI. Processing...')

        newi = {}
        while True:
            rows = ctable.QueryRows(1, 0)
            #if this is the last row then stop
            if len(rows) != 1:
                break

            ((entryid_tag, entryid), (tt, modt),
             (name_tag, name), (gid_tag, gid)) = rows[0]
            b64_entryid = base64.b64encode(entryid)

            newi.update({b64_entryid : gid})

            if mt.PROP_TYPE(gid_tag) == mt.PT_ERROR:
                # Was not synced for whatever reason.
                logging.debug('New      Outlook Contact: %20s %s', 
                              name, b64_entryid)
                sl.add_new(b64_entryid)
            else:
                if mt.PROP_TYPE(tt) == mt.PT_ERROR:
                    logging.debug('Impossible! Entry has no timestamp. i = %d', i)
                else:
                    if utils.utc_time_to_local_ts(modt) <= synct:
                        sl.add_unmod(b64_entryid)
                    else:
                        logging.debug('Modified Outlook Contact: %20s %s', 
                                      name, b64_entryid)
                        sl.add_mod(b64_entryid, gid)

            i += 1
            if cnt != 0 and i >= cnt:
                break

        ctable.SetColumns(self.get_def_cols(), 0)

        kss = newi.keys()
        for x, y in oldi.iteritems():
            if not x in kss and not y in kss:
                logging.debug('Deleted Outlook Contact: %s:%s', x, y)
                if pdb1id == self.get_dbid():
                    sl.add_del(x, y)
                else:
                    sl.add_del(y,x)

    def get_itemids (self, pname, destid):
        conf  = self.get_config()
        stag  = conf.make_sync_label(pname, destid)
        stp   = self.get_proptags().sync_tags[stag]

        ctable = self.get_contents()
        cols = (mt.PR_ENTRYID, mt.PR_DISPLAY_NAME, stp)
        ctable.SetColumns(cols, 0)

        ret = []
        while True:
            rows = ctable.QueryRows(1, 0)
            if len(rows) != 1:
                break

            ((entryid_tag, entryid), (name_tag, name),
             (remtag, remid)) = rows[0]

            ret.update({base64.b64encode(entryid) : remid})

        ctable.SetColumns(self.get_def_cols(), 0)

        return ret

    def del_itemids (self, itemids):
        """Delete the specified contacts from this folder if they exist. The
        return value is a pair of (success, [failed entrie]). success is true
        if and only all items were deleted successfully."""

        fobj = self.get_fobj()

        retv = True
        retf = []
        for iid in itemids:
            logging.info('Deleting ID: %s...', iid)
            eid = base64.b64decode(iid)
            hr = fobj.DeleteMessages([eid], 0, None, 0)
            if winerror.FAILED(hr):
                retv = False
                retf.append(base64.b64encode(eid))

        return retv, retf

    def find_item (self, itemid):
        eid = base64.b64decode(itemid)
        olc = OLContact(self, eid=eid)
        return olc

    def find_items (self, iids):
        return [OLContact(self, eid=base64.b64decode(iid)) for iid in iids]

    def batch_create (self, sync_list, src_dbid, items):
        """See the documentation in folder.Folder"""

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = sync_list.get_pname()

        src_sync_tag = c.make_sync_label(pname, src_dbid)
        dst_sync_tag = c.make_sync_label(pname, my_dbid)

        success = True
        for item in items:
            con_itemid = item.get_itemid_from_synctags(pname, 'ol')
            olc = OLContact(self, con=item, con_itemid=con_itemid)
            rid = item.get_itemid()
            olc.update_sync_tags(src_sync_tag, rid)

            ## FIXME: I strongly suspect this is not the most efficient way to
            ## do this. We should test by importing items in bulk into
            ## Outlook and measure performance, and fix this if needed.

            try:
                eid = olc.save()
                logging.info('Successfully created outlook entry for %30s (%s)',
                             olc.get_disp_name(), olc.get_itemid())
            except Exception, e:
                logging.error('Could not save contact (%s) due to: %s',
                              olc.get_disp_name(), str(e))
                logging.debug('Contact Entry: %s', olc)
                logging.debug(traceback.format_exc())
                success = False
                continue

            iid = olc.get_itemid()
            item.update_sync_tags(dst_sync_tag, iid)

        return success

    def batch_update (self, sync_list, src_dbid, items):
        """See the documentation in folder.Folder"""

        pname   = sync_list.get_pname()
        src_tag = self.get_config().make_sync_label(pname, src_dbid)

        store = self.get_msgstore().get_obj()
        success = True
        for item in items:
            con_itemid = item.get_itemid_from_synctags(pname, 'ol')
            olc = OLContact(self, con=item, con_itemid=con_itemid)

            ## We lose the sync tag as well when we blow everything. To ensure
            ## this gets recreated, put it back in.

            olc.update_sync_tags(src_tag, item.get_itemid())
            olprops = olc.get_olprops()
            oli     = olc.get_olitem()

            ## Wipe out the sucker
            try:
                def_cols = oli.GetPropList(mapi.MAPI_UNICODE)
                hr, ps = oli.DeleteProps(def_cols)
            except Exception, e:
                logging.error('%s: Could not clear our MAPI props for: %s (%s)',
                              'ol:batch_update()', item.get_name(), e)
                logging.debug(traceback.format_exc())
                success = False
                continue

            ## Now shove the new property set in
            try:
                hr, ps = oli.SetProps(olprops)
                oli.SaveChanges(mapi.KEEP_OPEN_READWRITE)
                logging.info('Successfully updated changes to Outlook for %s',
                             item.get_disp_name())
            except Exception, e:
                logging.error('%s: Could not set new props set for: %s (%s)',
                              'ol:batch_update()', item.get_disp_name(), e)
                success = False
                continue

        return success

    def writeback_sync_tags (self, pname, items):
        success = True
        for item in items:
            success = success and item.save_sync_tags()

        return success

    def bulk_clear_sync_flags (self, label_re=None):
        """See the documentation in folder.Folder.

        Need to explore if there is a faster way than iterating through
        entries after a table lookup.
        """
        if not label_re:
            label_re = 'asynk:[a-z][a-z]:id'

        tags = []
        for name, tag in self.get_proptags().sync_tags.iteritems():
            if re.search(label_re, name):
                tags.append(tag)

        return self._clear_tag(tags)

    def __str__ (self):
        if self.get_type() == Folder.PR_IPM_CONTACT_ENTRYID:
            ret = 'Contacts'
        elif self.get_type() == Folder.PR_IPM_NOTE_ENTRYID:
            ret = 'Notes'
        elif self.get_type() == Folder.PR_IPM_TASK_ENTRYID:
            ret = 'Tasks'

        return ('%-8s Name: %-15s\tEID: %s  Store: %s' % (
            ret, self.get_name(), base64.b64encode(self.get_entryid()),
            self.get_msgstore().get_name()))

    ##
    ## First some get_ and set_ routines
    ##

    ## Note: For Outlook related methods, itemid and entryid are aliases.

    def get_entryid (self):
        return self._get_prop('entryid')

    def set_entryid (self, entryid):
        self._set_prop('entryid', entryid)
        self.set_itemid(base64.b64encode(entryid))
        return entryid

    def get_proptags (self):
        return self.proptags

    def set_proptags (self, p):
        self.proptags = p

    def reset_def_cols (self):
        """All property read operations on the Outlook Item database, are
        given a set of columns, or properties, to fetch. A def_cols list is
        maintained for general iteration. Apart from the regular list of
        columns that are returned, we would like to also fetch the user
        defined property tags so they will be processed like any other
        property. """

        sync_tag_props = self.get_proptags().sync_tags.values()
        custom_props   = [self.get_proptags().valu('ASYNK_PR_CUSTOM_PROPS')]
        self.def_cols  = (self.get_contents().QueryColumns(mapi.TBL_ALL_COLUMNS) +
                          tuple(sync_tag_props) +
                          tuple(custom_props))

    def get_def_cols (self):
        return self.def_cols

    ## fobj is a pointer to the folder object that is returned by the MAPI
    ## library on opening this folder object.
    def get_fobj (self):
        return self._get_prop('fobj')

    def set_fobj (self, fobj):
        self._set_prop('fobj', fobj)

    def get_msgstore (self):
        return self._get_prop('msgstore')

    def set_msgstore (self, msgstore):
        self._set_prop('msgstore', msgstore)

    ##
    ## Now the more substantial Methods
    ##

    def get_contents (self):
        return self.get_fobj().GetContentsTable(mapi.MAPI_UNICODE)

    def del_entries (self, eids):
        """eids should be a list of EntryIDs - in binary format, as used by
        the MAPI routines."""

        num = len(eids)
        cf  = self.get_fobj()
        if num:
            logging.debug('Deleting %d entries in Outlook', num)
            hr = cf.DeleteMessages(eids, 0, None, 0)
            cf.SaveChanges(mapi.KEEP_OPEN_READWRITE)

    def _clear_tag (self, tags, dryrun=False):
        """Clear any property whose property tag is the provided array."""

        logging.info('Querying MAPI for all data needed to clear flag')
        ctable = self.get_contents()
    
        cols = tuple([mt.PR_ENTRYID, mt.PR_DISPLAY_NAME]) + tuple(tags)
        ctable.SetColumns(cols, 0)
        logging.info('Data obtained from MAPI. Clearing one at a time')

        cnt = set()
        errs = set()
        i   = 0
        store = self.get_msgstore().get_obj()
        hr = ctable.SeekRow(mapi.BOOKMARK_BEGINNING, 0)

        while True:
            rows = ctable.QueryRows(1, 0)
            # if this is the last row then stop
            if len(rows) != 1:
                break

            (entryid_tag, entryid), (name_tag, name) = rows[0][:2]

            i += 1
            for j in range(2, len(rows[0])):
                (gid_tag, gid) = rows[0][j]

                if mt.PROP_TYPE(gid_tag) != mt.PT_ERROR:
                    if not dryrun:
                        entry = store.OpenEntry(entryid, None,
                                                mapi.MAPI_BEST_ACCESS)
                        hr, ps = entry.DeleteProps([gid_tag])
                        if winerror.FAILED(hr):
                            logging.debug('Could not delete sync tag for: %s '
                                          '(%s), due to: %s', name,
                                          base64.b64encode(entryid),
                                          winerror.HRESULT_CODE(hr))
                            errs.add(entryid)
                        else:
                            entry.SaveChanges(0)
                            cnt.add(entryid)

        logging.info('Entries cleared: %d. Errors: %d; i: %d', len(cnt),
                     len(errs), i)

        ctable.SetColumns(self.get_def_cols(), 0)
        return (len(errs) == 0)

    @classmethod
    def get_folder_type (self, store, eid):
        """Returns a Folder_type, folder_obj tuple for the provided folder eid
        in the provided store.

        This fellow could really be anywhere in the *.ol.py files, but
        let's amuse ourselves a bit."""

        f = store.OpenEntry(eid, None, mapi.MAPI_BEST_ACCESS)
        hr, props = f.GetProps([mt.PR_CONTAINER_CLASS,
                                mt.PR_DISPLAY_NAME], mapi.MAPI_UNICODE)
        (ttag, tval), (ntag, nval) = props

        try:
            tval = self.get_ftype_from_cclass(tval)
        except KeyError, e:
            tval = Folder.UNKNOWN_t

        return tval, f

    @classmethod
    def get_cclass_from_ftype (self, ftype):
        return self.ftype_cclass_d[ftype]

    @classmethod
    def get_ftype_from_cclass (self, cclass):
        return self.cclass_ftype_d[cclass]


class OLContactsFolder(OLFolder):
    def __init__ (self, db, entryid, name, fobj, msgstore):
        OLFolder.__init__(self, db, entryid, name, fobj, msgstore)
        self.set_type(Folder.PR_IPM_CONTACT_ENTRYID)

    def print_key_stats (self):
        print 'Contacts Folder Name: ', self.get_name()

class OLNotesFolder(OLFolder):
    def __init__ (self, db, entryid, name, fobj, msgstore):
        OLFolder.__init__(self, db, entryid, name, fobj, msgstore)
        self.set_type(Folder.PR_IPM_NOTE_ENTRYID)

class OLTasksFolder(OLFolder):
    def __init__ (self, db, entryid, name, fobj, msgstore):
        OLFolder.__init__(self, db, entryid, name, fobj, msgstore)
        self.set_type(Folder.PR_IPM_TASK_ENTRYID)

    def print_key_stats (self):
        total       = 0
        recurring   = 0
        expired     = 0
        completed   = 0

        ctable = self.get_obj().GetContentsTable(mapi.MAPI_UNICODE)
        ctable.SetColumns(self.def_cols, 0)

        while True:
            rows = ctable.QueryRows(1, 0)
            #if this is the last row then stop
            if len(rows) != 1:
                break

            total += 1

            props = dict(rows[0])

            try:
                entryid = props[mt.PR_ENTRYID]
            except AttributeError, e:
                entryid = 'Not Available'

            try:
                subject = props[mt.PR_SUBJECT_W]
            except AttributeError, e:
                subject = 'Not Available'

            try:
                complete = props[self.get_proptags().valu('ASYNK_PR_TASK_COMPLETE')]
                if complete:
                    completed += 1
            except KeyError, e:
                complete = 'Not Available'

            try:
                tag = self.get_proptags().valu('ASYNK_PR_TASK_RECUR')
                recurr_status = props[tag]
                if recurr_status:
                    recurring += 1
            except KeyError, e:
                recurr_status = 'Not Available'

            try:
                tag = self.get_proptags().valu('ASYNK_PR_TASK_STATE')
                state = props[tag]
            except KeyError, e:
                state = 'Not Available'

            try:
                tag = self.get_proptags().valu('ASYNK_PR_TASK_DUE_DATE')
                duedate = utils.pytime_to_yyyy_mm_dd(props[tag])
            except KeyError, e:
                duedate = 'Not Available'


            if complete:
                continue

            print 'Task #%3d: Heading: %s' % (total, subject)
            print '\tEntryID   : ', base64.b64encode(entryid)
            print '\tCompleted : ', complete
            print '\tRecurring : ', recurr_status
            print '\tState     : ', state
            print '\tDue Date  : ', duedate
            print '\n'

        print '===== Summary Status for Task Folder: %s ======' % self.name
        print '\tTotal Tasks count : %4d' % total
        print '\tRecurring count   : %4d' % recurring
        print '\tExpired count     : %4d' % expired
        print '\tCompleted count   : %4d' % completed

class OLAppointmentsFolder(OLFolder):
    def __init__ (self, db, entryid, name, fobj, msgstore):
        OLFolder.__init__(self, db, entryid, name, fobj, store)
        self.set_type(Folder.PR_IPM_APPOINTMENT_ENTRYID)

class PropTags:
    """This Singleton class represents a set of all the possible mapi property
    tags. In general the mt module has pretty usable constants
    defined. However MAPI compllicates things with 'Named Properties' - which
    are not static, but have to be generated at runtime (not sure what all
    parameters change it...). This class includes all the mt properties
    as well as a set of hand selected named properties that are relevant for
    us here."""

    PSETID_Address_GUID = '{00062004-0000-0000-C000-000000000046}'
    PSETID_Task_GUID    = '{00062003-0000-0000-c000-000000000046}'

    def __init__ (self, def_cf, config):
        self.name_hash = {}
        self.valu_hash = {}

        # We use the def_cf to lookup named properties. I suspect this will
        # have to be changed when we start supporting multiple profiles and
        # folders...
        self.def_olcf = def_cf
        self.def_cf = def_cf.get_fobj()
        self.config = config

        self.sync_tags = {}
        self.load_proptags()

    def load_proptags (self):
        # Load up all available properties from mt module
        for name, value in mt.__dict__.iteritems():
            if name[:3] == 'PR_':
                # Store both the full ID (including type) and just the ID.
                # This is so PR_FOO_A and PR_FOO_W are still
                # differentiated. Note that in the following call, the value
                # hash will only contain the full ID.
                self.put(name=name, value=mt.PROP_ID(value))
                self.put(name=name, value=value)

        # Now Add a bunch of named properties that we are specifically
        # interested in.

        self.put(name='ASYNK_PR_FILE_AS', value=self.get_file_as_prop_tag())

        self.put(name='ASYNK_PR_EMAIL_1', value=self.get_email_prop_tag(1))
        self.put(name='ASYNK_PR_EMAIL_2', value=self.get_email_prop_tag(2))
        self.put(name='ASYNK_PR_EMAIL_3', value=self.get_email_prop_tag(3))

        self.put(name='ASYNK_PR_IM_1', value=self.get_im_prop_tag(1))

        self.put(name='ASYNK_PR_WORK_ADDRESS_POST_OFFICE_BOX',
                 value=self.get_work_addr_po_prop_tag())
        self.put(name='ASYNK_PR_WORK_ADDRESS_STREET',
                 value=self.get_work_addr_st_prop_tag())
        self.put(name='ASYNK_PR_WORK_ADDRESS_CITY',
                 value=self.get_work_addr_ct_prop_tag())
        self.put(name='ASYNK_PR_WORK_ADDRESS_STATE_OR_PROVINCE',
                 value=self.get_work_addr_sa_prop_tag())
        self.put(name='ASYNK_PR_WORK_ADDRESS_COUNTRY',
                 value=self.get_work_addr_co_prop_tag())
        self.put(name='ASYNK_PR_WORK_ADDRESS_POSTAL_CODE',
                 value=self.get_work_addr_pc_prop_tag())

        self.put('ASYNK_PR_TASK_DUE_DATE', self.get_task_due_date_tag())
        self.put('ASYNK_PR_TASK_STATE',    self.get_task_state_tag())
        self.put('ASYNK_PR_TASK_RECUR',    self.get_task_recur_tag())
        self.put('ASYNK_PR_TASK_COMPLETE', self.get_task_complete_tag())
        self.put('ASYNK_PR_TASK_DATE_COMPLETED',
                 self.get_task_date_completed_tag())

        self.put('ASYNK_PR_CUSTOM_PROPS', self.get_custom_prop_tag())

        self.load_sync_proptags()

    def load_sync_proptags (self):
        conf  = self.config
        mydid = self.def_olcf.get_db().get_dbid()
        olps  = conf.get_db_profiles(mydid)

        for pname, prof in olps.iteritems():
            db1id = conf.get_profile_db1(pname)
            db2id = conf.get_profile_db2(pname)

            stag = conf.make_sync_label(pname,
                                        db1id if db2id == mydid else db2id)
            prop_tag_valu = self.get_gid_prop_tag(pname)

            self.put(name=stag, value=prop_tag_valu)
            self.sync_tags.update({stag : prop_tag_valu})

        # self.put(name='ASYNK_PR_GCID', value=self.get_gid_prop_tag('gc'))
        # self.put(name='ASYNK_PR_BBID', value=self.get_gid_prop_tag('bb'))

    def valu (self, name):
        return self.name_hash[name]

    def name (self, valu):
        return self.valu_hash[valu]

    ## The rest of the methods below are internal to the class.

    def put (self, name, value):
        self.name_hash[name]  = value
        self.valu_hash[value] = name

    # Routines to construct the property tags for named property. Intended to
    # be used only once in the constructor

    def get_email_prop_tag (self, n):
        """MAPI is crappy.

        Email addresses of the EX type do not conatain an SMTP address
        value for their PR_EMAIL_ADDRESS property tag. While the desired
        smtp address is present in the system the property tag that will
        help us fetch it is not a constant and will differ from system
        to system, and from PST file to PST file. The tag has to be
        dynamically generated. Such properties are called named properties in
        Outlook.

        The routine jumps through the requisite hoops and appends those
        property tags to the supplied fields array. The augmented fields
        array is then returned.
        """
        if n <= 1:
            try:
                return self.valu('ASYNK_PR_EMAIL_1')
            except KeyError, e:
                prop_name = [(self.PSETID_Address_GUID, 0x8084)]
                prop_type = mt.PT_UNICODE
                prop_ids = self.def_cf.GetIDsFromNames(prop_name,
                                                       mapi.MAPI_CREATE)
                return (prop_type | prop_ids[0])

        prev_tag      = self.get_email_prop_tag(n-1)
        prev_tag_id   = mt.PROP_ID(prev_tag)
        prev_tag_type = mt.PROP_TYPE(prev_tag)

        return mt.PROP_TAG(prev_tag_type, prev_tag_id+1)

        # FIXME: Fri Jul 19 19:28:48 IST 2013: The Named property we seemed to
        # have been using so far is the dispidEmailOriginalDisplayName which
        # is technically not the Email address itself. The email addresses are
        # set via another named property called dispidEmailEmailAddress. The
        # following code should really do it. The problem with either approach
        # is that if the user sets the Display Name in Outlook that will be
        # lost. That can only be fixed by adding some code to ensure the
        # display name part of it is saved and restored. Till then, let's just
        # stick with the above code that seems to be alteast preserve the
        # email addresses.

        # dispids = [None, amt.dispidEmailEmailAddress,
        #            amt.dispidEmail2EmailAddress,
        #            amt.dispidEmail3EmailAddress]

        # prop_name = [(self.PSETID_Address_GUID, dispids[n])]
        # prop_type = mt.PT_UNICODE
        # prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)
        # return (prop_type | prop_ids[0])        

    def get_im_prop_tag (self, n):
        """I am no expert at this stuff but I found 4 InstantMessaging
        properties looking through the MAPI documentation. They are know by
        these "canonical property names": PidNameInstantMessagingAddress1,
        PidNameInstantMessagingAddress2, PidNameInstantMessagingAddress3 (all
        in the PSETID_AirSync property set) and PidLidInstantMessagingAddress
        that is a part of the PSETID_Address property set. In Outlook 2007
        documentation
        (http://msdn.microsoft.com/en-us/library/cc963764(v=office.12).aspx),
        the first three have been deprected.

        The long and short of all of that is that Outlook only supports a
        singlle instant messaging address, and we have only one property tag
        for that. Thank you."""

        plid = 0x00008062

        if n <= 1:
            try:
                return self.valu('ASYNK_PR_IM_1')
            except KeyError, e:
                prop_name = [(self.PSETID_Address_GUID, plid)]
                prop_type = mt.PT_UNICODE
                prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)
                return (prop_type | prop_ids[0])

        if n > 1:
            return None

    def get_gid_prop_tag (self, pname):
        gid = self.config.get_ol_gid(pname)
        prop_name = [(self.config.get_ol_guid(), gid)]
        prop_type = mt.PT_UNICODE
        prop_ids  = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])

    def get_custom_prop_tag (self):
        conf = self.config
        prop_name = [(conf.get_ol_guid(), conf.get_ol_cus_pid())]
        prop_type = mt.PT_UNICODE
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])

    def get_file_as_prop_tag (self):
        prop_name = [(self.PSETID_Address_GUID, 0x8005)]
        prop_type = mt.PT_UNICODE
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])

    def get_work_addr_po_prop_tag (self):
        prop_name = [(self.PSETID_Address_GUID,
                      amt.dispidWorkAddressPostOfficeBox)]
        prop_type = mt.PT_UNICODE
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])

    def get_work_addr_st_prop_tag (self):
        prop_name = [(self.PSETID_Address_GUID, amt.dispidWorkAddressStreet)]
        prop_type = mt.PT_UNICODE
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])

    def get_work_addr_ct_prop_tag (self):
        prop_name = [(self.PSETID_Address_GUID, amt.dispidWorkAddressCity)]
        prop_type = mt.PT_UNICODE
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])

    def get_work_addr_sa_prop_tag (self):
        prop_name = [(self.PSETID_Address_GUID, amt.dispidWorkAddressState)]
        prop_type = mt.PT_UNICODE
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])

    def get_work_addr_co_prop_tag (self):
        prop_name = [(self.PSETID_Address_GUID, amt.dispidWorkAddressCountry)]
        prop_type = mt.PT_UNICODE
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])

    def get_work_addr_pc_prop_tag (self):
        prop_name = [(self.PSETID_Address_GUID, amt.dispidWorkAddressPostalCode)]
        prop_type = mt.PT_UNICODE
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])

    def get_task_due_date_tag (self):
        prop_name = [(self.PSETID_Task_GUID, 0x8105)]
        prop_type = mt.PT_SYSTIME
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])

    def get_task_date_completed_tag (self):
        prop_name = [(self.PSETID_Task_GUID, 0x810f)]
        prop_type = mt.PT_SYSTIME
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])

    def get_task_state_tag (self):
        prop_name = [(self.PSETID_Task_GUID, 0x8113)]
        prop_type = mt.PT_LONG
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])

    def get_task_complete_tag (self):
        prop_name = [(self.PSETID_Task_GUID, 0x811c)]
        prop_type = mt.PT_BOOLEAN
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])

    def get_task_recur_tag (self):
        prop_name = [(self.PSETID_Task_GUID, 0x8126)]
        prop_type = mt.PT_BOOLEAN
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, mapi.MAPI_CREATE)

        return (prop_type | prop_ids[0])
