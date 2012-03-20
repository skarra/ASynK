##
## Created       : Wed May 18 13:16:17 IST 2011
## Last Modified : Tue Mar 20 16:12:44 IST 2012
##
## Copyright (C) 2011, 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

import sys, os, logging, traceback

if __name__ == "__main__":
    ## Being able to fix the sys.path thusly makes is easy to execute this
    ## script standalone from IDLE. Hack it is, but what the hell.
    DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('../Gout')))
    EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib')]
    sys.path = EXTRA_PATHS + sys.path

from   abc            import ABCMeta, abstractmethod
from   folder         import Folder
from   win32com.mapi  import mapi, mapitags, mapiutil

class OLFolder(Folder):
    """An Outlook folder directly corresponds to a MAPI Folder entity. This
    class wraps a mapi folder object while implementing the normalized Folder
    methods and accessors defined by Gout.

    This itself is an abstract class, and only its derived classes can be
    instantiated.
    """

    __metaclass__ = ABCMeta

    def __init__ (self, db, entryid, name, fobj, msgstore):
        Folder.__init__(self, db)

        self.set_entryid(entryid)
        self.set_name(name)
        self.set_fobj(fobj)
        self.set_msgstore(msgstore)

        self.set_proptags(PropTags(self.get_fobj(), self.get_config()))
        self.reset_def_cols()

    ##
    ## Implementation of some abstract methods inherted from Folder
    ##

    def prep_sync_lists (self, destid, last_sync_stop, limit=0):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def insert_new_items (self, items):
        """See the documentation in folder.Folder"""

        raise NotImplementedError

    def bulk_clear_sync_flags (self, dbids):
        """See the documentation in folder.Folder. 

        Need to explore if there is a faster way than iterating through
        entries after a table lookup.
        """
        for dbid in dbids:
            if dbid == 'gc':
                tag = 'GOUT_PR_GCID'
            elif dbid == 'bb':
                tag = 'GOUT_PR_BBID'
        self._clear_tag(tag)

    def __str__ (self):
        if self.type == Folder.PR_IPM_CONTACT_ENTRYID:
            ret = 'Contacts'
        elif self.type == Folder.PR_IPM_NOTE_ENTRYID:
            ret = 'Notes'
        elif self.type == Folder.PR_IPM_TASK_ENTRYID:
            ret = 'Tasks'

        return ('%s.\tName: %s;\tEID: %s;\tStore: %s' % (
            ret, self.name, base64.b64encode(self.entryid),
            self.store.name))        

    ##
    ## First some get_ and set_ routines
    ##

    ## Note: Entryid and itemid have identical values, but maintanined
    ## independently for clarity

    def get_entryid (self):
        return self._get_prop('entryid')

    def set_entryid (self, entryid):
        self._set_prop('entryid', entryid)
        self.set_itemid(entryid)

    def get_proptags (self):
        return self.proptags

    def set_proptags (self, p):
        self.proptags = p

    def reset_def_cols (self):
        self.def_cols  = (self.get_contents().QueryColumns(0) +
                          (self.get_proptags().valu('GOUT_PR_GCID'),))

    def get_def_cols (self):
        return self.def_cols

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

    def _clear_tag (self, tag):
        logging.info('Querying MAPI for all data needed to clear flag')
        ctable = self.get_contents()
        ctable.SetColumns((self.prop_tags.valu(tag), mapitags.PR_ENTRYID), 0)
        logging.info('Data obtained from MAPI. Clearing one at a time')

        cnt = 0
        i   = 0
        store = self.get_msgstore()
        hr = ctable.SeekRow(mapi.BOOKMARK_BEGINNING, 0)

        while True:
            rows = ctable.QueryRows(1, 0)
            # if this is the last row then stop
            if len(rows) != 1:
                break
    
            (gid_tag, gid), (entryid_tag, entryid) = rows[0]

            i += 1
            if mapitags.PROP_TYPE(gid_tag) != mapitags.PT_ERROR:
                entry = store.OpenEntry(entryid, None, MOD_FLAG)
                hr, ps = entry.DeleteProps([gid_tag])
                entry.SaveChanges(mapi.KEEP_OPEN_READWRITE)

                cnt += 1

        logging.info('Num entries cleared: %d. i = %d', cnt, i)
        return cnt

class OLContactsFolder(OLFolder):
    def __init__ (self, db, entryid, name, fobj, msgstore):
        OLFolder.__init__(self, db, entryid, name, fobj, msgstore)
        self.set_type(Folder.PR_IPM_CONTACT_ENTRYID)

        self.print_key_stats()

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
                entryid = props[mapitags.PR_ENTRYID]
            except AttributeError, e:
                entryid = 'Not Available'

            try:
                subject = props[mapitags.PR_SUBJECT_W]
            except AttributeError, e:
                subject = 'Not Available'

            try:
                complete = props[self.prop_tags.valu('GOUT_PR_TASK_COMPLETE')]
                if complete:
                    completed += 1
            except KeyError, e:
                complete = 'Not Available'

            try:
                tag = self.prop_tags.valu('GOUT_PR_TASK_RECUR')
                recurr_status = props[tag]
                if recurr_status:
                    recurring += 1
            except KeyError, e:
                recurr_status = 'Not Available'

            try:
                tag = self.prop_tags.valu('GOUT_PR_TASK_STATE')
                state = props[tag]
            except KeyError, e:
                state = 'Not Available'

            try:
                tag = self.prop_tags.valu('GOUT_PR_TASK_DUE_DATE')
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
    tags. In general the mapitags module has pretty usable constants
    defined. However MAPI compllicates things with 'Named Properties' - which
    are not static, but have to be generated at runtime (not sure what all
    parameters change it...). This class includes all the mapitags properties
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
        self.def_cf = def_cf
        self.config = config

        # Load up all available properties from mapitags module

        for name, value in mapitags.__dict__.iteritems():
            if name[:3] == 'PR_':
                # Store both the full ID (including type) and just the ID.
                # This is so PR_FOO_A and PR_FOO_W are still
                # differentiated. Note that in the following call, the value
                # hash will only contain the full ID.
                self.put(name=name, value=mapitags.PROP_ID(value))
                self.put(name=name, value=value)

        # Now Add a bunch of named properties that we are specifically
        # interested in.

        self.put(name='GOUT_PR_FILE_AS', value=self.get_file_as_prop_tag())

        self.put(name='GOUT_PR_EMAIL_1', value=self.get_email_prop_tag(1))
        self.put(name='GOUT_PR_EMAIL_2', value=self.get_email_prop_tag(2))
        self.put(name='GOUT_PR_EMAIL_3', value=self.get_email_prop_tag(3))

        self.put(name='GOUT_PR_GCID', value=self.get_gid_prop_tag())

        self.put('GOUT_PR_TASK_DUE_DATE', self.get_task_due_date_tag())
        self.put('GOUT_PR_TASK_STATE',    self.get_task_state_tag())
        self.put('GOUT_PR_TASK_RECUR',    self.get_task_recur_tag())
        self.put('GOUT_PR_TASK_COMPLETE', self.get_task_complete_tag())
        self.put('GOUT_PR_TASK_DATE_COMPLETED',
                 self.get_task_date_completed_tag())

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
        dynamically generated.

        The routine jumps through the requisite hoops and appends those
        property tags to the supplied fields array. The augmented fields
        array is then returned.
        """
        if n <= 1:
            try:
                return self.valu('GOUT_PR_EMAIL_1')
            except KeyError, e:
                prop_name = [(self.PSETID_Address_GUID, 0x8084)]
                prop_type = mapitags.PT_UNICODE
                prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)
                return (prop_type | prop_ids[0])

        prev_tag      = self.get_email_prop_tag(n-1)
        prev_tag_id   = mapitags.PROP_ID(prev_tag)
        prev_tag_type = mapitags.PROP_TYPE(prev_tag)

        return mapitags.PROP_TAG(prev_tag_type, prev_tag_id+1)        

    def get_gid_prop_tag (self):
        ## FIXME: The following is a terrible that needs to be fixed
        ## immediately...
        prop_name = [(self.config.get_olsync_guid(),
                      self.config.get_olsync_gid_next())]
        prop_type = mapitags.PT_UNICODE
        prop_ids  = self.def_cf.GetIDsFromNames(prop_name, 0)

        return (prop_type | prop_ids[0])

    def get_file_as_prop_tag (self):
        prop_name = [(self.PSETID_Address_GUID, 0x8005)]
        prop_type = mapitags.PT_UNICODE
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)

        return (prop_type | prop_ids[0])        

    def get_task_due_date_tag (self):
        prop_name = [(self.PSETID_Task_GUID, 0x8105)]
        prop_type = mapitags.PT_SYSTIME
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)

        return (prop_type | prop_ids[0])        

    def get_task_date_completed_tag (self):
        prop_name = [(self.PSETID_Task_GUID, 0x810f)]
        prop_type = mapitags.PT_SYSTIME
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)

        return (prop_type | prop_ids[0])        

    def get_task_state_tag (self):
        prop_name = [(self.PSETID_Task_GUID, 0x8113)]
        prop_type = mapitags.PT_LONG
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)

        return (prop_type | prop_ids[0])        

    def get_task_complete_tag (self):
        prop_name = [(self.PSETID_Task_GUID, 0x811c)]
        prop_type = mapitags.PT_BOOLEAN
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)

        return (prop_type | prop_ids[0])        

    def get_task_recur_tag (self):
        prop_name = [(self.PSETID_Task_GUID, 0x8126)]
        prop_type = mapitags.PT_BOOLEAN
        prop_ids = self.def_cf.GetIDsFromNames(prop_name, 0)

        return (prop_type | prop_ids[0])        

def main (argv=None):

    from state import Config
    from pimdb_ol import OLPIMDB

    logging.debug('Getting started... Reading Config File...')
    config = Config('../app_state.json')
    
    ol     = OLPIMDB(config)

if __name__ == "__main__":    
    logging.getLogger().setLevel(logging.DEBUG)
    try:
        main()
    except Exception, e:
        print 'Caught Exception... Hm. Need to cleanup.'
        print 'Full Exception as here:', traceback.format_exc()
