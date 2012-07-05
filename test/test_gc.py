import getopt, logging, os, sys, traceback

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath('../')
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

def main ():
    tests = TestGCContact()

    tests.test_print_item('https://www.google.com/m8/feeds/contacts/karra.etc%40gmail.com/full/5e6d5ad30b0e2008')
    # tests.test_find_item('https://www.google.com/m8/feeds/contacts/karra.etc%40gmail.com/full/4b814c4c8f0c1558')
    #tests.test_sync_status()
    #tests.test_del_item('http://www.google.com/m8/feeds/contacts/karra.etc%40gmail.com/base/1fabc8309273c15')
    # tests.test_del_item('http://www.google.com/m8/feeds/contacts/karra.etc%40gmail.com/base/1fabc8309273c15')

class TestGCContact:
    def __init__ (self):
        from   pimdb_gc   import GCPIMDB
        from   state      import Config

        config = Config('../config.json', './state.test.json')

        # The following is the 'Gout' group on karra.etc@gmail.com
        # self.gid = 'http://www.google.com/m8/feeds/groups/karra.etc%40gmail.com/base/41baff770f898d85'
        self.gid = 'http://www.google.com/m8/feeds/groups/karra.etc%40gmail.com/base/6'

        # Parse command line options
        try:
            opts, args = getopt.getopt(sys.argv[1:], '', ['user=', 'pw='])
        except getopt.error, msg:
            print 'python gc_wrapper.py --user [username] --pw [password]'
            sys.exit(2)

        user = ''
        pw = ''
        # Process options
        for option, arg in opts:
            if option == '--user':
                user = arg
            elif option == '--pw':
                pw = arg

        while not user:
            user = raw_input('Please enter your username: ')

        while not pw:
            pw = raw_input('Password: ')
            if not pw:
                print 'Password cannot be blank'

        try:
            self.pimdb = GCPIMDB(config, user, pw)
        except gdata.client.BadAuthentication:
            print 'Invalid credentials. WTF.'
            raise

    def find_group (self, gid):
        #    sample.print_groups()
        self.gout, ftype = self.pimdb.find_folder(gid)
        if self.gout:
            print 'Found the sucker. Name is: ', self.gout.get_name()
            return self.gout
        else:
            print 'D''oh. Folder not found.'
            return

    def test_print_item (self, gcid):
        from   contact_gc import GCContact
        f = self.find_group(self.gid)

        gce = f.get_gdc().GetContact(gcid)
        g   = GCContact(f, gce=gce)

        print g

    def test_find_item (self, gcid):
        f = self.find_group(self.gid)
        gce = f.get_gdc().GetContact(gcid)

        name = None
        if gce.name.full_name:
            name = gce.name.full_name.text
        elif gce.name.family_name:
            name = gce.name.family_name.text
            if gce.name.given_name:
                name = gce.name.given_name.text + name
        elif gce.name.given_name:
            name = entry.name.given_name.text

        logging.debug('ID  : %s', gcid)
        logging.debug('Name: %s', name)

        return gce

    def test_del_item (self, gcid):
        f = self.find_group(self.gid)
        gce = f.get_gdc().GetContact(gcid)
        f.get_gdc().Delete(gce)

    def test_create_contact (self, f=None):
        if not f:
            f = self.gout

        c = GCContact(f)
        c.set_name("ScrewBall Joseph")

        cid = c.save()
        if cid:
            print 'Successfully added contact. ID: ', cid
        else:
            print 'D''oh. Failed.'

    def get_folder_contacts (self, f, cnt=0):
        """A thought out version of this routine will eventually go as a
        method of GCFolder class.."""

        logging.info('Querying Google for status of Contact Entries...')

        updated_min = f.get_config().get_last_sync_stop('gc', 'ol')
        feed = f._get_group_feed(updated_min=updated_min, showdeleted='false')

        logging.info('Response recieved from Google. Processing...')

        if not feed.entry:
            logging.info('No entries in feed.')
            return

        contacts = []
        for i, entry in enumerate(feed.entry):
            c = GCContact(f, gce=entry)
            contacts.append(c)

        return contacts

    def test_fetch_group_entries (self, gid=None):
        if not gid:
            gid = self.gid

        f  = self.find_group(gid)
        cs = self.get_folder_contacts(f)
        print 'Got %d entries\n' % len(cs)
        for i, c in enumerate(cs):
            print 'Contact No %d: ' % i
            print str(c)

    def test_sync_status (self, gid=None):
        from   sync       import SyncLists

        if not gid:
            gid = self.gid

        f = self.find_group(gid)
        sl = SyncLists(f, 'ol')
        f.prep_sync_lists('ol', sl)

    def test_pimdbgc ():
        config = Config('../app_state.json')
    
        # Parse command line options
        try:
            opts, args = getopt.getopt(sys.argv[1:], '', ['user=', 'pw='])
        except getopt.error, msg:
            print 'python gc_wrapper.py --user [username] --pw [password]'
            sys.exit(2)
    
        user = ''
        pw = ''
        # Process options
        for option, arg in opts:
            if option == '--user':
                user = arg
            elif option == '--pw':
                pw = arg
    
        while not user:
            user = raw_input('Please enter your username: ')
    
        while not pw:
            pw = raw_input('Password: ')
            if not pw:
                print 'Password cannot be blank'
    
        try:
            sample = GCPIMDB(config, user, pw)
        except gdata.client.BadAuthentication:
            print 'Invalid credentials. WTF.'
            return
    
        sample.print_groups()
        gid = sample.new_folder('Hurrah Testing', Folder.CONTACT_t)
        #gid = 'http://www.google.com/m8/feeds/groups/karra.etc%40gmail.com/base/50fccc2a8e0100eb'
        sample.del_folder(gid)
        sample.print_groups()

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
