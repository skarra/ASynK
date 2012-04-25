##
## Created       : Tue Mar 13 14:26:01 IST 2012
## Last Modified : Wed Apr 25 18:02:39 IST 2012
##
## Copyright (C) 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
##
## This file defines an abstract base Contact class essentially as a way of
## documenting what this application considers as a normalized contact
## container. The "Copy Constructor" of this class will be the bridge across
## contact entries from different databases.
##

from abc     import ABCMeta, abstractmethod
from pimdb   import PIMDB
from item    import Item

import copy, logging

class Contact(Item):
    __metaclass__ = ABCMeta

    def __init__ (self, folder, con=None):
        """Constructor for the abstract base class Contact. If con is not
        None, this behaves like pseudo copy constructor, copying all the
        contact properties from the pass contact. Note, in particular that all
        the 'object attributes' of con are left untouched, and are populated
        as per the general rules of creating a new contact."""

        Item.__init__(self, folder)

        self.props.update({'firstname'    : None, 'company'      : None,
                           'lastname'     : None, 'postal'       : {},
                           'middlename'   : None, 'notes'        : [],
                           'name'         : None, 'phone_home'   : [],
                           'suffix'       : None, 'phone_work'   : [],
                           'title'        : None, 'phone_mob'    : [],
                           'gender'       : None, 'phone_other'  : [],
                           'nickname'     : None, 'phone_prim'   : None,
                           'birthday'     : None, 'fax_home'     : [],
                           'anniv'        : None, 'fax_work'     : [],
                           'web_home'     : [],   'fax_prim'     : None,
                           'web_work'     : [],   'email_home'   : [],
                           'web_prim'     : None, 'email_work'   : [],
                           'dept'         : None, 'email_other'  : [],
                           'fileas'       : None, 'email_prim'   : None,
                           'prefix'       : None, 'im_prim'      : None,
                           'im'           : {},   'custom'       : {},
                           })

        if con:
            self.init_props_from_con(con)

    ##
    ## Now onto the non-abstract methods. We do not want to use method
    ## generators - it makes the code harder to read and maintain. It would be
    ## simple to enforce range checking and other validation when it's in
    ## plain english like so.
    ##

    def init_props_from_con (self, con):
        """Make a deepcopy of all the item properties from con into the props
        dictionary, utilizing the appropriate get_ and set_ routines.
        """

        prop_names = con.get_prop_names()
        for prop in prop_names:
            get_method = 'get_%s' % prop
            set_method = 'set_%s' % prop

            val = copy.deepcopy(getattr(con, get_method)())
            # logging.debug('setting value (%s) using method: %s',
            #               val, set_method)
            getattr(self, set_method)(val)

    def get_firstname (self):
        return self._get_prop('firstname')

    def set_firstname (self, val):
        self._set_prop('firstname', val)
        #        self.update_fullname()

    def get_lastname (self):
        return self._get_prop('lastname')

    def set_lastname (self, val):
        self._set_prop('lastname', val)
        #        self.update_fullname()

    def get_middlename (self):
        return self._get_prop('middlename')

    def set_middlename (self, val):
        self._set_prop('middlename', val)

    def update_fullname (self):
        pr = self.get_prefix()
        fn = self.get_firstname()
        ln = self.get_lastname()
        su = self.get_suffix()

        name = pr if pr else ''
        name += fn if fn else ''
        name += ln if ln else ''
        name += su if su else ''

        self._set_prop('name', name)

    def get_name (self):
        return self._get_prop('name')

    def set_name (self, val):
        self._set_prop('name', val)
        return val

    def get_prefix (self):
        return self._get_prop('prefix')

    def set_prefix (self, val):
        return self._set_prop('prefix', val)

    def get_suffix (self):
        return self._get_prop('suffix')

    def set_suffix (self, val):
        return self._set_prop('suffix', val)

    def get_fileas (self):
        return self._get_prop('fileas')

    def set_fileas (self, val):
        return self._set_prop('fileas', val)

    def get_gender (self):
        return self._get_prop('gender')

    def set_gender (self, val):
        return self._set_prop('gender', val)

    def get_nickname (self):
        return self._get_prop('nickname')

    def set_nickname (self, val):
        return self._set_prop('nickname', val)

    def get_birthday (self):
        return self._get_prop('birthday')

    def set_birthday (self, val):
        return self._set_prop('birthday', val)

    def get_anniv (self):
        return self._get_prop('anniv')

    def set_anniv (self, val):
        return self._set_prop('anniv', val)

    def get_web_prim (self):
        return self._get_prop('web_prim')

    def set_web_prim (self, val):
        return self._set_prop('web_prim', val)

    def get_web_home (self):
        return self._get_prop('web_home')

    def set_web_home (self, val):
        return self._set_prop('web_home', val)

    def add_web_home (self, val):
        return self._append_to_prop('web_home', val)

    def get_web_work (self):
        return self._get_prop('web_work')

    def set_web_work (self, val):
        return self._set_prop('web_work', val)

    def add_web_work (self, val):
        return self._append_to_prop('web_work', val)

    def get_company (self):
        return self._get_prop('company')

    def set_company (self, val):
        return self._set_prop('company', val)

    def get_title (self):
        return self._get_prop('title')

    def set_title (self, val):
        return self._set_prop('title', val)

    def get_dept (self):
        return self._get_prop('dept')

    def set_dept (self, val):
        if val:
            return self._set_prop('dept', val)

    def get_postal (self, which=None):
        postals = self._get_prop('postal')
        if which:
            return postals[which]
        else:
            return postals

    def set_postal (self, val):
        return self._set_prop('postal', val)

    def add_postal (self, which, val):
        return self._update_prop('postal', which, val)

    def add_postal_detail (self, which, detail, val):
        postal = self.get_postal(which)
        if postal:
            postal.update({detail : val})
        else:
            self.set_postal(which, {detail : val})

    def get_notes (self):
        return self._get_prop('notes')

    def set_notes (self, val):
        return self._set_prop('notes', val)

    def add_notes (self, val):
        return self._append_to_prop('notes', val)

    def get_email_prim (self):
        return self._get_prop('email_prim')

    def set_email_prim (self, val):
        return self._set_prop('email_prim', val)

    def get_email_home (self):
        return self._get_prop('email_home')

    def set_email_home (self, val):
        return self._set_prop('email_home', val)

    def add_email_home (self, val):
        return self._append_to_prop('email_home', val)

    def get_email_work (self):
        return self._get_prop('email_work')

    def set_email_work (self, val):
        return self._set_prop('email_work', val)

    def add_email_work (self, val):
        return self._append_to_prop('email_work', val)

    def get_email_other (self):
        return self._get_prop('email_other')

    def set_email_other (self, val):
        return self._set_prop('email_other', val)

    def add_email_other (self, val):
        return self._append_to_prop('email_other', val)

    ## Note that all phone values are (label, number-as-string) tuples.

    def get_phone_home (self):
        return self._get_prop('phone_home')

    def set_phone_home (self, val):
        return self._set_prop('phone_home', val)

    def add_phone_home (self, val):
        return self._append_to_prop('phone_home', val)

    def get_phone_work (self):
        return self._get_prop('phone_work')

    def set_phone_work (self, val):
        return self._set_prop('phone_work', val)

    def add_phone_work (self, val):
        return self._append_to_prop('phone_work', val)

    def get_phone_mob (self):
        return self._get_prop('phone_mob')

    def set_phone_mob (self, val):
        return self._set_prop('phone_mob', val)

    def add_phone_mob (self, val):
        return self._append_to_prop('phone_mob', val)

    def get_phone_other (self):
        return self._get_prop('phone_other')

    def set_phone_other (self, val):
        return self._set_prop('phone_other', val)

    def add_phone_other (self, val):
        return self._append_to_prop('phone_other', val)

    ## FIXME: Not really sure if this way of handling the primary phone will
    ## really cut it. Need to focus some testing on this.

    def get_phone_prim (self):
        return self._get_prop('phone_prim')

    def set_phone_prim (self, val):
        return self._set_prop('phone_prim', val)

    def get_fax_home (self):
        return self._get_prop('fax_home')

    def set_fax_home (self, val):
        return self._set_prop('fax_home', val)

    def add_fax_home (self, val):
        return self._append_to_prop('fax_home', val)

    def get_fax_work (self):
        return self._get_prop('fax_work')

    def set_fax_work (self, val):
        return self._set_prop('fax_work', val)

    def add_fax_work (self, val):
        return self._append_to_prop('fax_work', val)

    ## FIXME: Do something about the fax_prim field and how to manage that.

    def get_fax_prim (self):
        return self._get_prop('fax_prim')

    def set_fax_prim (self, val):
        return self._set_prop('fax_prim', val)

    def get_im_prim (self):
        return self._get_prop('im_prim')

    def set_im_prim (self, val):
        return self._set_prop('im_prim', val)

    def get_im (self, which=None):
        all_ims = self._get_prop('im')

        if which and which in all_ims:
            return all_ims[which]
        else:
            return all_ims

    def set_im (self, val):
        return self._set_prop('im', val)

    def add_im (self, which, val):
        return self._update_prop('im', which, val)

    def get_custom (self, which=None):
        custs = self._get_prop('custom')
        if which:
           if which in custs:
               return custs[which]
           else:
               return None
        else:
            return custs

    def set_custom (self, val):
        return self._set_prop('custom', val)

    def add_custom (self, which, val):
        return self._update_prop('custom', which, val)

    def update_custom (self, d):
        return self._update_prop('custom', None, None, d)

## FIXME: This file needs extensive unit testing. There's quite a bit of
## pseudo-repititive codet hat has been produced by manual cop-n-paste, which
## is a certain recipe for silly typo errors that will not get flagged until
## run time...
