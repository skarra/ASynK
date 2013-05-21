##
## Created : Tue Apr 02 13:00:12 IST 2013
##
## Copyright (C) 2013 by Sriram Karra <karra.etc@gmail.com>
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

from   state        import Config
from   pimdb        import PIMDB
from   folder       import Folder
from   folder_cd    import CDContactsFolder
from   caldavclientlibrary.protocol.webdav.definitions  import davxml
from   caldavclientlibrary.protocol.carddav.definitions import carddavxml
from   caldavclientlibrary.protocol.url   import URL
from   caldavclientlibrary.client.account import CalDAVAccount

import datetime, logging, os, re, urllib, urlparse

class CDPIMDB(PIMDB):
    """A wrapper over a connection to a CardDAV server with methods for common
    server operations"""

    def __init__ (self, config, uri, user, pw):
        """If 'uri' dooes not start with a http:// or a https:// it is
        assumed to be equivalent to http:// """

        logging.debug('Logging into CardDAV server: %s - user: %s',
                      uri, user)

        PIMDB.__init__(self, config)
        self.set_user(user)
        self.set_pw(pw)
        self.parse_uri(uri)
        self.cd_init()
        self.set_folders()
        self.set_def_folders()

    ##
    ## First implementation of the abstract methods of PIMDB.
    ##

    def get_dbid (self):
        """See the documentation in class PIMDB"""

        return 'cd'

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
            logging.erorr('Only Contact Groups are supported at this time.')
            return None

        root = self.get_def_root_folder_path()
        resource = URL(os.path.join(root, fname))
        ret = self.get_account().session.makeAddressBook(resource)

    def del_folder (self, itemid, store=None):
        """Get rid of the specified folder."""

        sess = self.session()
        path = URL(url=itemid)

        logging.info('Deleting all the contained items. Will not remove folder')

        items = sess.getPropertiesOnHierarchy(path, (davxml.getetag,))
        hrefs = [x for x in items.keys() if x != path.toString().strip()]

        for href in hrefs:
            sess.deleteResource(URL(url=href))
            logging.info('Deleted file %s...', href)

    def set_folders (self):
        """See the documentation in class PIMDB"""

        fs = self.fetch_folders()
        for uri, root, name in fs:
            fo   = CDContactsFolder(self, uri, name, root)
            self.add_contacts_folder(fo)

    def set_def_folders (self):
        """See the documentation in class PIMDB"""

        ## FIXME: We should be fetching the default folders using:
        ## {urn:ietf:params:xml:ns:carddav}default-addressbook-URL

        root     = self.get_def_root_folder_path()
        props    = (carddavxml.def_adbk_url,)

        res, bad = self.session().getProperties(URL(url=root), props)
        def_uri  = res.values()[0].toString().strip()
        logging.debug('Looking for default folder: "%s"', def_uri)
        def_f, t = self.find_folder(def_uri)
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
       elif type(t) == str or type(t) == unicode:
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

        res = re.search(r'(\d\d\d\d\d\d\d\dT\d\d\d\d\d\dZ).*', t)
        if res:
            t = res.group(1)
        else:
            return None
        
        return datetime.datetime.strptime(t, '%Y%m%dT%H%M%SZ')

    ## Note: I learnt of the setter, and @property and @property.setter
    ## decorations well after I started developing ASynK. So for the sake of
    ## consitency across the code base we will use explicit get_ and set_
    ## methods

    def get_server (self):
        return self.server

    def set_server (self, server):
        self.server = server

    def get_account (self):
        return self.account

    def set_account (self, account):
        self.account = account

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
        return self.get_account().session
    ##
    ## Other internal and non-static methods
    ##

    def parse_uri (self, uri):
        if not uri.startswith('http'):
            uri = 'http://' + uri
        splits = urlparse.urlsplit(uri)
        self.set_server(splits.scheme + "://" + splits.netloc)
        self.set_path(splits.path)

    def cd_init (self):
        sf  = self.get_server()
        ssl = sf.startswith('https://')
        server = sf[8:] if ssl else sf[7:]
        account  = CalDAVAccount(server, ssl=ssl, user=self.get_user(),
                                 pswd=self.get_pw(), root=self.get_path(),
                                 principal=None, logging=False)
        self.set_account(account)

    def get_contacts_folders_roots (self):
        return self.get_account().getPrincipal().adbkhomeset

    def get_def_root_folder_path (self):
        homeset = self.get_contacts_folders_roots()
        if not homeset:
            raise Exception('Principal does not have any addressbook home')

        ## FIXME: What does it mean to have multiple paths in adbkhomeset?
        return homeset[0].path

    def fetch_folders (self):
        """Fetch and return the list of addressbooks from the server."""
        
        logging.debug('CDPIMDB.set_folders(): Begin')

        sess  = self.session()
        roots = self.get_contacts_folders_roots()
        props = (davxml.resourcetype, davxml.getlastmodified,)

        ret   = []
        for root in roots:
            path = root.path
            logging.debug('Processing Root path %s in Root.', path)
            results = sess.getPropertiesOnHierarchy(URL(url=path), props)
            items = results.keys()
            items.sort()
            for rurl in items:
                rurl = urllib.unquote(rurl)
                if rurl == path:
                    continue

                props = results[rurl]
                rtype = props.get(davxml.resourcetype)
                if not isinstance(rtype, str):
                    for child in rtype.getchildren():
                        if child.tag == carddavxml.addressbook:
                            name = rurl[len(path):-1]
                            logging.debug('Found Folder %-15s in URI "%s"',
                                          name, rurl)
                            ret.append((rurl.strip(), path, name))

        logging.debug('CDPIMDB.set_folders(): Done.')

        return ret
