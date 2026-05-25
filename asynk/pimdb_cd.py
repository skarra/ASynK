##
## Created : Tue Apr 02 13:00:12 IST 2013
## SPDX-FileCopyrightText: 2013-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
## ####
##

from utils import HTTPError
from state import Config
from pimdb import PIMDB
from folder import Folder
from folder_cd import CDContactsFolder
import caldav

import iso8601
import datetime, logging, os, re, sys, urllib.request, urllib.parse, urllib.error, urllib.parse

class CardDAVPrincipalNotFoundError(Exception):
    pass

class CDPIMDB(PIMDB):
    """A wrapper over a connection to a CardDAV server with methods for common
    server operations"""

    def __init__ (self, config, uri, user, pw):
        """If 'uri' dooes not start with a http:// or a https:// it is
        assumed to be equivalent to http:// """

        logging.info('Logging into CardDAV server: %s - user: %s...',
                     uri, user)

        PIMDB.__init__(self, config)
        self.set_user(user)
        self.set_pw(pw)
        self.set_client_logging(config.get_cd_logging())
        self.parse_uri(uri)
        self.cd_init()
        self.set_folders()
        self.set_def_folders()

        logging.info('Logging into CardDAV server: %s - user: %s... done.',
                     uri, user)

    ##
    ## First implementation of the abstract methods of PIMDB.
    ##

    def get_dbid (self):
        """See the documentation in class PIMDB"""

        return 'cd'

    def list_folders (self, silent=False):
        """List all addressbooks. Returns a list of (fid, name, folder_object) tuples."""
        ret = []
        for i, f in enumerate(self.get_contacts_folders()):
            fid = f.get_itemid()
            name = f.get_name()
            if not silent:
                logging.info(' %2d: Contacts Name: %-25s ID: %s',
                             i, name, fid)
            ret.append((fid, name, f))
        return ret


    def new_folder (self, fname, ftype=None, storeid=None):
        """See the documentation in class PIMDB.

        It appears like CardDAV allows multiple 'root' addressbooks, and
        multiple folders in each addressbook. In order to support this we will
        have to provide a storeid to distinguish the various root
        addressbooks. For now new_folder will only create the default root
        addressbook which is the first entry in the adbkhomeset property."""

        logging.debug('bb:new_folder(): fname: %s; ftype: %s', fname, ftype)
        if not ftype:
            ftype = Folder.CONTACT_t

        if ftype != Folder.CONTACT_t:
            logging.error('Only Contact Groups are supported at this time.')
            return None

        root = self.get_def_root_folder_path()
        if not root.endswith('/'):
            root += '/'
        folder_url = root + fname + '/'

        fo, t = self.find_folder(folder_url)
        if fo:
            logging.info("Addressbook folder already exists: %s", folder_url)
            return fo

        body = f"""<?xml version="1.0" encoding="utf-8" ?>
        <D:mkcol xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
          <D:set>
            <D:prop>
              <D:resourcetype>
                <D:collection/>
                <C:addressbook/>
              </D:resourcetype>
              <D:displayname>{fname}</D:displayname>
            </D:prop>
          </D:set>
        </D:mkcol>"""

        headers = {'Content-Type': 'text/xml; charset="utf-8"'}
        logging.info("Creating new addressbook at %s", folder_url)
        res = self.client.request(folder_url, 'MKCOL', body=body, headers=headers)
        if res.status not in (201, 200, 207):
            logging.error("Failed to create addressbook: status %d, body %s", res.status, res.raw)
            return None

        self.set_folders()
        fo, t = self.find_folder(folder_url)
        return fo

    def del_folder (self, itemid, store=None):
        """Get rid of the specified folder."""
        logging.info('Deleting all the contained items from %s. Will not remove folder', itemid)

        body = """<?xml version="1.0" encoding="utf-8" ?>
        <D:propfind xmlns:D="DAV:">
          <D:prop>
            <D:getetag/>
          </D:prop>
        </D:propfind>"""
        headers = {'Depth': '1', 'Content-Type': 'text/xml; charset="utf-8"'}

        try:
            res = self.client.request(itemid, 'PROPFIND', body=body, headers=headers)
        except Exception as e:
            logging.error("Failed to list items for del_folder: %s", e)
            return

        if res and res.status in (200, 207):
            res.find_objects_and_props()
            for href in res.objects.keys():
                norm_href = href
                if norm_href.endswith('/'):
                    norm_href = norm_href[:-1]
                norm_itemid = itemid
                if norm_itemid.endswith('/'):
                    norm_itemid = norm_itemid[:-1]

                if norm_href == norm_itemid or norm_href == urllib.parse.urlsplit(norm_itemid).path:
                    continue

                full_href = href
                if full_href.startswith('/'):
                    full_href = self.get_server() + full_href

                logging.info('Deleting file %s...', full_href)
                try:
                    self.client.request(full_href, 'DELETE')
                except Exception as e:
                    logging.error("Failed to delete %s: %s", full_href, e)

    def set_folders (self):
        """See the documentation in class PIMDB"""

        fs = self.fetch_folders()
        for uri, root, name in fs:
            fo   = CDContactsFolder(self, uri, name, root)
            self.add_contacts_folder(fo)

    def set_def_folders (self):
        """See the documentation in class PIMDB"""

        root = self.get_def_root_folder_path()
        body = """<?xml version="1.0" encoding="utf-8" ?>
        <D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
          <D:prop>
            <C:default-addressbook-url/>
          </D:prop>
        </D:propfind>"""
        headers = {'Depth': '0', 'Content-Type': 'text/xml; charset="utf-8"'}

        def_uri = None
        try:
            res = self.client.request(root, 'PROPFIND', body=body, headers=headers)
            if res and res.status in (200, 207):
                res.find_objects_and_props()
                for href, props in res.objects.items():
                    tag = '{urn:ietf:params:xml:ns:carddav}default-addressbook-url'
                    if tag in props:
                        elem = props[tag]
                        href_elem = elem.find('.//{DAV:}href')
                        if href_elem is not None and href_elem.text:
                            def_uri = href_elem.text.strip()
                            break
        except Exception as e:
            logging.debug("Could not get default-addressbook-url property: %s", e)

        def_f = None
        if def_uri:
            if def_uri.startswith('/'):
                def_uri = self.get_server() + def_uri
            if not def_uri.endswith('/'):
                def_uri += '/'
            logging.debug('Looking for default folder: "%s"', def_uri)
            def_f, t = self.find_folder(def_uri)

        if not def_f:
            logging.debug('Could not find default adbk Property or folder match.')
            fs = self.get_contacts_folders()
            if len(fs) > 0:
                def_f = fs[0]
                logging.debug('Setting first available folder as default: %s',
                              def_f.get_name())
            else:
                logging.debug('No folders found on the server to set as default.')
                def_f = None

        self.set_def_folder(Folder.CONTACT_t, def_f)
   
    def set_sync_folders (self):
        """See the documentation in class PIMDB"""

        raise NotImplementedError

    def prep_for_sync (self, dbid, pname, dr):
        """See the documentation in class PIMDB"""

        ## FIXME: Can do stuff like ensure if the folder is still there, and
        ## such error checking.
        pass

    ##
    ## Now the non-abstract methods and internal methods
    ##

    @classmethod
    def get_vcard_time (self, t=None):
       """Convert a datetime.datetime object to a time string formatted in the
       format used in vCard files - which is always represented in UTC. So the
       passed value should either be a naive object having the UTC time, or an
       aware object with tzinfo set.

       If t is None, the current time is returned."""

       ## FIXME: This whole date time business is a HUGE mess. We should
       ## standardize the way we deal with timestamps. The best case scenario
       ## all timestamps stored in item/contact objects should be
       ## datetime.datetime obejcts, and any conversions that are needed
       ## should be handled at the client side.

       if not t:
           t = datetime.datetime.utcnow()
       elif type(t) == str or type(t) == str:
           ## Most likely this is in iso8601 format.
           res = re.search(r'(\d\d\d\d\-\d\d\-\d\d \d\d:\d\d:\d\d).*', t)
           if res:
               t = res.group(1)
               t = datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
           else:
               t = datetime.datetime.utcnow()

       else:
           if t.tzinfo:
               t = t - t.tzinfo.utcoffset(t)
    
       return t.strftime('%Y%m%dT%H%M%SZ')

    @classmethod
    def parse_vcard_time (self, t):
        """Return a datetime object containing the native UTC timestamp based
        on the specified vCard REV timestamp string."""

       # IMP: Note that we assume the time is in UTC - and ignore what is
       # actually in the string. This sucks, but this is all I am willing to
       # do for the m moment. FIXME

        res = re.search(r'(\d\d\d\d\d\d\d\dT\d\d\d\d\d\d).*', t)
        if res:
            t = res.group(1)
            return datetime.datetime.strptime(t, '%Y%m%dT%H%M%S')
        else:
            t = iso8601.parse_date(t)
            return datetime.datetime.utcfromtimestamp(t)

    ## Note: I learnt of the setter, and @property and @property.setter
    ## decorations well after I started developing ASynK. So for the sake of
    ## consitency across the code base we will use explicit get_ and set_
    ## methods

    def get_server (self):
        return self.server

    def set_server (self, server):
        self.server = server

    def get_account (self):
        return self.client

    def set_account (self, client):
        self.client = client

    def get_path (self):
        return self.path

    def set_path (self, path):
        self.path = path if path else '/'

    def get_user (self):
        return self.user

    def set_user (self, user):
        self.user = user

    def get_pw (self):
        return self.pw

    def set_pw (self, pw):
        self.pw = pw

    def get_def_headers (self):
        return self.def_headers

    def set_def_headers (self, d):
        self.def_headers = d

    def get_settings (self):
        return self.settings

    def set_settings (self, s):
        self.settings = s

    def session (self):
        return self.client

    def set_client_logging (self, val):
        self.client_logging = val

    def get_client_logging (self):
        return self.client_logging

    ##
    ## Other internal and new methods
    ##

    def parse_uri (self, uri):
        if not uri.startswith('http'):
            uri = 'http://' + uri
        splits = urllib.parse.urlsplit(uri)
        self.set_server(splits.scheme + "://" + splits.netloc)
        self.set_path(splits.path)

    def cd_init (self):
        url = self.get_server() + self.get_path()
        logging.info("Initializing caldav.DAVClient with URL: %s", url)
        try:
            client = caldav.DAVClient(url, username=self.get_user(), password=self.get_pw())
            self.client = client
            self.discover_principal_and_home()
        except Exception as e:
            logging.fatal('Could not open connection to %s. Error: %s', url, e)
            raise

    def discover_principal_and_home (self):
        # 1. Find current-user-principal
        body = """<?xml version="1.0" encoding="utf-8" ?>
        <D:propfind xmlns:D="DAV:">
          <D:prop>
            <D:current-user-principal/>
          </D:prop>
        </D:propfind>"""
        headers = {'Depth': '0', 'Content-Type': 'text/xml; charset="utf-8"'}

        start_url = str(self.client.url)
        try:
            res = self.client.request(start_url, 'PROPFIND', body=body, headers=headers)
        except Exception as e:
            logging.warning("Initial PROPFIND for principal failed: %s. Using start URL as principal.", e)
            res = None

        principal_url = None
        if res and res.status in (200, 207):
            res.find_objects_and_props()
            for href, props in res.objects.items():
                tag = '{DAV:}current-user-principal'
                if tag in props:
                    elem = props[tag]
                    href_elem = elem.find('.//{DAV:}href')
                    if href_elem is not None and href_elem.text:
                        principal_url = href_elem.text.strip()
                        break

        if not principal_url:
            principal_url = self.get_path()
            logging.info("Principal URL not discovered. Defaulting to: %s", principal_url)
        else:
            logging.info("Discovered Principal URL: %s", principal_url)

        if principal_url.startswith('/'):
            principal_url = self.get_server() + principal_url

        self.principal_url = principal_url

        # 2. Find addressbook-home-set
        body_home = """<?xml version="1.0" encoding="utf-8" ?>
        <D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
          <D:prop>
            <C:addressbook-home-set/>
          </D:prop>
        </D:propfind>"""
        headers_home = {'Depth': '0', 'Content-Type': 'text/xml; charset="utf-8"'}
        try:
            res_home = self.client.request(self.principal_url, 'PROPFIND', body=body_home, headers=headers_home)
        except Exception as e:
            logging.fatal("Failed to fetch addressbook-home-set: %s", e)
            raise

        homeset_url = None
        if res_home and res_home.status in (200, 207):
            res_home.find_objects_and_props()
            for href, props in res_home.objects.items():
                tag = '{urn:ietf:params:xml:ns:carddav}addressbook-home-set'
                if tag in props:
                    elem = props[tag]
                    href_elem = elem.find('.//{DAV:}href')
                    if href_elem is not None and href_elem.text:
                        homeset_url = href_elem.text.strip()
                        break

        if not homeset_url:
            homeset_url = self.principal_url
            logging.info("Addressbook Home Set not discovered. Fallback to: %s", homeset_url)
        else:
            logging.info("Discovered Addressbook Home Set URL: %s", homeset_url)

        if homeset_url.startswith('/'):
            homeset_url = self.get_server() + homeset_url

        self.homeset_url = homeset_url

    def get_contacts_folders_roots (self):
        return [self.homeset_url]

    def get_def_root_folder_path (self):
        return self.homeset_url

    def fetch_folders (self):
        """Fetch and return the list of addressbooks from the server."""
        logging.debug('CDPIMDB.fetch_folders(): Begin')

        body = """<?xml version="1.0" encoding="utf-8" ?>
        <D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
          <D:prop>
            <D:resourcetype/>
            <D:displayname/>
          </D:prop>
        </D:propfind>"""
        headers = {'Depth': '1', 'Content-Type': 'text/xml; charset="utf-8"'}

        home = self.get_def_root_folder_path()
        try:
            res = self.client.request(home, 'PROPFIND', body=body, headers=headers)
        except Exception as e:
            logging.error("Failed to fetch folders in fetch_folders: %s", e)
            return []

        ret = []
        if res and res.status in (200, 207):
            res.find_objects_and_props()
            for href, props in res.objects.items():
                norm_href = href
                if norm_href.endswith('/'):
                    norm_href = norm_href[:-1]
                norm_home = home
                if norm_home.endswith('/'):
                    norm_home = norm_home[:-1]

                if norm_href == norm_home or norm_href == urllib.parse.urlsplit(norm_home).path:
                    continue

                is_addressbook = False
                res_type = props.get('{DAV:}resourcetype')
                if res_type is not None:
                    for child in res_type:
                        if child.tag == '{urn:ietf:params:xml:ns:carddav}addressbook':
                            is_addressbook = True
                            break

                if is_addressbook:
                    name = None
                    disp_name = props.get('{DAV:}displayname')
                    if disp_name is not None and disp_name.text:
                        name = disp_name.text.strip()
                    if not name:
                        name = os.path.basename(href.rstrip('/'))

                    full_href = href
                    if full_href.startswith('/'):
                        full_href = self.get_server() + full_href
                    if not full_href.endswith('/'):
                        full_href += '/'
                    ret.append((full_href, home, name))
                    logging.debug("Found Addressbook: %s at %s", name, full_href)

        logging.debug('CDPIMDB.fetch_folders(): Done. Found %d folders.', len(ret))
        return ret
