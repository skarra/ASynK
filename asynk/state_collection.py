##
## Created: Sun Oct 05 21:35:37 IST 2014
## SPDX-FileCopyrightText: 2014-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
####
##
## The classes in this file represent different "collection" types. A
## collection in ASynK is a folder of contacts uniquely specified by a tuple
## (DB ID, Store ID, Folder ID)
##

import logging, netrc, os
from   abc              import ABCMeta, abstractmethod

try:
    from pimdb_ol import OLPIMDB
except ImportError as e:
    ## This could mean one of two things: (a) we are not on Windows, or (b)
    ## some of th relevant supporting stuff is not installed (like
    ## pywin32). these error cases are handled elsewhere, so move on.
    pass

class AsynkCollectionError(Exception):
    pass

class NetrcAuth:
    """A helper Singletone class to parse netrc files and to look for the
    right authentication information for a specified collection."""

    def __init__ (self):
        try:
            self.netrc = None
            self.netrc = netrc.netrc()
        except IOError as e:
            logging.info('~/.netrc not found.')
        except netrc.NetrcParseError as e:
            logging.warning('Ignoring ~/.netrc: could not parse it (%s)', e)

    def get_auth (self, pname, dbid, coll_n):
        """Look for the right collection, parsing the netrc for both styles of
        machine names - the old one which was of the form gc_pname and the new
        one of the form gc1_pname. Note that this means the caller should know
        how to use the coll_n parameter and should expect that parameter to be
        ignored if that suits the netrc data!"""

        if self.netrc is None:
            return None, None

        tries = ['%s%s_%s' % (dbid, coll_n, pname), '%s_%s' % (dbid, pname)]
        for mach in tries:
            res = self.netrc.authenticators(mach)
            if res is not None:
                return res[0], res[2]

        return None, None

netrc = NetrcAuth()

## FIXME: The Profile class needs a little more work; It really calls for a
## refactor of state.py and this class perhaps fits into a file of its
## own. Let's take this up at a separate time as a separate refactoring
## altogether.

class Profile:
    def __init__ (self, conf, pname=None, **kwargs):
        self.set_conf(conf)
        self.set_pname(pname)
        self.read_netrc()

    def read_netrc (self):
        self.netrc = NetrcAuth()

    ##
    ## getter / setters
    ##

    def get_conf (self):
        return self.name

    def set_conf (self, conf):
        self.conf = conf

    def get_pname (self):
        return self.name

    def set_pname (self, pname):
        self.pname = pname


class Collection:
    def __init__ (self, config=None, dbid=None, stid=None,
                  fid=None, pname=None, colln=1):
        self.set_config(config)
        self.set_dbid(dbid)
        self.set_db(None)
        self.set_stid(stid)
        self.set_fid(fid)
        self.set_pname(pname)
        self.set_colln(colln)

        self.set_username(None)
        self.set_pwd(None)
        self.set_folder_name(None)

    @abstractmethod
    def login (self):
        """Returns a PIMDB object of the right type after logging in to the
        appropriate store and authenticating oneself. For e.g. In case of a
        Google Contacts Store, this will login to the right server and
        estabish a connection."""

        pass

    ##
    ## Getters and Setters
    ##

    def get_db (self):
        return self.db

    def set_db (self, db):
        self.db = db
        if db:
            db.colln = self.get_colln()
        return db

    def get_dbid (self):
        return self.dbid

    def set_dbid (self, dbid):
        self.dbid = dbid

    def get_stid (self):
        return self.stid

    def set_stid (self, stid):
        self.stid = stid

    def get_fid (self, cd_fix=False):
        fid = self.fid
        if (fid is not None and cd_fix and self.get_dbid() == 'cd' and
            fid != 'default' and fid[-1] != '/'):
            fid += '/'
        return fid

    def set_fid (self, fid):
        self.fid = fid

    def get_username (self):
        return self.username

    def set_username (self, username):
        self.username = username

    def get_pwd (self):
        return self.pwd

    def set_pwd (self, pwd):
        self.pwd = pwd

    def get_pname (self):
        return self.pname

    def set_pname (self, pname):
        self.pname = pname

    def get_folder_name (self):
        return self.folder_name

    def set_folder_name (self, folder_name):
        self.folder_name = folder_name

    def get_config (self):
        return self.config

    def set_config (self, config):
        self.config = config

    def get_colln (self):
        return self.colln

    def set_colln (self, colln):
        self.colln = colln

    def all_set (self):
        return (self.get_dbid() is not None and
                self.get_stid() is not None and
                self.get_fid()  is not None)

    ##
    ## more serious action
    ##

    def init_username_pwd (self):
        """Take in account the authentication credentials available from
        different sources for this Collection, resolve any conflicts and set
        the state to the right values.

        The rules are as follows:

        - Highest priority for cmdline username / password
        - Next comes anything specified in netrc
        - If neither of the above are set, then get them from stdin
        """

        u = None
        p = None
        u, p = netrc.get_auth(self.get_pname(), self.get_dbid(),
                              self.get_colln())

        cmd_u = self.get_username()
        cmd_p = self.get_pwd()

        dbn = '%s%s' % (self.get_dbid(), self.get_colln())

        if cmd_u is not None:
            logging.debug('Using cmdline username for collection %s', dbn)
            u = cmd_u
        else:
            while not u and self.force_username():
                u = input('Please enter username for %s: ' % dbn)

        if cmd_p is not None:
            logging.debug('Using cmdline password for collection %s', dbn)
            p = cmd_p
        else:
            while not p and self.force_pwd():
                p = input('Enter password for %s: ' % dbn)

        self.set_username(u)
        self.set_pwd(p)

    def force_username (self):
        return False

    def force_pwd (self):
        return False

    ##
    ## Finally some representation and other such object level methods
    ##


    def __eq__ (self, other):
        return (self.get_dbid() == other.get_dbid() and
                self.get_stid() == other.get_stid() and
                self.get_fid()  == other.get_fid())

    def __str__ (self):
        return str({'dbid' : self.dbid,
                    'stid' : self.stid,
                    'foid' : self.fid,
                    'username' : self.get_username(),
                    'password' : self.get_pwd()})

class BBCollection(Collection):
    def __init__ (self, config=None, stid=None, fid=None, pname=None, colln=1):
        Collection.__init__(self, config=config, dbid='bb', stid=stid,
                            fid=fid, pname=pname, colln=colln)

    def login (self):
        try:
            from pimdb_bb import BBPIMDB
        except ImportError as e:
            raise AsynkCollectionError(
                '%s: BBDB backend requires the demjson3 package.\n'
                'Install with: pip install asynk[bbdb]  '
                '(or: pip install demjson3)' % e)

        if self.get_stid() is not None:
            bbfn = self.get_stid()
        else:
            bbfn = '~/.bbdb'

        if not bbfn:
            raise AsynkCollectionError('Need BBDB Store to be specified')

        bb   = BBPIMDB(self.config, bbfn)
        return self.set_db(bb)


class CDCollection(Collection):
    def __init__ (self, config=None, stid=None, fid=None, pname=None, colln=1):
        Collection.__init__(self, config=config, dbid='cd', stid=stid, fid=fid,
                            pname=pname, colln=colln)

    def login (self):
        try:
            from pimdb_cd import CDPIMDB
        except ImportError as e:
            raise AsynkCollectionError("%s: Cannot use any CardDAV accounts" % e)

        try:
            pimcd = CDPIMDB(self.get_config(), self.get_stid(),
                            self.get_username(), self.get_pwd())
        except Exception as e:
            raise AsynkCollectionError('Invalid CardDAV credentials (%s).' % e)

        return self.set_db(pimcd)

    def force_username (self):
        return True

    def force_pwd (self):
        return True


class EXCollection(Collection):
    def __init__ (self, config=None, stid=None, fid=None, pname=None, colln=1):
        Collection.__init__(self, config=config, dbid='ex', stid=stid, fid=fid,
                            pname=pname, colln=colln)
        self.token_cache = None

    def get_token_cache (self):
        return self.token_cache

    def set_token_cache (self, token_cache):
        self.token_cache = token_cache

    def login (self):
        try:
            from pimdb_ex import EXPIMDB
        except ImportError as e:
            raise AsynkCollectionError(
                '%s: Exchange backend requires msal and requests packages.\n'
                'Install with: pip install asynk[exchange]  '
                '(or: pip install msal requests)' % e)

        # client_id can be overridden by the collection's pwd (e.g. from command line or netrc)
        client_id = self.get_pwd()

        pimex = EXPIMDB(self.get_config(),
                        client_id=client_id,
                        username=self.get_username(),
                        token_cache_path=self.get_token_cache())

        ## FIXME: Need better error handling
        return self.set_db(pimex)

    def force_username (self):
        return False

    def force_pwd (self):
        return False



class GCCollection(Collection):
    def __init__ (self, config=None, stid=None, fid=None, pname=None, colln=1):
        Collection.__init__(self, config=config, dbid='gc', stid=stid, fid=fid,
                            pname=pname, colln=colln)

    def login (self):
        try:
            from pimdb_gc import GCPIMDB
        except ImportError as e:
            raise AsynkCollectionError(
                '%s: Google Contacts backend requires additional packages.\n'
                'Install with: pip install asynk[google]  '
                '(or: pip install google-api-python-client '
                'google-auth-httplib2 google-auth-oauthlib)' % e)

        cs_path = self.get_pwd()
        if not cs_path:
            ## Fall back to the default client secrets shipped with ASynK
            default_cs = self.get_config().get_gc_client_secret_file()
            if default_cs:
                app_root = self.get_config().get_app_root()
                cs_path = os.path.join(app_root, default_cs)

        try:
            pimgc = GCPIMDB(self.get_config(),
                            self.get_username(), cs_path)
        except Exception as e:
            raise AsynkCollectionError('Invalid Google credentials (%s)' % e)

        return self.set_db(pimgc)

    def force_username (self):
        return True

    def force_pwd (self):
        return False


class OLCollection(Collection):
    def __init__ (self, config=None, stid=None, fid=None, pname=None, colln=1):
        Collection.__init__(self, config=config, dbid='ol', stid=stid, fid=fid,
                            pname=pname, colln=colln)

    def login (self):
        return OLPIMDB(self.get_config())


collection_id_to_class = {
    'bb' : BBCollection,
    'cd' : CDCollection,
    'ex' : EXCollection,
    'gc' : GCCollection,
    'ol' : OLCollection
    }
