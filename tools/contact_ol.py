##
## Created       : Sun Dec 04 19:42:50 IST 2011
## Last Modified : Sun Apr 01 16:19:52 IST 2012
##
## Copyright (C) 2011, 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
##
## This file extends the Contact base class to implement an Outlook Contact
## item while implementing the base class methods.

import base64, logging, os, sys, traceback, utils
from   datetime import datetime

if __name__ == "__main__":
    ## Being able to fix the sys.path thusly makes is easy to execute this
    ## script standalone from IDLE. Hack it is, but what the hell.
    DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('../Gout')))
    EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib')]
    sys.path = EXTRA_PATHS + sys.path

from   contact import Contact
from   win32com.mapi import mapitags as mt
from   win32com.mapi import mapi
import winerror

def yyyy_mm_dd_to_pytime (date_str):
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return pywintypes.Time(dt.timetuple())

def pytime_to_yyyy_mm_dd (pyt):
    return ('%04d-%02d-%02d' % (pyt.year, pyt.month, pyt.day))

class OLContactError(Exception):
    pass

class OLContact(Contact):
    prop_update_t = utils.enum('PROP_REPLACE', 'PROP_APPEND')

    def __init__ (self, folder, olprops=None, eid=None, con=None):
        """Constructor for OLContact. The starting properties of the contact
        can be initialized either from an existing Contact object, or from an
        Outlook item property list. It is an error to provide both.

        It is redundant to provide both olprops (array of property tuples) and
        an entryid. The entryid will override the property list.
        """

        if ((olprops and con) or (eid and con)):
            raise OLContactError(
                'Both olprops/eid and con cannot be specified in OLContact()')

        if olprops and eid:
            logging.warning('olprops and eid are not null. Ignoring olprops')
            olprops = None

        Contact.__init__(self, folder, con)

        ## Set up some of the basis object attributes and parent folder/db
        ## properties to make it easier to access them

        self.set_db_config(self.get_config().get_db_config(self.get_dbid()))
        self.set_sync_fields(self.get_db_config()['sync_fields'])
        self.set_email_domains(self.get_db_config()['email_domains'])
        self.set_proptags(folder.get_proptags())

        self.set_olprops(olprops)

        if olprops:
            self.init_props_from_olprops(olprops)
        elif eid:
            self.init_props_from_eid(eid)

    ##
    ## First the inherited abstract methods from the base classes
    ##

    def save (self):
        """Saves the current contact to Outlook so it is persistent. Returns
        the itemid for the saved entry. Returns None in case of an error"""

        ## FIXME: This only takes care of new insertions. In-place updates are
        ## not taken care of by this. The situation needs fixing on a fairly
        ## urgent basis.

        logging.info('Saving to Outlook: %-32s ....', self.get_name())
        fobj = self.get_folder().get_fobj()
        msg = fobj.CreateMessage(None, 0)

        if not msg:
            return None

        hr, res = msg.SetProps(self.get_olprops())
        if (winerror.FAILED(hr)):
            logging.critical('push_to_outlook(): unable to SetProps (code: %x)',
                             winerror.HRESULT_CODE(hr))
            return None

        msg.SaveChanges(mapi.KEEP_OPEN_READWRITE)

        # Now that we have successfully saved the record, let's fetch the
        # entryid and return it to the caller.

        hr, props  = msg.GetProps([mt.PR_ENTRYID], mapi.MAPI_UNICODE)
        (tag, val) = props[0]
        if mt.PROP_TYPE(tag) == mt.PT_ERROR:
            logging.error('save: EntryID could not be found. Weird')
            return None
        else:
            return val
    ##
    ## Now onto the non-abstract methods.
    ##

    def get_entryid (self):
        return self._get_att('entryid')

    def set_entryid (self, eid):
        """Set the entryid, and also the itemid - which is the base64 encoded
        value of the binary entryid."""

        self._set_att('entryid', eid)
        self.set_itemid(base64.b64encode(eid))
        return eid

    def get_db_config (self):
        return self._get_att('db_config')

    def set_db_config (self, dbc):
        return self._set_att('db_config', dbc)

    def get_proptags (self):
        return self.proptags

    def set_proptags (self, p):
        self.proptags = p

    def get_olitem (self):
        """Returns a reference to the underlying outlook item obtained from a
        MAPI OpenMsg() call, if possible. If the contact has just been
        created, and not been saved, there would not be a olitem yet, and in
        that case a None is returned. None is also returned in case of some
        error."""

        res = self._get_att('olitem')
        if res:
            return res

        eid = self.get_entryid()
        if not eid:
            logging.debug('OLContact.get_olitem: No olitem or entryid yet')
            return None

        msgstore = self.get_folder().get_msgstore()
        res = msgstore.OpenEntry(eid, None, MOD_FLAG)
        if res:
            return self._set_att('olitem', res)

    def set_olitem (self, olitem):
        return self._set_att('olitem', olitem)

    def get_sync_fields (self):
        return self._get_att('sync_fields')

    def set_sync_fields (self, sf):
        return self._set_att('sync_fields', sf)

    def get_email_domains (self):
        return self._get_att('email_domains')

    def set_email_domains (self, sf):
        return self._set_att('email_domains', sf)

    def get_olprops (self, refresh=True):
        """Get an array of property tuples (tag, value) that is useful in MAPI
        routines. Every call to this routine will regenerate the olprops
        property array from the contacts' fields, and return it. Callers
        should cache the value if no changes are anticipated, in the interest
        of performance"""

        if refresh:
            return self.init_olprops_from_props()
        else:
            return self._get_att('olprops')

    def get_olprops_from_mapi (self, entryid=None):
        """This reads the current contact's entire property list from MAPI and
        returns an array of property tuples"""

        pass

    def set_olprops (self, olprops):
        return self._set_att('olprops', olprops)

    def init_props_from_olprops (self, olprops):
        olpd = self._make_olprop_dict(olprops, self.get_sync_fields())

        self._snarf_itemid_from_olprops(olpd)
        self._snarf_names_gender_from_olprops(olpd)
        self._snarf_notes_from_olprops(olpd)
        self._snarf_emails_from_olprops(olpd)
        self._snarf_postal_from_olprops(olpd)
        self._snarf_org_details_from_olprops(olpd)
        self._snarf_phones_and_faxes_from_olprops(olpd)
        self._snarf_dates_from_olprops(olpd)
        self._snarf_websites_from_olprops(olpd)
        self._snarf_ims_from_olprops(olpd)

        self._snarf_custom_props_from_olprops(olpd)

    def init_props_from_eid (self, eid):
        self.set_itemid(eid)
        oli = self.get_olitem()

    def init_olprops_from_props (self):
        # There are a few message properties that are sort of 'expected' to be
        # set. Most are set automatically by the store provider or the
        # transport provider. However some have to be set by the client; so,
        # let's do the honors. More on this here:
        # http://msdn.microsoft.com/en-us/library/cc839866(v=office.12).aspx
        # http://msdn.microsoft.com/en-us/library/cc839595(v=office.12).aspx

        olprops = [(mt.PR_MESSAGE_CLASS, "IPM.Contact")]

        self._add_itemid_to_olprops(olprops)
        self._add_names_gender_to_olprops(olprops)
        self._add_notes_to_olprops(olprops)
        self._add_emails_to_olprops(olprops)
        self._add_postal_to_olprops(olprops)
        self._add_org_details_to_olprops(olprops)
        self._add_phones_and_faxes_to_olprops(olprops)
        self._add_dates_to_olprops(olprops)
        self._add_websites_to_olprops(olprops)
        self._add_ims_to_olprops(olprops)

        self._add_custom_props_to_olprops(olprops)

        return self.set_olprops(olprops)

    def __str__ (self):
        ret = ''

        props = self.get_prop_names()
        for prop in props:
            ret += '%18s: %s\n' % (prop, self._get_prop(prop))

        return ret

    ##
    ## Internal functions that are not inteded to be called from outside.
    ##

    def _snarf_itemid_from_olprops (self, olpd):
        self.set_itemid(self._get_olprop(olpd, mt.PR_ENTRYID))
        self.set_entryid(self.get_itemid())

    def _snarf_names_gender_from_olprops (self, olpd):
        ## FIXME: I suppose there must be some way MAPI uses the firstname and
        ## lastname etc instead of just the full display name. Learn to handle
        ## it.

        self.set_name(self._get_olprop(olpd, mt.PR_DISPLAY_NAME))
        self.set_firstname(self._get_olprop(olpd, mt.PR_GIVEN_NAME))
        self.set_lastname(self._get_olprop(olpd, mt.PR_SURNAME))
        self.set_prefix(self._get_olprop(olpd, mt.PR_DISPLAY_NAME_PREFIX))
        self.set_suffix(self._get_olprop(olpd, mt.PR_GENERATION))
        self.set_nickname(self._get_olprop(olpd, mt.PR_NICKNAME))
        self.set_gender(self._get_olprop(olpd, mt.PR_GENDER))

    def _snarf_notes_from_olprops (self, olprop):
        self.add_notes(self._get_olprop(olpd, mt.PR_BODY))

    def _snarf_emails_from_olprops (self, olprop):
        ## Build an array out of the three email addresses as applicable
        email1 = self.get_proptags().valu('ASYNK_PR_EMAIL_1')
        email2 = self.get_proptags().valu('ASYNK_PR_EMAIL_2')
        email3 = self.get_proptags().valu('ASYNK_PR_EMAIL_3')

        eds = self.get_email_domains()

        self._snarf_email (email1, eds)
        self._snarf_email (email2, eds)
        self._snarf_email (email3, eds)

    def _snarf_email (self, tag, domains):
        """Fetch the email address using the specified tag, classify the
        addres into home, work or other, and file them into the appropriate
        property field.

        tag is the property tag that is to be used to look up an email
        address from the properties array. domains is the email_domains
        dictionary from the app state config file that is used to """

        addr = self._get_olprop(olpd, tag)
        work, work, other = self._classify_email_addr(addr, domains)

        ## Note that the following implementation means if the same domain is
        ## specified in more than one category, it ends up being copied to
        ## every category. In effect this means when this is synched to google
        ## contacts, the GC entry will have the same email address twice for
        ## the record

        if home:
            self.add_email_home(e1)

        if work:
            self.add_email_work(e1)

        if other:
            self.add_email_other(e1)

    def _classify_email_addr (self, addr, domains):
        """Return a tuple of (home, work, other) booleans classifying if the
        specified address falls within one of the domains."""

        res = {'home' : False, 'work' : False, 'other' : False}

        for cat in res.keys():
            try:
                for domain in domains[cat]:
                    if re.search((domain + '$'), addr):
                        res[cat] = True
            except KeyError, e:
                logging.warning('Invalid email_domains specification.')

        return (res['home'], res['work'], res['other'])


    def _snarf_postal_from_olprops (self, olpd):
        self.set_postal(self._get_olprop(olpd, mt.PR_POSTAL_ADDRESS))

    def _snarf_org_details_from_olprops (self, olpd):
        self.set_company( self._get_olprop(olpd, mt.PR_COMPANY_NAME))
        self.set_title(   self._get_olprop(olpd, mt.PR_TITLE))
        self.set_dept(    self._get_olprop(olpd, mt.PR_DEPARTMENT_NAME))

    def _snarf_phones_and_faxes_from_olprops (self, olpd):
        self.set_phone_prim(
            self._get_olprop(olpd, mt.PR_PRIMARY_TELEPHONE_NUMBER))
        self.add_phone_mob(
            self._get_olprop(olpd, mt.PR_MOBILE_TELEPHONE_NUMBER))
        self.add_phone_home(
            self._get_olprop(olpd, mt.PR_HOME_TELEPHONE_NUMBER))
        self.add_phone_home(
            self._get_olprop(olpd, mt.PR_HOME2_TELEPHONE_NUMBER))
        self.add_phone_work(
            self._get_olprop(olpd, mt.PR_BUSINESS_TELEPHONE_NUMBER))
        self.add_phone_work(
            self._get_olprop(olpd, mt.PR_BUSINESS2_TELEPHONE_NUMBER))
        self.add_phone_other(
            self._get_olprop(olpd, mt.PR_OTHER_TELEPHONE_NUMBER))

        self.set_phone_prim(
            self._get_olprop(olpd, mt.PR_PRIMARY_FAX_NUMBER))
        self.add_fax_home(
            self._get_olprop(olpd, mt.PR_HOME_FAX_NUMBER))
        self.add_fax_work(
            self._get_olprop(olpd, mt.PR_BUSINESS_FAX_NUMBER))

    def _snarf_dates_from_olprop (self, olpd):
        date = pytime_to__yyyy_mm_dd(self._get_olprop(olpd, mt.PR_BIRTHDAY))
        self.set_birthday(date)

        date = pytime_to__yyyy_mm_dd(
            self._get_olprop(olpd, mt.PR_WEDDING_ANNIVERSARY))
        self.set_anniv(date)

    def _snarf_websites_from_olprops (self, olpd):
        self.add_web_home(self._get_olprop(olpd, mt.PR_PERSONAL_HOME_PAGE))
        self.add_web_work(self._get_olprop(olpd, mt.PR_BUSINESS_HOME_PAGE))

        ## The End.


    # def left_overs (self):
    #     self.gcid = self._get_prop(self.get_proptags().valu('ASYNK_PR_GCID'))
    #     self.last_mod  = self._get_olprop(olpd, mt.PR_LAST_MODIFICATION_TIME)

    def _snarf_ims_from_olprops (self, olpd):
        """In Outlook IM Addresses are also named properties like Email
        addresses..."""

        im = self.get_proptags().valu('ASYNK_PR_IM_1')
        self.add_im(self._get_olprop(olpd, im))

    def _snarf_custom_props_from_olprops (self, olpd):
        logging.error("_snarf_custom_props_ol(): Not Implemented Yet")

    def _make_olprop_dict (self, olprops, fields):
        """olprops is an array of property tuples - the sort of thing that is
        returned by GetColumns routine of MAPI, etc. This routine takes
        olprops and converts it into a dictionary with the tag as key and
        value as the, er, value - while limiting to only those tags that are
        present in the fields array"""

        ar = {}
        for field in fields:
            ar[field] = []

        for t, v in olprops:
            if t in fields:
                ar[t].append(v)

        return ar

    def _add_itemid_to_olprops (self, olprops):
        return

    def _add_names_gender_to_olprops (self, olprops):
        n = self.get_name()
        if n:
            olprops.append((mt.PR_DISPLAY_NAME, n))

        fatag = self.get_proptags().valu('ASYNK_PR_FILE_AS')
        if self.get_fileas():
            olprops.append((fatag, self.get_fileas()))
        else:
            ## If there is no fileas set, Let's put in some default.
            ## The default should be configurable the user: FIXME
            olprops.append((fatag, self.get_name()))

        ln = self.get_lastname()
        if ln:
            olprops.append((mt.PR_SURNAME, ln))

        gn = self.get_firstname()
        if gn:
            olprops.append((mt.PR_GIVEN_NAME, gn))

        pr = self.get_prefix()
        if pr:
            olprops.append((mt.PR_DISPLAY_NAME_PREFIX, pr))

        su = self.get_suffix()
        if su:
            olprops.append((mt.PR_GENERATION, pr))

    def _add_notes_to_olprops (self, olprops):
        notes = self.get_notes()
        if notes:
            olprops.append((mt.PR_BODY, notes))

    def _add_emails_to_olprops (self, olprops):
        """Outlook has space only for 3 email addressess. The Gout internal
        representation as well as the representation in other PIMDBs does not
        allow us to maintain the same order on a round trip sync without a
        significant amount of additional work. In the absence of that we do a
        hack here which is to first assign all work addresses, then home
        addresses and then finally other addresses"""

        i = 0
        for email in self.get_email_home():
            i += 1
            if i > 3:
                return

            tag = self.get_proptags().valu('ASYNK_PR_EMAIL_%d' % i)
            olprops.append((tag, email))

        for email in self.get_email_work():
            i += 1
            if i > 3:
                return

            tag = self.get_proptags().valu('ASYNK_PR_EMAIL_%d' % i)
            olprops.append((tag, email))

        for email in self.get_email_other():
            i += 1
            if i > 3:
                return

            tag = self.get_proptags().valu('ASYNK_PR_EMAIL_%d' % i)
            olprops.append((tag, email))

    def _add_postal_to_olprops (self, olprops):
        postal = self.get_postal()
        if postal:
            olprops.append((mt.PR_POSTAL_ADDRESS, postal))

    def _add_org_details_to_olprops (self, olprops):
        name = self.get_company()
        if name:
            olprops.append((mt.PR_COMPANY_NAME, name))

        title = self.get_title()
        if title:
            olprops.append((mt.PR_TITLE, title))

        dept = self.get_dept()
        if dept:
            olprops.append((mt.PR_DEPARTMENT_NAME, dept))

    def _add_phones_and_faxes_to_olprops (self, olprops):
        ## FIXME: We have to deal with more than two phone numbers each
        phh     = self.get_phone_home()
        phh_cnt = len(phh)
        if phh_cnt >= 1:
            olprops.append((mt.PR_HOME_TELEPHONE_NUMBER, phh[0]))

        if phh_cnt >= 2:
            olprops.append((mt.PR_HOME2_TELEPHONE_NUMBER, phh[1]))

        phw     = self.get_phone_work()
        phw_cnt = len(phw)
        if phw_cnt >= 1:
            olprops.append((mt.PR_BUSINESS_TELEPHONE_NUMBER, phw[0]))

        if phw_cnt >= 2:
            olprops.append((mt.PR_BUSINESS2_TELEPHONE_NUMBER, phw[1]))

        phm = self.get_phone_mob()
        if len(phm) >= 1:
            olprops.append((mt.PR_MOBILE_TELEPHONE_NUMBER, phm[0]))

        ph_prim = self.get_phone_prim()
        if ph_prim:
            olprops.append((mt.PR_PRIMARY_TELEPHONE_NUMBER, ph_prim))

        fah = self.get_fax_home()
        if len(fah) >= 1:
            olprops.append((mt.PR_HOME_FAX_NUMBER, fah[0]))

        faw = self.get_fax_work()
        if len(faw) >= 1:
            olprops.append((mt.PR_BUSINESS_FAX_NUMBER, faw[0]))

        fax_prim = self.get_fax_prim()
        if fax_prim:
            olprops.append((mt.PR_PRIMARY_FAX_NUMBER, fax_prim))

    def _add_dates_to_olprops (self, olprops):
        bday = self.get_birthday()
        if bday:
            bday = yyyy_mm_dd_to_pytime(bday)
            props.append((mt.PR_BIRTHDAY, bday))

        anniv = self.get_anniv()
        if anniv:
            anniv = yyyy_mm_dd_to_pytime(anniv)
            props.append((mt.PR_WEDDING_ANNIVERSARY, anniv))

    def _add_websites_to_olprops (self, olprops):
        ## FIXME: What happens to additional websites?
        web = self.get_web_home()
        if web:
            props.append((mt.PR_PERSONAL_HOME_PAGE, web[0]))

        web = self.get_web_work()
        if web:
            props.append((mt.PR_BUSINESS_HOME_PAGE, web[0]))

    def _add_ims_to_olprops (self, olprops):
        im = self.get_im()
        if im:
            tag = self.get_proptags().valu('ASYNK_PR_IM_1')
            olprops.append((tag, im[0]))

    def _add_custom_props_to_olprops (self, olprops):
        logging.error("_add_custom_props_ol(): Not Implemented Yet")

def main (argv=None):
    tests = TestOLContact()
    tests.test_sync_status()

class TestOLContact:
    def __init__ (self):
        from state import Config
        from pimdb_ol import OLPIMDB

        logging.debug('Getting started... Reading Config File...')

        self.config = Config('../app_state.json')
        self.ol     = OLPIMDB(self.config)
        self.deff   = self.ol.get_def_folder()

        print "\nHurrah: Name is: ", self.deff.get_name()

    def test_new_contact (self):
        c = OLContact(self.deff)
        c.set_name('Goofy Ball')
        c.set_gender('Male')
        c.set_notes('This is a test from the newly created good stuff')
        c.save()

    def test_sync_status (self):
        from   sync       import SyncLists
        sl = SyncLists(self.deff, 'gc')
        self.deff.prep_sync_lists('gc', sl)

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    try:
        main()
    except Exception, e:
        print 'Caught Exception... Hm. Need to cleanup.'
        print 'Full Exception as here:', traceback.format_exc()

## FIXME: Needs more thorough unit testing.
