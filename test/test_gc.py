import getopt, logging, os, sys, traceback

CUR_DIR           = os.path.abspath('')
ASYNK_BASE_DIR    = os.path.abspath('..')

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath('../')
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'asynk')]
sys.path = EXTRA_PATHS + sys.path

from state         import Config
import gdata, gdata.data, gdata.contacts.data, gdata.contacts.client
from   pimdb_gc   import GCPIMDB
from   contact_gc import GCContact
from   folder_gc  import BatchState
import utils
import xml.etree.ElementTree as ET

def main ():
    tests = TestGCContact()

    tests.test_batch_error()
    # tests.test_print_item('https://www.google.com/m8/feeds/contacts/karra.etc%40gmail.com/full/5e6d5ad30b0e2008')
    # tests.test_find_item('https://www.google.com/m8/feeds/contacts/karra.etc%40gmail.com/full/4b814c4c8f0c1558')
    #tests.test_sync_status()
    #tests.test_del_item('http://www.google.com/m8/feeds/contacts/karra.etc%40gmail.com/base/1fabc8309273c15')
    # tests.test_del_item('http://www.google.com/m8/feeds/contacts/karra.etc%40gmail.com/base/1fabc8309273c15')

class TestGCContact:
    def __init__ (self):
        self.conf = Config(asynk_base_dir=ASYNK_BASE_DIR, user_dir='./')

        # The following is the 'Gout' group on karra.etc@gmail.com
        # self.gid = 'http://www.google.com/m8/feeds/groups/karra.etc%40gmail.com/base/41baff770f898d85'
        # self.gid =
        # 'http://www.google.com/m8/feeds/groups/karra.etc%40gmail.com/base/6'
        self.gid = 'http://www.google.com/m8/feeds/groups/karra.etc%40gmail.com/base/204eb63b8e2dad8d'

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
            self.pimdb = GCPIMDB(self.conf, user, pw)
        except gdata.client.BadAuthentication:
            print 'Invalid credentials. WTF.'
            raise

    def test_batch_error (self):
        fobj = self.find_group(self.gid)

        con0 = GCContact(fobj)
        con0.set_firstname('Namo Narayananaya')
        gce0 = con0.get_gce()

        con = GCContact(fobj)
        con.set_firstname('Ayeshwarya')
        con.set_birthday('abcd"ef')
        # con.set_anniv('1978-05-31 %s est n il y a %d ans')
        # con.set_birthday('1980-08-10')
        gce = con.get_gce()

        feed = self.pimdb.new_feed()
        feed.add_insert(entry=gce0, batch_id_string="DeadBeef")
        feed.add_insert(entry=gce0, batch_id_string="DeadBeef")
        feed.add_insert(entry=gce, batch_id_string="DeadBeef")

        b = BatchState(1, feed, op='insert', sync_tag="asynk:testgcex:ex")

        print 'Request: ', utils.pretty_xml(str(feed))
        rr = self.pimdb.exec_batch(feed)
        print 'Response: ', utils.pretty_xml(str(rr))

        for entry in rr.entry:
            print entry.batch_status
            if entry.batch_status:
                print 'Code: ',entry.batch_status.code
                print 'Reason: ', entry.batch_status.reason
            else:
                self.handle_interrupted_feed(feed, str(rr))

    def handle_interrupted_feed (self, feed, resp_xml):
        resp = ET.fromstring(resp_xml)
        ffc = utils.find_first_child

        resp_title = ffc(resp, utils.QName_GNS0('title'), ret='node').text
        resp_intr  = ffc(resp, utils.QName_GNS3('interrupted'), ret='node')

        parsed = int(resp_intr.attrib['parsed'])
        reason = resp_intr.attrib['reason']

        entry = feed.entry[parsed]
        logging.error('The server encountered a %s while processing ' +
                      'the feed. The reason given is: %s', resp_title,
                      resp_intr)
        logging.error('The problematic entry is likely this one: %s',
                      utils.pretty_xml(str(entry)))

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
