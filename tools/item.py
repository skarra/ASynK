##
## Created	     : Tue Mar 13 14:26:01 IST 2012
## Last Modified : Mon Apr 09 11:25:13 IST 2012
##
## Copyright (C) 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
##
## This file defines an abstract base Item class. Contact, Task, Appointment
## and Note can / will be derived from this base class and will reside in
## their own files.
##

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
                      'modified'   : None,
                      }

        # Attributes are non-persistent properties of the class or object,
        # such as references to the enclosing folder, PIMDB, etc.
        self.atts  = {'config'     : None,
                      'db'         : None,
                      'folder'     : None,
                      'itemid'     : None,
                      'type'       : None,
                      'sync_tags'  : {},
                      }

        # Then there are many class attributes that are needed to work with
        # the programatically in the application, like pointers to the parent
        # Folder and DB object, etc. Such attributes are tracked separately
        # like any other object attributes

        self.set_folder(folder)
        self.set_db(folder.get_db())
        self.set_dbid(folder.get_dbid())
        self.set_config(folder.get_config())

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

    def _update_prop (self, prop, which, val):
        """If a particular property value is a dictionary, we would like to
        update the dictinary with a new mapping or alter an existing
        mapping. This method does exactly that."""

        if not self.props[prop]:
            self.props[prop] = {which : val}
        else:
            self.props[prop].update({which : val})

    def _get_att (self, key):
        return self.atts[key]

    def _set_att (self, key, val):
        self.atts.update({key : val})
        return val

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

    def get_folder (self):
        return self._get_att('folder')

    def set_folder (self, val):
        return self._set_att('folder', val)

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
        self.dbid = val

    def get_created (self):
        return self._get_prop('created')

    def set_created (self, c):
        return self._set_prop('created', c)

    def get_updated (self):
        return self._get_prop('updated')

    def set_updated (self, u):
        return self._set_prop('updated', u)

    def get_type (self):
        return self._get_att('type')

    def set_type (self, val):
        if not val in self.valid_types:
            raise GoutInvalidPropValueError('Invalid type: %s' % val)

        self._set_att('type', val)

    def get_email_domains (self):
        return self.get_db().get_email_domains()

    def get_notes_map (self):
        return self.get_db().get_notes_map()

    def get_phones_map (self):
        return self.get_db().get_phones_map()

    def get_sync_tags (self, destid=None):
        """Return the sync tag corresponding to specified DBID: destid. If
        destid is None, the full dictionary of sync tags is returned to the
        uesr."""

        tags = self._get_att('sync_tags')
        return tags[destid] if destid else tags

    def set_sync_tags (self, val, save=False):
        """While this is not anticipated to be used much, this routine gives
        the flexibility to set the entire sync_tags dictionary
        wholesale. Potential use cases include clearing all existing values,
        etc."""

        self._set_att('sync_tags', val)
        if save:
            self.save()

    def update_sync_tags (self, destid, val, save=False):
        """Update the specified sync tag with given value. If the tag does not
        already exist an entry is created."""

        self._update_att('sync_tags', destid, val)
        if save:
            self.save()

    def __str__ (self):
        ret = ''

        props = self.get_prop_names()
        for prop in props:
            ret += '%18s: %s\n' % (prop, self._get_prop(prop))

        return ret

## FIXME: This file needs extensive unit testing
