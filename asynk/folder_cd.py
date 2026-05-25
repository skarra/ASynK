##
## Created : Wed Apr 03 12:59:03 IST 2013
## SPDX-FileCopyrightText: 2013-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK

from utils import HTTPError
from folder import Folder
from contact_cd import CDContact

import logging, vobject, urllib.parse, html

class CDContactsFolder(Folder):
    def __init__ (self, db, fid, gn, root_path):
        Folder.__init__(self, db)

        if fid[-1] != '/':
            fid += '/'

        self.set_itemid(fid)
        self.set_name(gn)
        self.set_root_path(root_path)
        self.set_type(Folder.CONTACT_t)
        self.reset_contacts()

    ##
    ## Internal and helper functions
    ##        

    def __str__ (self):
        ret = 'Contacts'

        return ('%s.\tName: %s;\tGID: %s;\t' % (ret, self.get_name(),
                                                self.get_itemid()))

    def get_batch_size (self):
        """See the documentation in folder.Folder"""

        return 100

    def prep_sync_lists (self, destid, sl, updated_min=None, cnt=0):
        """See the documentation in folder.Folder"""

        pname = sl.get_pname()
        conf  = self.get_config()
        pdb1id = conf.get_profile_db1(pname)
        oldi  = conf.get_itemids(pname)
        curi  = self.get_itemids(pname, destid)

        kss = list(curi.keys())
        for x, y in oldi.items():
            if not x in kss and not y in kss:
                logging.debug('Del      Carddav Contact: %s:%s', x, y)
                colln = getattr(self, 'colln', getattr(self.get_db(), 'colln', None))
                is_db1 = (colln == 1) if colln is not None else (pdb1id == self.get_dbid())
                if is_db1:
                    sl.add_del(x, y)
                else:
                    sl.add_del(y,x)

        stag = conf.make_sync_label(pname, destid)

        if not updated_min:
            updated_min = conf.get_last_sync_stop(pname)

        # Note: crdid refers to the CardDAV server item id for the contact,
        # and the remid refers to the ID on the other end of the sync
        # profile.
        for i, (crdid, item) in enumerate(self.get_contacts().items()):
            try:
                label, remid = item.get_sync_tags(stag)[0]
            except IndexError as e:
                label = None
                remid = None

            name = 'No Name'
            if item.get_name():
                name = item.get_name()
            elif item.get_disp_name():
                name = item.get_disp_name()

            if not remid:
                # New contact
                logging.debug('New      CardDAV Contact: %20s %s', 
                              name, crdid)
                sl.add_new(crdid)
            else:
                if item.get_updated(iso=True) > updated_min:
                    logging.debug('Modified CardDAV Contact: %20s %s', 
                                  name, crdid)
                    sl.add_mod(crdid, remid)
                else:
                    sl.add_unmod(crdid)

            # FIXME: We should really storing the etags here...
            sl.add_etag(crdid, item.get_etag())

        logging.debug('Total Contacts   : %5d', len(curi))

    def get_itemids (self, pname, destid):
        """See the documentation in folder.Folder"""

        self._refresh_contacts()
        ret = {}
        stag = self.get_config().make_sync_label(pname, destid)
        for locid, con in self.get_contacts().items():
            if stag in con.get_sync_tags():
                t, remid = con.get_sync_tags(stag)[0]
                ret.update({locid : remid})

        return ret

    def del_itemids (self, itemids):
        client = self.get_db().session()
        for itemid in itemids:
            path = self.item_path(itemid)
            try:
                res = client.request(path, 'DELETE')
                if res.status in (200, 204):
                    self.del_contact(itemid)
                    logging.info('Deleted CardDAV server contact %s...', itemid)
                else:
                    logging.error('Could not delete itemid: %s (status: %d)', itemid, res.status)
            except Exception as e:
                logging.error('Could not delete itemid: %s (%s)', itemid, e)

    def item_path (self, itemid):
        if itemid[0] != '/':
            iid = self.get_itemid()
            if iid[-1] != '/':
                iid += '/'
            itemid = iid + itemid + '.vcf'

        return itemid

    def find_item (self, itemid):
        """See the documentation in folder.Folder"""
        client = self.get_db().session()
        path = self.item_path(itemid)
        try:
            res = client.request(path, 'GET')
            if res.status == 404:
                return None
            if res.status != 200:
                logging.error("Failed to GET contact %s (status: %d)", path, res.status)
                return None
            data = res.raw if isinstance(res.raw, str) else getattr(res.raw, 'text', str(res.raw))
            itemid = CDContact.normalize_cdid(itemid)
            
            etag = res.headers.get('etag') or res.headers.get('ETag')
            contact = CDContact(self, vco=vobject.readOne(data), itemid=itemid)
            if etag:
                contact.set_etag(etag.strip('"'))
            return contact
        except Exception as e:
            logging.error('Error (%s) parsing vCard object for %s',
                          e, itemid)
            raise

    def find_items (self, itemids):
        """See the documentation in folder.Folder"""
        client = self.get_db().session()
        ids = [self.item_path(x) for x in itemids]
        
        import xml.etree.ElementTree as ET
        
        multiget = ET.Element('{urn:ietf:params:xml:ns:carddav}addressbook-multiget')
        prop = ET.SubElement(multiget, '{DAV:}prop')
        ET.SubElement(prop, '{DAV:}getetag')
        ET.SubElement(prop, '{urn:ietf:params:xml:ns:carddav}address-data')
        
        for href in ids:
            path_part = urllib.parse.urlsplit(href).path
            href_el = ET.SubElement(multiget, '{DAV:}href')
            href_el.text = path_part
            
        ET.register_namespace('D', 'DAV:')
        ET.register_namespace('C', 'urn:ietf:params:xml:ns:carddav')
        
        body = ET.tostring(multiget, encoding='utf-8').decode('utf-8')
        headers = {'Depth': '1', 'Content-Type': 'text/xml; charset="utf-8"'}
        
        try:
            res = client.request(self.get_itemid(), 'REPORT', body=body, headers=headers)
        except Exception as e:
            logging.error("Failed REPORT request for addressbook-multiget: %s", e)
            raise
            
        ret = []
        if res and res.status in (200, 207):
            res.find_objects_and_props()
            for href, props in res.objects.items():
                etag_elem = props.get('{DAV:}getetag')
                vcf_elem = props.get('{urn:ietf:params:xml:ns:carddav}address-data')
                
                if vcf_elem is None or not vcf_elem.text:
                    logging.debug("No address-data found for %s", href)
                    continue
                    
                etag = etag_elem.text if etag_elem is not None else None
                if etag:
                    etag = etag.strip('"')
                    
                key = CDContact.normalize_cdid(href)
                try:
                    cd = CDContact(self, vco=vobject.readOne(vcf_elem.text), itemid=key)
                    if etag:
                        cd.set_etag(etag)
                    ret.append(cd)
                except Exception as e:
                    logging.error('Error (%s) parsing vCard object for %s', e, key)
                    raise
                    
        return ret

    def batch_create (self, src_sl, src_dbid, items):
        """See the documentation in folder.Folder"""

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = src_sl.get_pname()

        src_sync_tag = c.make_sync_label(src_sl.get_pname(), src_dbid)
        dst_sync_tag = c.make_sync_label(src_sl.get_pname(), my_dbid)

        success = True
        for item in items:

            ## CardDAV does not support a multiput operation. So we will have
            ## to PUT the damn items one at a time.
            con_itemid = item.get_itemid_from_synctags(pname, 'cd')
            cd = CDContact(self, con=item, con_itemid=con_itemid)
            cd.update_sync_tags(src_sync_tag, item.get_itemid(), save=True)
            self.add_contact(cd)            

            item.update_sync_tags(dst_sync_tag, cd.get_itemid())

            logging.info('Successfully created CardDAV entry for %30s (%s)',
                          cd.get_disp_name(), cd.get_itemid())

        return True

    def batch_update (self, src_sl, src_dbid, items):
        """See the documentation in folder.Folder"""

        my_dbid = self.get_dbid()
        c       = self.get_config()
        pname   = src_sl.get_pname()

        src_sync_tag = c.make_sync_label(pname, src_dbid)
        dst_sync_tag = c.make_sync_label(pname, my_dbid)

        cons = self.get_contacts()

        success = True

        for item in items:
            tag, href = item.get_sync_tags(dst_sync_tag)[0]
            con_old = cons[href]
            con_itemid = item.get_itemid_from_synctags(pname, 'cd')
            con_new = CDContact(self, con=item, con_itemid=con_itemid)

            con_new.set_uid(con_old.get_uid())
            con_new.update_sync_tags(src_sync_tag, item.get_itemid())

            try:
                con_new.save(etag=con_old.get_etag())
                logging.info('Successfully updated CardDAV entry for %30s (%s)',
                             con_new.get_disp_name(), con_new.get_itemid())
            except HTTPError as e:
                logging.error('Error (%s). Could not update CardDAV entry %s',
                               e, con_new.get_disp_name())
                success = False

        return success

    def writeback_sync_tags (self, pname, items):
        """See the documentation in folder.Folder"""

        logging.info('Writing sync state to CardDAV server...')
        success = True
        for item in items:
            success = success and item.save()

        logging.info('Writing sync state to CardDAV server...done')
        return success

    def bulk_clear_sync_flags (self, label_re=None):
        """See the documentation in folder.Folder"""

        logging.info('folder_cd:bulk_clear_sync_tags: Not implemented yet.')
        return True

    ##
    ## Internal and helper functions
    ##        

    def reset_contacts (self):
        self.contacts = {}

    def get_contacts (self):
        return self.contacts

    def add_contact (self, bbc):
        self.contacts.update({bbc.get_itemid() : bbc})

    def del_contact (self, itemid):
        if itemid in self.contacts:
            del self.contacts[itemid]

    def _refresh_contacts (self):
        logging.debug('Refreshing Contacts for folder %s...',
                      self.get_name())
        self.reset_contacts()
        client = self.get_db().session()

        body = """<?xml version="1.0" encoding="utf-8" ?>
        <D:propfind xmlns:D="DAV:">
          <D:prop>
            <D:getetag/>
          </D:prop>
        </D:propfind>"""
        headers = {'Depth': '1', 'Content-Type': 'text/xml; charset="utf-8"'}

        try:
            res = client.request(self.get_itemid(), 'PROPFIND', body=body, headers=headers)
        except Exception as e:
            logging.error("Failed to fetch contact etags: %s", e)
            return

        hrefs = []
        if res and res.status in (200, 207):
            res.find_objects_and_props()
            for href, props in res.objects.items():
                norm_href = href
                if norm_href.endswith('/'):
                    norm_href = norm_href[:-1]
                norm_folder = self.get_itemid()
                if norm_folder.endswith('/'):
                    norm_folder = norm_folder[:-1]

                if norm_href == norm_folder or norm_href == urllib.parse.urlsplit(norm_folder).path:
                    continue

                etag_elem = props.get('{DAV:}getetag')
                if etag_elem is not None:
                    hrefs.append(href)

        if hrefs:
            cons = self.find_items(hrefs)
            for con in cons:
                self.add_contact(con)
                logging.debug('Successfully fetched and added contact: %s',
                              con.get_disp_name())

        logging.debug('Refreshing Contacts for folder %s..done.',
                      self.get_name())

    def show (self, detailed=False):
        self._refresh_contacts()
        cons = self.get_contacts()
        logging.info('Total contained contacts: %d', len(list(cons.keys())))
        logging.info('Items in brief: ')

        for itemid, con in cons.items():
            if detailed:
                logging.info('Printing Contact: %s', con.get_disp_name())
                logging.info('%s', con)
            else:
                logging.info('  Name: %-25s Gender: %s Itemid: %s',
                             con.get_disp_name(), con.get_gender(), itemid)

    def get_root_path (self):
        return self._get_prop('root_path')

    def set_root_path (self, root_path):
        self._set_prop('root_path', root_path)

    def put_item (self, name, data, content_type, etag=None):
        client = self.get_db().session()
        headers = {'Content-Type': content_type}
        if etag:
            headers['If-Match'] = f'"{etag}"'
        else:
            headers['If-None-Match'] = '*'

        logging.debug("PUT contact %s with etag %s", name, etag)
        res = client.request(name, 'PUT', body=data, headers=headers)
        if res.status not in (200, 201, 204):
            raw_body = res.raw if isinstance(res.raw, str) else getattr(res.raw, 'text', str(res.raw))
            logging.error("Failed to PUT contact: status %d, body %s", res.status, raw_body)
            raise HTTPError(res.status, raw_body)

        ## Capture the new ETag from the response so subsequent PUTs
        ## (e.g. writeback_sync_tags) use the correct If-Match value.
        new_etag = None
        if hasattr(res, 'headers'):
            new_etag = res.headers.get('etag') or res.headers.get('ETag')
        if new_etag:
            new_etag = new_etag.strip('"')

        return name, new_etag
