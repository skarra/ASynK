##
## Created : Tue Mar 13 14:26:01 IST 2012
##
## Copyright (C) 2012, 2013 Sriram Karra <karra.etc@gmail.com>
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
## This file defines an abstract base Contact class essentially as a way of
## documenting what this application considers as a normalized contact
## container. The "Copy Constructor" of this class will be the bridge across
## contact entries from different databases.
##

from abc     import ABCMeta, abstractmethod
from pimdb   import PIMDB
from item    import Item

import copy, logging, re, string

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
                           'postal_prim_label' : None,
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
            getattr(self, set_method)(val)

    def get_firstname (self):
        return self._get_prop('firstname')

    def set_firstname (self, val):
        if not self.in_init():
            self.dirty(True)

        self._set_prop('firstname', string.strip(val) if val else None)

    def get_lastname (self):
        return self._get_prop('lastname')

    def set_lastname (self, val):
        if not self.in_init():
            self.dirty(True)

        self._set_prop('lastname', string.strip(val) if val else None)

    def get_middlename (self):
        return self._get_prop('middlename')

    def set_middlename (self, val):
        if not self.in_init():
            self.dirty(True)

        self._set_prop('middlename', val)

    def update_fullname (self):
        if not self.in_init():
            self.dirty(True)

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
        if not self.in_init():
            self.dirty(True)

        self._set_prop('name', val)
        return val

    def get_disp_name (self):
        """In many cases we just want some name to be displayed - in debug
        messages, etc. which has to be built from a number of fields. This
        routine does that."""

        return ' '.join([x.strip() for x in [self.get_firstname(),
                                             self.get_middlename(),
                                             self.get_lastname()] if x])

    def get_prefix (self):
        return self._get_prop('prefix')

    def set_prefix (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('prefix', val)

    def get_suffix (self):
        return self._get_prop('suffix')

    def set_suffix (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('suffix', val)

    def get_fileas (self):
        return self._get_prop('fileas')

    def set_fileas (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('fileas', val)

    def get_gender (self):
        return self._get_prop('gender')

    def set_gender (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('gender', val)

    def get_nickname (self):
        return self._get_prop('nickname')

    def set_nickname (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('nickname', val)

    def get_birthday (self):
        return self._get_prop('birthday')

    def set_birthday (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('birthday', val)

    def get_anniv (self):
        return self._get_prop('anniv')

    def set_anniv (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('anniv', val)

    def get_web_prim (self):
        return self._get_prop('web_prim')

    def set_web_prim (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('web_prim', val)

    def get_web_home (self):
        return self._get_prop('web_home')

    def set_web_home (self, val):
        if not self.in_init():
            self.dirty(True)

        if not self.in_init():
            self.dirty(True)

        return self._set_prop('web_home', val)

    def add_web_home (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._append_to_prop('web_home', val)

    def get_web_work (self):
        return self._get_prop('web_work')

    def set_web_work (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('web_work', val)

    def add_web_work (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._append_to_prop('web_work', val)

    def get_company (self):
        return self._get_prop('company')

    def set_company (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('company', val)

    def get_title (self):
        return self._get_prop('title')

    def set_title (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('title', val)

    def get_dept (self):
        return self._get_prop('dept')

    def set_dept (self, val):
        if not self.in_init():
            self.dirty(True)

        if val:
            return self._set_prop('dept', val)

    ## The postal property has the structure. It is uesful to keep this in
    ## mind when operating it. The set operations will only take a label, and
    ## will slot them into the right place based on the postal_map
    ## configuration variable. Following things to be noted:
    ##
    ## - labels need not be unique even within a category.
    ## 
    ## - the primary flag is set on the basis of label, therefore it is
    ##   sometimes not possibel to correctly identify the address element that
    ##   is primary... such is life.
    ##
    ## postal : {
    ##     "home" : [
    ##         ("label_1", {
    ##           "street"  : "street name",
    ##           "city"    : "city name",
    ##           "country' : "country name",
    ##           ## and so on
    ##           }),
    ##
    ##         ("label_2",  {
    ##             ....
    ##         }),
    ##     ]},
    ## 
    ##     "work" : [
    ##         ("label_1", {
    ##             ....
    ##           }),
    ##
    ##         ("label_2", {
    ##             ....
    ##         }),
    ##      ]},
    ##
    ##     "other" : [
    ##         ("label_1", {
    ##             ....
    ##           }),
    ##
    ##         ("label_2", {
    ##             ....
    ##         }),
    ##      ]},
    ## }
    
    def get_postal (self, type=None, as_array=False):
        """Return the full list of the specified type (home, work, other,
        etc.). If type is None, return the whole damn thing).

        if type is None, then the return value can be either a flattened
        out array of tuples, or a categorized dictionary depending of the
        as_array flag, which defaults to False

        If there is no postals of specified type, then None is returned."""

        postals = self._get_prop('postal')
        if not type:
            if not as_array:
                return postals
            ret = []
            for cat, ary in postals.iteritems():
                ret += ary

            ## Now, we need to ensure the primary address is the first element
            ## in the array. So we're not quite done yet.
            index = -1
            for  i, (label, val) in enumerate(ret):
                if self.is_postal_prim(label):
                    index = i
                    prim  = (label, val)
                    break

            if index != -1:
                ret.pop(index)
                ret.insert(0, prim)          
                
            return ret

        return postals[type] if type in postals else None

    def set_postal (self, val, type=None):
        """val should be a dictionary of label : address mappings. Note that
        address itself is a dictionary. Oh, lord, this is getting too funny."""

        if not self.in_init():
            self.dirty(True)

        if type:
            return self._update_prop('postal', type, val)
        else:
            return self._set_prop('postal', val)

    def add_postal (self, which, val):
        postal_map = self.get_postal_map()

        type = 'home'
        if postal_map and len(postal_map) > 0:
            for cat, reg in postal_map.iteritems():
                if re.search(reg, which):
                    type = cat
                    break

        addrs = self.get_postal(type)
        if addrs:
            addrs.append((which, val))
            if not self.in_init():
                self.dirty(True)
        else:
            self.set_postal([(which, val)], type)

    def set_postal_prim_label (self, label):
        return self._set_prop('postal_prim_label', label)

    def get_postal_prim_label (self):
        return self._get_prop('postal_prim_label')

    def is_postal_prim (self, label):
        """Returns True if the provided label corresponds to the primary
        address entry, and False otherwise."""

        return self.get_postal_prim_label() == label

    def get_notes (self):
        return self._get_prop('notes')

    def set_notes (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('notes', val)

    def add_notes (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._append_to_prop('notes', val)

    def get_email_prim (self):
        return self._get_prop('email_prim')

    def set_email_prim (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('email_prim', val)

    def get_email_home (self):
        return self._get_prop('email_home')

    def set_email_home (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('email_home', val)

    def add_email_home (self, val):
        return self._append_to_prop('email_home', val)

    def get_email_work (self):
        return self._get_prop('email_work')

    def set_email_work (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('email_work', val)

    def add_email_work (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._append_to_prop('email_work', val)

    def get_email_other (self):
        return self._get_prop('email_other')

    def set_email_other (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('email_other', val)

    def add_email_other (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._append_to_prop('email_other', val)

    ## Note that all phone values are (label, number-as-string) tuples.

    def get_phone_home (self):
        return self._get_prop('phone_home')

    def set_phone_home (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('phone_home', val)

    def add_phone_home (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._append_to_prop('phone_home', val)

    def get_phone_work (self):
        return self._get_prop('phone_work')

    def set_phone_work (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('phone_work', val)

    def add_phone_work (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._append_to_prop('phone_work', val)

    def get_phone_mob (self):
        return self._get_prop('phone_mob')

    def set_phone_mob (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('phone_mob', val)

    def add_phone_mob (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._append_to_prop('phone_mob', val)

    def get_phone_other (self):
        return self._get_prop('phone_other')

    def set_phone_other (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('phone_other', val)

    def add_phone_other (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._append_to_prop('phone_other', val)

    ## FIXME: Not really sure if this way of handling the primary phone will
    ## really cut it. Need to focus some testing on this.

    def get_phone_prim (self):
        return self._get_prop('phone_prim')

    def set_phone_prim (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('phone_prim', val)

    def get_fax_home (self):
        return self._get_prop('fax_home')

    def set_fax_home (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('fax_home', val)

    def add_fax_home (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._append_to_prop('fax_home', val)

    def get_fax_work (self):
        return self._get_prop('fax_work')

    def set_fax_work (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('fax_work', val)

    def add_fax_work (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._append_to_prop('fax_work', val)

    ## FIXME: Do something about the fax_prim field and how to manage that.

    def get_fax_prim (self):
        return self._get_prop('fax_prim')

    def set_fax_prim (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('fax_prim', val)

    def get_im_prim (self):
        return self._get_prop('im_prim')

    def set_im_prim (self, val):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('im_prim', val)

    def get_im (self, which=None):
        all_ims = self._get_prop('im')

        if which and which in all_ims:
            return all_ims[which]
        else:
            return all_ims

    def set_im (self, val):
        if not self.in_init():
            self.dirty(True)

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
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('custom', val)

    def add_custom (self, which, val):
        if not self.in_init():
            self.dirty(True)

        return self._update_prop('custom', which, val)

    def update_custom (self, d):
        if not self.in_init():
            self.dirty(True)

        return self._update_prop('custom', None, None, d)

    def del_custom (self, which):
        """Delete a custom property and return True if property actually
        exists. Returns False if property is not in custom list of contact"""

        if not self.in_init():
            self.dirty(True)

        if which in self._get_prop('custom'):
            del self._get_prop('custom')[which]
            return True

        return False

## FIXME: This file needs extensive unit testing. There's quite a bit of
## pseudo-repititive codet hat has been produced by manual cop-n-paste, which
## is a certain recipe for silly typo errors that will not get flagged until
## run time...
