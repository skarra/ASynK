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
## This file defines an abstract base Item class. Contact, Task, Appointment
## and Note can / will be derived from this base class and will reside in
## their own files.
##

import datetime, logging, re

from abc     import ABCMeta, abstractmethod
from pimdb   import PIMDB, GoutInvalidPropValueError
from folder  import Folder

class Item:
    """A generic PIM item - can be a Contact, Task, Note, or Appointment.

    Items have two types of properties: props and atts - props are properties
    of a contact that are made persistent in a PIM Database. Examples are:
    name, phone numbers, email addresses, etc. atts are attributes of the
    class or object thare are needed for the code to work, and are not stored
    to the database. Examples of such attributes include a reference to the
    enclosing folder object, PIMDB session, config and application state
    values, etc.

    It is important to keep this difference in mind, and there are different
    accessors for properties and attributes.
    """

    __metaclass__ = ABCMeta

    valid_types   = [Folder.CONTACT_t, Folder.NOTE_t, Folder.TASK_t,
                     Folder.APPT_t]

    def __init__ (self, folder):
        # Items have properties that need to persist in the underlying
        # database. We call them 'props'. These are defined and tracked in a
        # single dictionary. Each of the derived classes will, of course, add
        # to this stuff.
        self.props = {'created'    : None,
                      'updated'    : None,
                      'sync_tags'  : {},
                      }

        # Attributes are non-persistent properties of the class or object,
        # such as references to the enclosing folder, PIMDB, etc.
        self.atts  = {'config'     : None,
                      'db'         : None,
                      'folder'     : None,
                      'itemid'     : None,
                      'type'       : None,
                      }

        self.in_init(True)
        self.dirty(False)

        # Then there are many class attributes that are needed to work with
        # the programatically in the application, like pointers to the parent
        # Folder and DB object, etc. Such attributes are tracked separately
        # like any other object attributes

        self.set_folder(folder)
        self.set_db(folder.get_db() if folder else None)
        self.set_dbid(folder.get_dbid() if folder else None)
        self.set_config(folder.get_config() if folder else None)

    ##
    ## First the abstract methods
    ##

    @abstractmethod
    def save (self):
        """Make this item persistent in the underlying database. On success
        this method should set the itemid field if it has changed, and return
        the new value. On failure None is returned."""

        raise NotImplementedError

    ##
    ## Now the internal helper methods that will be used in the internal
    ## implementetion of the class methods.
    ##

    def _get_prop (self, key):
        return self.props[key]

    def _set_prop (self, key, val):
        self.props.update({key : val})
        return val

    def _append_to_prop (self, key, val):
        """In the particular property value is an array, we would like to
        append individual elements to the property value. this method does
        exactly that."""

        if not self.props[key]:
            self.props[key] = [val]
        else:
            self.props[key].append(val)

    def _update_prop (self, prop, which, val, d=None):
        """If a particular property value is a dictionary, we would like to
        update the dictinary with a new mapping or alter an existing
        mapping. This method does exactly that. Alternately we can just pass
        in a whole dictionary to update."""

        if not self.props[prop]:
            if d:
                self.props[prop] = d
            else:
                self.props[prop] = {which : val}
        else:
            if d:
                self.props[prop].update(d)
            else:
                self.props[prop].update({which : val})

    def _del_prop (self, key, which):
        """In case the avalue of the specified attribute is a dictionary, this
        routine can be used to delete an entry in the attribute's value."""

        del self.props[key][which]

    def _get_att (self, key):
        return self.atts[key]

    def _set_att (self, key, val):
        self.atts.update({key : val})
        return val

    def _del_att (self, key, which):
        """In case the avalue of the specified attribute is a dictionary, this
        routine can be used to delete an entry in the attribute's value."""

        del self.atts[key][which]

    def _append_to_att (self, key, val):
        """In the particular atterty value is an array, we would like to
        append individual elements to the attribute value. this method does
        exactly that."""

        if not self.atts[key]:
            self.atts[key] = [val]
        else:
            self.atts[key].append(val)

    def _update_att (self, att, which, val):
        """If a particular attributes value is a dictionary, we would like to
        update the dictionary with a new mapping or alter an existing
        mapping. This method does exactly that."""

        if not self.atts[att]:
            self.atts[att] = {which : val}
        else:
            self.atts[att].update({which : val})

    ##
    ## Finally, the get_ and set_ methods.
    ##

    def get_prop_names (self):
        return self.props.keys()

    def get_att_names (self):
        return self.atts.keys()

    ## First the object attributes

    def dirty (self, val=None):
        if val is None:
            return self._get_att('dirty')

        return self._set_att('dirty', val)

    def in_init (self, val=None):
        if val is None:
            return self._get_att('in_init')

        return self._set_att('in_init', val)

    def get_folder (self):
        return self._get_att('folder')

    def set_folder (self, val):
        return self._set_att('folder', val)

    def get_store (self):
        return self.get_folder().get_store()

    def get_db (self):
        return self._get_att('db')

    def set_db (self, val):
        return self._set_att('db', val)

    def get_config (self):
        return self._get_att('config')

    def set_config (self, config):
        return self._set_att('config', config)

    def get_itemid (self):
        return self._get_att('itemid')

    def set_itemid (self, val):
        self._set_att('itemid', val)

    ## Now, the item properties

    def get_dbid (self):
        return self.dbid

    def set_dbid (self, val):
        if not self.in_init():
            self.dirty(True)

        self.dbid = val

    def get_created (self, iso=False):
        val = self._get_prop('created')
        if type(val) == datetime.datetime and iso:
            return val.isoformat()
        else:
            return val

    def set_created (self, c):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('created', c)

    def get_updated (self, iso=False):
        val = self._get_prop('updated')
        if type(val) == datetime.datetime and iso:
            return val.isoformat()
        else:
            return val

    def set_updated (self, u):
        if not self.in_init():
            self.dirty(True)

        return self._set_prop('updated', u)

    def get_type (self):
        return self._get_att('type')

    def set_type (self, val):
        if not self.in_init():
            self.dirty(True)

        if not val in self.valid_types:
            raise GoutInvalidPropValueError('Invalid type: %s' % val)

        self._set_att('type', val)

    def get_email_domains (self):
        return self.get_db().get_email_domains()

    def get_postal_map (self):
        return self.get_db().get_postal_map()

    def get_notes_map (self):
        return self.get_db().get_notes_map()

    def get_phones_map (self):
        return self.get_db().get_phones_map()

    def get_sync_tags (self, label=None):
        """Return the sync tag corresponding to specified DBID: label. If
        label is None, the full dictionary of sync tags is returned to the
        uesr. label can also be a regular expression, in which case all sync
        tags matching the regular expression are returned as an array of (tag,
        value) tuples"""

        tags = self._get_prop('sync_tags')
        try:
            return [(label, tags[label])] if label else tags
        except KeyError, e:
            ## Could not make an exact match, now let's attempt a regexp
            ## match... 
            pass

        ret = []
        for key, val in tags.iteritems():
            if re.search(label, key):
                ret.append((key, val))

        return ret

    def set_sync_tags (self, val, save=False):
        """While this is not anticipated to be used much, this routine gives
        the flexibility to set the entire sync_tags dictionary
        wholesale. Potential use cases include clearing all existing values,
        etc."""

        if not self.in_init():
            self.dirty(True)

        self._set_prop('sync_tags', val)
        if save:
            self.save()

    def update_sync_tags (self, destid, val, save=False):
        """Update the specified sync tag with given value. If the tag does not
        already exist an entry is created."""

        if not self.in_init():
            self.dirty(True)

        self._update_prop('sync_tags', destid, val)
        if save:
            self.save()

    def del_sync_tags (self, label_re):
        """Remove the sync_tag from the current item if the label matches
        specified regular expression: label_re.

        This method returns True if any property was actually removed, and
        False if label_re did not match any sync_tag."""

        if not self.in_init():
            self.dirty(True)

        dels = []

        for pair in self.get_sync_tags(label_re):
            tag, val = pair
            dels.append(tag)

        arr = [self._del_prop('sync_tags', t) for t in dels]

        return len(arr) > 0

    def get_itemid_from_synctags (self, pname, dbid):
        """Look in the synctags list to see if there is an itemid already for
        the given profile and dbid combo. This is needed  when this item has
        been fetched from a remote db and has already been synched to the
        destination earlier. """

        conf  = self.get_config()
        label = conf.make_sync_label(pname, dbid)
        try:
            tag, itemid = self.get_sync_tags(label)[0]
            return itemid
        except IndexError, e:
            return None

    def __str__ (self):
        ret = '\n%18s: %s\n' % ('itemid', self.get_itemid())
        props = self.get_prop_names()
        for prop in props:
            ret += '%18s: %s\n' % (prop, self._get_prop(prop))

        return ret

## FIXME: This file needs extensive unit testing
