##
## Created       : Wed Apr 03 19:02:15 IST 2013
## Last Modified : Thu Apr 04 15:40:58 IST 2013
##
## Copyright (C) 2013 Sriram Karra <karra.etc@gmail.com>
##
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero General Public License as published by the
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
## This file defines a wrapper class around a CardDAV contact entry. In other
## words this file wraps a vCard object.
##

from   contact    import Contact

class CDContact(Contact):
    def __init__ (self, folder, con=None, vco=None, itemid=None):
        """vco, if not None, should be a valid vCard object (i.e. the contents
        of a vCard file, for e.g. When vco is not None, itemid should also be
        not None"""

        Contact.__init__(self, folder, con)

        conf = self.get_config()
        if con:
            ## FIXME: Reproduce the logic from other contact_* files for this case
            pass

        self.set_vco(vco)
        if vco:
            self.init_props_from_vco(vco)
            assert(itemid)
            self.set_itemid(itemid)

    ##
    ## First the inherited abstract methods from the base classes
    ##

    def save (self):
        """Saves the current contact on the server."""
        pass

    ##
    ## Now onto the non-abstract methods.
    ##

    ## First the get/set methods
    
    def get_vco (self, refresh=False):
        vco = self._get_att('vco')
        if vco and (not refresh):
            return vco

        return self.init_vco_from_props()

    def set_vco (self, vco):
        return self._set_att('vco', vco)

    ## The Rest...

    def init_props_from_vco (self, vco):
        self._snarf_names_gender_from_vco(vco)

    def _snarf_names_gender_from_vco (self, vco):
        if not vco:
            return

        if vco.n and vco.n.value:
            if vco.n.value.given:
                self.set_firstname(vco.n.value.given)

            if vco.n.value.family:
                self.set_lastname(vco.n.value.family)

            if vco.n.value.additional:
                self.set_middlename(vco.n.value.additional)

            if vco.n.value.prefix:
                self.set_prefix(vco.n.value.prefix)

            if vco.n.value.suffix:
                self.set_suffix(vco.n.value.suffix)

        ## FIXME: Need to handle the formatted name when it is present. There
        ## are known cases when the formatted name is different from the
        ## Last/First - for e.g. in apple addressbook, the FN is the orgname
        ## if the user has checked the 'company' box. So I guess the right way
        ## to handle the formatted name business is to faithfully copy
        ## whatever is there.

        ## FIXME: vCard3.0 does not really support standard gender
        ## fields... This is going to be a perennial problem.
