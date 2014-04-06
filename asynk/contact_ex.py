##
## Created : Wed Apr 02 11:31:26 IST 2014
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
## ####
##
## This file extends the Contact base class to implement an Exchange Contact
## item while implementing the base class methods.
##

from   contact    import Contact
import utils

class EXContactError(Exception):
    pass

class EXContact(Contact):
    prop_update_t = utils.enum('PROP_REPLACE', 'PROP_APPEND')

    def __init__ (self, folder, ews_con=None, con=None):
        """Constructor for EXContact. The starting properties of the contact
        can be initialized either from an existing Contact object, or from an
        pyews contact object. It is an error to provide both.
        """

        if (ews_con and con):
            raise EXContactError(
                'Both ews con and con cannot be specified in EXContact()')

        Contact.__init__(self, folder, con)

        ## Sometimes we might be creating a contact object from a remote
        ## source which might have the Entry ID in its sync tags field. if
        ## that is present, we should use it to initialize the itemid field
        ## for the current object

        conf = self.get_config()
        if con:
            try:
                pname_re = conf.get_profile_name_re()
                label    = conf.make_sync_label(pname_re, self.get_dbid())
                tag, itemid = con.get_sync_tags(label)[0]              
                self.set_itemid(itemid)
            except Exception, e:
                logging.debug('Potential new EXContact: %s', con.get_name())

        if ews_con is not None:
            self._init_props_from_ews_con(ews_con)

    ##
    ## First the inherited abstract methods from the base classes
    ##

    def save (self):
        pass

    ##
    ## Now onto the non-abstract methods.
    ##

    def get_parent_folder_id (self):
        """Fetch and return the itemid of the parent folder of this contact in
        the Exchange store. This will be none if this is a new contact that
        has not yet be written to the server"""

        try:
            return self._get_att('parentid')
        except Exception, e:
            return None

    def set_parent_folder_id (self, pfid):
        return self._set_att('parentid', pfid)
        
    ##
    ## And now, the internal methods
    ##

    def _init_props_from_ews_con (self, ews_con):
        self.set_parent_folder_id(ews_con.ParentFolderId)

    ##
    ## some additional get and set methods
    ##
