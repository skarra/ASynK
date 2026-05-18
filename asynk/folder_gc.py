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
## ####
##
## Google Contacts Folder implementation using the People API v1.
## Replaces the old GData/Atom-based implementation.
##

import copy, logging, re

from folder import Folder

from contact_gc import GCContact

import utils

## personFields to request when listing connections. Must match the
## definition in pimdb_gc.py.
PERSON_FIELDS = ','.join([
    'names', 'nicknames', 'emailAddresses', 'phoneNumbers', 'addresses',
    'organizations', 'birthdays', 'events', 'urls', 'imClients',
    'biographies', 'memberships', 'userDefined', 'photos', 'genders',
    'metadata',
])

## ---------------------------------------------------------------------------
## Helpers
## ---------------------------------------------------------------------------

def get_udp_by_key (udps, key):
    """Get the value of the first userDefined property with the specified key.

    udps is a list of dicts like [{"key": "...", "value": "..."}].
    """
    if not udps:
        return None

    for ep in udps:
        if ep.get('key') == key:
            return ep.get('value')

    return None

def get_udps_by_key_prefix (udps, keyprefix):
    """Get a dict of all userDefined properties whose keys match the given
    prefix."""

    ret = {}
    if not udps:
        return ret

    for ep in udps:
        k = ep.get('key', '')
        if k.startswith(keyprefix):
            v = ep.get('value')
            if v:
                ret[k] = v

    return ret

SYNC_OK                    = 200
SYNC_CREATED               = 201
SYNC_NOT_MODIFIED          = 304
SYNC_BAD_REQUEST           = 400
SYNC_UNAUTHORIZED          = 401
SYNC_FORBIDDEN             = 403
SYNC_CONFLICT              = 409
SYNC_INTERNAL_SERVER_ERROR = 500

## ---------------------------------------------------------------------------
## GCContactsFolder
## ---------------------------------------------------------------------------

class GCContactsFolder(Folder):
    """A class that wraps a Google Contacts folder (contact group) using
    the People API v1."""

    BATCH_SIZE = 200   # People API allows up to 200 per batch

    def __init__ (self, db, gid, gn, gcentry):
        Folder.__init__(self, db)

        self.set_itemid(gid)
        self.set_name(gn)
        self.set_gcentry(gcentry)
        self.set_type(Folder.CONTACT_t)
        self.set_service(db.get_service())

        self.reset_contacts()

    ##
    ## Implementation of the abstract methods inherited from Folder
    ##

    def get_batch_size (self):
        return self.BATCH_SIZE

    def prep_sync_lists (self, destid, sl, updated_min=None, cnt=0):
        """See the documentation in folder.Folder"""

        pname = sl.get_pname()
        conf  = self.get_config()
        pdb1id = conf.get_profile_db1(pname)
        oldi  = conf.get_itemids(pname)
        newi  = self.get_itemids(pname, destid)

        kss = list(newi.keys())
        for x, y in oldi.items():
            if not x in kss and not y in kss:
                logging.debug('Del      Google Contact: %s:%s', x, y)
                if pdb1id == self.get_dbid():
                    sl.add_del(x, y)
                else:
                    sl.add_del(y, x)

        logging.info('Querying Google for status of Contact Entries...')
        stag = conf.make_sync_label(pname, destid)

        if not updated_min:
            updated_min = conf.get_last_sync_stop(pname)

        persons = self._get_group_contacts(updated_min=updated_min)

        logging.info('Response received from Google. Processing...')

        if not persons:
            logging.info('No entries in response.')
            for x in kss:
                sl.add_unmod(x)
            return

        skip     = 0
        etag_cnt = 0

        for i, person in enumerate(persons):
            gcid = person.get('resourceName', '')
            olid = get_udp_by_key(person.get('userDefined'), stag)
            etag = person.get('etag')

            ## Check if the contact was deleted
            deleted = person.get('metadata', {}).get('deleted', False)

            ## Extract a display name for logging
            name = None
            names = person.get('names', [])
            if names:
                n = names[0]
                name = (n.get('displayName') or n.get('familyName')
                        or n.get('givenName'))

            if deleted:
                if olid:
                    pass
                    # We will trust our own delete logic...
                else:
                    skip += 1
                    continue
            else:
                if olid:
                    update_time = None
                    for src in person.get('metadata', {}).get('sources', []):
                        ut = src.get('updateTime')
                        if ut:
                            if not update_time or ut > update_time:
                                update_time = ut

                    is_modified = True
                    if update_time and updated_min:
                        try:
                            import datetime
                            from dateutil.parser import isoparse
                            ut_dt = isoparse(update_time)
                            um_dt = isoparse(updated_min)
                            # Allow a 5-second clock skew tolerance
                            if ut_dt <= um_dt + datetime.timedelta(seconds=5):
                                is_modified = False
                        except Exception as e:
                            logging.warning('Could not parse timestamps: %s', e)
                            if update_time <= updated_min:
                                is_modified = False

                    if not is_modified:
                        pass
                    else:
                        logging.debug('Modified Google Contact: %20s %s',
                                      name, gcid)
                        sl.add_mod(gcid, olid)
                else:
                    logging.debug('New      Google Contact: %20s %s',
                                  name, gcid)
                    sl.add_new(gcid)

            if etag:
                sl.add_etag(gcid, etag)
                etag_cnt += 1
            else:
                sl.add_entry(gcid)

        for x in kss:
            if not x in sl.get_news() and not x in sl.get_mods():
                sl.add_unmod(x)

        logging.debug('Total Contacts   : %5d', len(newi))
        logging.debug('num with etags   : %5d', etag_cnt)
        logging.debug('num del bef sync : %5d', skip)

    def get_itemids (self, pname, destid):
        self._refresh_contacts()
        ret = {}
        stag = self.get_config().make_sync_label(pname, destid)
        for locid, con in self.get_contacts().items():
            if stag in con.get_sync_tags():
                t, remid = con.get_sync_tags(stag)[0]
                ret[locid] = remid

        return ret

    def find_item (self, itemid):
        """Fetch a single contact by resourceName and return a GCContact."""
        svc = self.get_service()
        person = svc.people().get(
            resourceName=itemid,
            personFields=PERSON_FIELDS).execute()
        gc = GCContact(self, person=person)
        return gc

    def find_items (self, itemids):
        """Fetch multiple contacts by resourceName. Returns a list of
        GCContact objects.  itemids can be a list of resource names or a
        dict whose keys are resource names (as returned by get_mods)."""

        if isinstance(itemids, dict):
            itemids = list(itemids.keys())

        ret = []
        svc = self.get_service()

        ## People API getBatchGet supports up to 200 resource names
        for i in range(0, len(itemids), self.BATCH_SIZE):
            batch = itemids[i:i + self.BATCH_SIZE]
            resp = svc.people().getBatchGet(
                resourceNames=batch,
                personFields=PERSON_FIELDS).execute()

            for pr in resp.get('responses', []):
                person = pr.get('person')
                if person:
                    ret.append(GCContact(self, person=person))

        return ret

    def batch_create (self, src_sl, src_dbid, items):
        """See the documentation in folder.Folder"""

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = src_sl.get_pname()

        src_sync_tag = c.make_sync_label(pname, src_dbid)
        dst_sync_tag = c.make_sync_label(pname, my_dbid)

        svc     = self.get_service()
        success = True

        ## Build contacts in batches of BATCH_SIZE
        for i in range(0, len(items), self.BATCH_SIZE):
            batch_items = items[i:i + self.BATCH_SIZE]
            contacts = []
            bid_map = {}   # index → (bid, orig_item)

            for j, item in enumerate(batch_items):
                con_itemid = item.get_itemid_from_synctags(pname, 'gc')
                gc  = GCContact(self, con=item, con_itemid=con_itemid)
                bid = item.get_itemid()
                gc.update_sync_tags(src_sync_tag, bid)

                person_body = gc.init_person_from_props()
                contacts.append({'contactPerson': person_body})
                bid_map[j] = (bid, gc, item)

            batch_num = (i // self.BATCH_SIZE) + 1
            logging.debug('Uploading new batch #%02d to Google. Count: %d',
                          batch_num, len(contacts))

            try:
                resp = svc.people().batchCreateContacts(
                    body={'contacts': contacts,
                          'readMask': PERSON_FIELDS}).execute()

                for j, cp in enumerate(resp.get('createdPeople', [])):
                    person = cp.get('person', {})
                    gcid = person.get('resourceName', '')
                    bid, gc, orig = bid_map[j]
                    orig.update_sync_tags(dst_sync_tag, gcid)
                    logging.info('Successfully created gmail entry for %30s (%s)',
                                 gc.get_disp_name(), orig.get_itemid())
            except Exception as e:
                logging.error('Batch create failed: %s', e)
                success = False

        return success

    def batch_update (self, sync_list, src_dbid, items):
        """See the documentation in folder.Folder"""

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = sync_list.get_pname()

        src_sync_tag = c.make_sync_label(pname, src_dbid)
        dst_sync_tag = c.make_sync_label(pname, my_dbid)

        tags  = [item.get_sync_tags(dst_sync_tag)[0] for item in items]
        gcids = [val for (tag, val) in tags]

        ## Fetch current persons to get fresh etags
        logging.debug('Refreshing etags for modified entries...')
        current_persons = self._fetch_persons(gcids)
        etag_map = {p['resourceName']: p['etag']
                    for p in current_persons if 'etag' in p}

        svc     = self.get_service()
        success = True

        for i in range(0, len(items), self.BATCH_SIZE):
            batch_items = items[i:i + self.BATCH_SIZE]
            update_body = {}

            for item, gcid in zip(batch_items[0:len(batch_items)],
                                  gcids[i:i + self.BATCH_SIZE]):
                con_itemid = item.get_itemid_from_synctags(pname, 'gc')
                gc  = GCContact(self, con=item, con_itemid=con_itemid)
                bid = item.get_itemid()
                gc.update_sync_tags(src_sync_tag, bid)

                person_body = gc.init_person_from_props()
                person_body['resourceName'] = gcid
                person_body['etag'] = etag_map.get(gcid, '')

                update_body[gcid] = person_body

            batch_num = (i // self.BATCH_SIZE) + 1
            logging.debug('Uploading mod batch #%02d to Google. Count: %d',
                          batch_num, len(update_body))

            try:
                from pimdb_gc import UPDATE_PERSON_FIELDS
                resp = svc.people().batchUpdateContacts(
                    body={'contacts': update_body,
                          'readMask': PERSON_FIELDS,
                          'updateMask': UPDATE_PERSON_FIELDS,
                          }).execute()

                for rn, result in resp.get('updateResult', {}).items():
                    person = result.get('person', {})
                    logging.info('Successfully updated gmail entry for %s',
                                 person.get('resourceName', rn))
            except Exception as e:
                logging.error('Batch update failed: %s', e)
                success = False

        return success

    def writeback_sync_tags (self, pname, items):
        """Write back sync tags to Google for the given items."""

        conf  = self.get_config()
        remid = conf.get_other_dbid(pname, self.get_dbid())
        stag  = conf.make_sync_label(pname, remid)

        svc     = self.get_service()
        success = True

        ## Collect resource names to refresh etags
        gcids = []
        for item in items:
            tags = item.get_sync_tags(stag)
            if not tags:
                logging.debug('Null tags. Item: \n%s', item)
                raise Exception('Missing sync tags for writeback')
            t, iid = tags[0]
            gcids.append(item.get_itemid())

        current_persons = self._fetch_persons(gcids)
        etag_map = {p['resourceName']: p['etag']
                    for p in current_persons if 'etag' in p}

        for i in range(0, len(items), self.BATCH_SIZE):
            batch_items = items[i:i + self.BATCH_SIZE]
            update_body = {}

            for item in batch_items:
                gcid = item.get_itemid()
                person_body = item.init_person_from_props()
                person_body['resourceName'] = gcid
                person_body['etag'] = etag_map.get(gcid, '')

                update_body[gcid] = person_body

            batch_num = (i // self.BATCH_SIZE) + 1
            logging.debug('Writeback batch #%02d. Count: %d',
                          batch_num, len(update_body))

            try:
                svc.people().batchUpdateContacts(
                    body={'contacts': update_body,
                          'readMask': 'userDefined',
                          'updateMask': 'userDefined',
                          }).execute()
            except Exception as e:
                logging.error('Writeback batch failed: %s', e)
                success = False

        return success

    def bulk_clear_sync_flags (self, label_re=None):
        """See the documentation in folder.Folder"""

        if not label_re:
            label_re = 'asynk:[a-z][a-z]:id'

        logging.info('Fetching contact entries from Google for folder %s...',
                     self.get_name())

        persons = self._get_group_contacts()
        if not persons:
            return True

        logging.info('Clearing sync state information...')

        mods = {}
        cnt  = 0
        for person in persons:
            udps = person.get('userDefined', [])
            if not udps:
                continue

            new_udps = []
            modified = False
            for ep in udps:
                if re.search(label_re, ep.get('key', '')):
                    logging.debug('  Tag %s match for item %s',
                                  ep.get('key'), person.get('resourceName'))
                    cnt += 1
                    modified = True
                else:
                    new_udps.append(ep)

            if modified:
                rn = person['resourceName']
                person['userDefined'] = new_udps
                mods[rn] = {
                    'person': person,
                    'updatePersonFields': 'userDefined',
                }

        logging.info('Found %d contacts with matching sync tags (%s).',
                     cnt, label_re)

        if not mods:
            return True

        logging.info('Sending modification request to Google...')

        svc = self.get_service()
        success = True
        rn_list = list(mods.keys())

        for i in range(0, len(rn_list), self.BATCH_SIZE):
            batch_rns = rn_list[i:i + self.BATCH_SIZE]
            batch_body = {rn: mods[rn] for rn in batch_rns}

            batch_num = (i // self.BATCH_SIZE) + 1
            logging.debug('Uploading clear batch #%02d. Count: %d',
                          batch_num, len(batch_body))

            try:
                svc.people().batchUpdateContacts(
                    body={'contacts': batch_body,
                          'readMask': 'userDefined',
                          'updateMask': {'paths': ['userDefined']}
                          }).execute()
            except Exception as e:
                logging.error('Clear sync flags batch failed: %s', e)
                success = False

        logging.info('Sending modification request to Google...Done')
        return success

    def _refresh_contacts (self):
        """Reload all contacts in this group from Google."""
        persons = self._get_group_contacts()
        for person in persons:
            gc = GCContact(self, person=person)
            self.add_contact(gc)

    def show (self, what='summary'):
        logging.info(str(self))
        logging.info('Summary of contained Items:')

        self._refresh_contacts()
        for itemid, con in self.get_contacts().items():
            logging.info('  Name: %-25s Itemid: %s', con.get_name(), itemid)

    def __str__ (self):
        ret = 'Contacts'
        return ('%s.\tName: %s;\tGID: %s;\t' % (ret, self.get_name(),
                                                self.get_itemid()))

    ##
    ## Internal and helper routines
    ##

    def is_dirty (self):
        return self._get_prop('dirty')

    def is_clean (self):
        return not self.is_dirty()

    def set_clean (self):
        return self._set_prop('dirty', False)

    def set_dirty (self):
        return self._set_prop('dirty', True)

    def add_contact (self, gcc):
        self.contacts[gcc.get_itemid()] = gcc

    def del_itemids (self, itemids):
        """Delete the specified contacts from Google and from the local
        cache."""

        svc = self.get_service()

        ## People API batchDeleteContacts
        for i in range(0, len(itemids), self.BATCH_SIZE):
            batch = itemids[i:i + self.BATCH_SIZE]
            logging.info('Deleting %d contacts...', len(batch))
            svc.people().batchDeleteContacts(
                body={'resourceNames': batch}).execute()

            for rid in batch:
                try:
                    del self.contacts[rid]
                except KeyError:
                    pass

    def reset_contacts (self):
        self.contacts = {}

    def get_contacts (self):
        return self.contacts

    def get_service (self):
        return self._get_prop('service')

    def set_service (self, service):
        self._set_prop('service', service)

    ## Keep get_gdc/set_gdc as aliases for transition
    def get_gdc (self):
        return self.get_service()

    def set_gdc (self, svc):
        self.set_service(svc)

    def get_gcentry (self):
        return self._get_prop('gcentry')

    def set_gcentry (self, gcentry):
        self._set_prop('gcentry', gcentry)

    def _get_group_contacts (self, updated_min=None):
        """Fetch all contacts that belong to this group from the People API.

        Returns a list of Person resource dicts.
        """

        svc = self.get_service()
        group_resource_name = self.get_itemid()

        all_persons = []
        page_token = None

        while True:
            resp = svc.people().connections().list(
                resourceName='people/me',
                personFields=PERSON_FIELDS,
                pageSize=1000,
                pageToken=page_token,
                requestSyncToken=False,
            ).execute()

            connections = resp.get('connections', [])

            ## Filter to only include contacts in this group
            for person in connections:
                memberships = person.get('memberships', [])
                for m in memberships:
                    cgm = m.get('contactGroupMembership', {})
                    if cgm.get('contactGroupResourceName') == group_resource_name:
                        all_persons.append(person)
                        break

            page_token = resp.get('nextPageToken')
            if not page_token:
                break

        return all_persons

    def _fetch_persons (self, resource_names):
        """Fetch multiple Person resources by resourceName.  Returns a list
        of Person dicts."""

        svc = self.get_service()
        ret = []

        for i in range(0, len(resource_names), self.BATCH_SIZE):
            batch = resource_names[i:i + self.BATCH_SIZE]
            resp = svc.people().getBatchGet(
                resourceNames=batch,
                personFields=PERSON_FIELDS).execute()

            for pr in resp.get('responses', []):
                person = pr.get('person')
                if person:
                    ret.append(person)

        return ret

    def del_all_entries (self):
        """Delete all contacts in this group."""

        persons = self._get_group_contacts()
        if not persons:
            return

        rnames = [p['resourceName'] for p in persons]
        self.del_itemids(rnames)


class BatchState:
    """Compatibility shim — retains the BatchState class name so that any
    code importing it from folder_gc doesn't break.

    In the People API world, batch operations are handled directly by
    batchCreateContacts / batchUpdateContacts / batchDeleteContacts, so
    the old XML-feed-based BatchState logic is no longer needed.  This
    class is kept as a minimal stub.
    """

    def __init__ (self, num, f=None, op=None, sync_tag=None):
        self.num  = num
        self.cnt  = 0
        self.f    = f
        self.operation = op
        self.cons = {}
        self.origs = {}
        self.sync_tag = sync_tag

    def incr_cnt (self):
        self.cnt += 1
        return self.cnt

    def get_cnt (self):
        return self.cnt

    def get_bnum (self):
        return self.num

    def get_size (self):
        return 0

    def add_con (self, key, new, orig=None):
        self.cons[key] = new
        self.origs[key] = orig

    def get_con (self, key):
        return self.cons[key]

    def get_orig (self, key):
        return self.origs[key]

    def get_operation (self):
        return self.operation

    def set_operation (self, op):
        self.operation = op
