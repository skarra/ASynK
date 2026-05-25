##
## Created : Sun May 25 09:14:00 PDT 2026
## SPDX-FileCopyrightText: 2014-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
## ####
##
## Tests for field preservation during cross-database sync. Verifies the core
## ASynK principle: if a source DB supports a field that the destination DB
## doesn't, that field must not be lost — even when updates from the
## destination are synced back to the source.
##
## Tests cover schema mismatches across Exchange (Graph API), Google Contacts,
## CardDAV, and the abstract Contact base class.
##

import copy, json, os, sys, unittest
from unittest.mock import MagicMock, patch

## Ensure the asynk package is importable
asynk_base = os.path.dirname(os.path.dirname(os.path.dirname(
                 os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(asynk_base, 'asynk'))

from contact import Contact
from contact_ex import EXContact, ASYNK_EXTENSION_NAME


def _make_mock_folder ():
    """Create a minimal mock folder object for constructing contacts."""

    folder = MagicMock()
    folder.get_db.return_value = MagicMock()
    folder.get_dbid.return_value = 'ex'
    folder.get_config.return_value = MagicMock()
    folder.get_itemid.return_value = 'mock_folder_id'
    db = folder.get_db.return_value
    db.get_email_domains.return_value = {}
    db.get_postal_map.return_value = {}
    db.get_notes_map.return_value = None
    db.get_phones_map.return_value = None
    db.get_graph_client.return_value = None
    return folder


def _make_graph_contact (**overrides):
    """Build a typical Graph API contact dict with sensible defaults."""

    gc = {
        'id'                   : 'graph_contact_001',
        'parentFolderId'       : 'parent_folder_001',
        'changeKey'            : 'ck_001',
        'displayName'          : 'Alice Wonderland',
        'givenName'            : 'Alice',
        'surname'              : 'Wonderland',
        'middleName'           : 'Marie',
        'title'                : 'Dr.',
        'generation'           : 'Jr.',
        'nickName'             : 'Ali',
        'fileAs'               : 'Wonderland, Alice',
        'jobTitle'             : 'Software Engineer',
        'companyName'          : 'ACME Corp',
        'department'           : 'Engineering',
        'personalNotes'        : 'Met at PyCon 2025',
        'birthday'             : '1990-03-15',
        'businessHomePage'     : 'https://acme.example.com',
        'emailAddresses'       : [
            {'name': 'Alice W', 'address': 'alice@home.example.com'},
            {'name': 'Alice',   'address': 'alice@acme.example.com'},
        ],
        'homePhones'           : ['+1-555-0101', '+1-555-0102'],
        'businessPhones'       : ['+1-555-0201'],
        'mobilePhone'          : '+1-555-0301',
        'imAddresses'          : ['alice@im.example.com'],
        'homeAddress'          : {
            'street' : '123 Maple St',
            'city'   : 'Springfield',
            'state'  : 'IL',
            'countryOrRegion' : 'US',
            'postalCode' : '62701',
        },
        'businessAddress'      : {
            'street' : '456 Oak Ave',
            'city'   : 'Chicago',
            'state'  : 'IL',
        },
        'createdDateTime'      : '2025-01-15T10:30:00Z',
        'lastModifiedDateTime' : '2026-05-20T14:00:00Z',
        'extensions'           : [],
    }
    gc.update(overrides)
    return gc


def _make_extension_data (**overrides):
    """Build a typical ASynK extension data dict."""

    ext = {
        'extensionName' : ASYNK_EXTENSION_NAME,
        'syncTags'      : {'asynk:profile1:gc': 'gc_remote_id_123'},
        'gender'        : 'Female',
        'anniversary'   : '2015-06-20',
        'alias'         : 'alicew',
        'personalHomePage' : 'https://alice.example.com',
        'faxHome'       : [['HomeFax', '+1-555-9901']],
        'faxWork'       : [['WorkFax', '+1-555-9902']],
        'customData'    : {
            'phones' : {
                'home'  : {'+1-555-0101': 'Home', '+1-555-0102': 'Home2'},
                'work'  : {'+1-555-0201': 'Work'},
                'mob'   : {'+1-555-0301': 'Mobile'},
                'other' : {'+1-555-0401': 'Pager'},
            },
            'ims'    : {'alice@im.example.com': 'Jabber'},
        },
    }
    ext.update(overrides)
    return ext


## ====================================================================
## Test 1: Graph API → ASynK round-trip field preservation
## ====================================================================

class TestGraphToAsynkRoundTrip(unittest.TestCase):
    """Test that reading a Graph contact into ASynK and writing it back
    produces a Graph dict that preserves all data."""

    def setUp (self):
        self.folder = _make_mock_folder()

    def test_basic_fields_round_trip (self):
        """Standard name/org/email fields survive a Graph→ASynK→Graph
        round-trip."""

        gc = _make_graph_contact()
        con = EXContact(self.folder, graph_con=gc)

        ## Verify ASynK props were populated
        self.assertEqual(con.get_firstname(), 'Alice')
        self.assertEqual(con.get_lastname(), 'Wonderland')
        self.assertEqual(con.get_middlename(), 'Marie')
        self.assertEqual(con.get_prefix(), 'Dr.')
        self.assertEqual(con.get_suffix(), 'Jr.')
        self.assertEqual(con.get_nickname(), 'Ali')
        self.assertEqual(con.get_title(), 'Software Engineer')
        self.assertEqual(con.get_company(), 'ACME Corp')
        self.assertEqual(con.get_dept(), 'Engineering')

        ## Convert back
        result = con.to_graph_dict()

        self.assertEqual(result['givenName'], 'Alice')
        self.assertEqual(result['surname'], 'Wonderland')
        self.assertEqual(result['middleName'], 'Marie')
        self.assertEqual(result['title'], 'Dr.')
        self.assertEqual(result['generation'], 'Jr.')
        self.assertEqual(result['nickName'], 'Ali')
        self.assertEqual(result['jobTitle'], 'Software Engineer')
        self.assertEqual(result['companyName'], 'ACME Corp')
        self.assertEqual(result['department'], 'Engineering')

    def test_emails_round_trip (self):
        """All email addresses survive round-trip."""

        gc = _make_graph_contact(emailAddresses=[
            {'name': '', 'address': 'a@home.com'},
            {'name': '', 'address': 'b@work.com'},
            {'name': '', 'address': 'c@other.com'},
            {'name': '', 'address': 'd@extra.com'},
        ])
        con = EXContact(self.folder, graph_con=gc)

        ## With default domain config (empty), all go to email_work
        all_emails = (con.get_email_home() + con.get_email_work() +
                      con.get_email_other())
        self.assertEqual(len(all_emails), 4)

        ## Round-trip back to Graph
        result = con.to_graph_dict()
        self.assertEqual(len(result['emailAddresses']), 4)

    def test_phones_with_labels_round_trip (self):
        """Phone numbers AND their labels survive Graph→ASynK→Graph."""

        ext = _make_extension_data()
        gc = _make_graph_contact(extensions=[ext])
        con = EXContact(self.folder, graph_con=gc)

        ## Verify home phones restored with correct labels
        home_phones = con.get_phone_home()
        self.assertEqual(len(home_phones), 2)
        self.assertEqual(home_phones[0], ('Home', '+1-555-0101'))
        self.assertEqual(home_phones[1], ('Home2', '+1-555-0102'))

        ## Verify other phones (from custom overflow) restored
        other_phones = con.get_phone_other()
        self.assertEqual(len(other_phones), 1)
        self.assertEqual(other_phones[0], ('Pager', '+1-555-0401'))

        ## Verify mobile with label
        mob_phones = con.get_phone_mob()
        self.assertEqual(len(mob_phones), 1)
        self.assertEqual(mob_phones[0], ('Mobile', '+1-555-0301'))

    def test_postal_address_round_trip (self):
        """Postal addresses survive Graph→ASynK→Graph."""

        gc = _make_graph_contact()
        con = EXContact(self.folder, graph_con=gc)

        ## Verify home address was read
        home_postal = con.get_postal('home')
        self.assertIsNotNone(home_postal)
        self.assertEqual(len(home_postal), 1)
        label, addr = home_postal[0]
        self.assertEqual(addr['street'], '123 Maple St')
        self.assertEqual(addr['city'], 'Springfield')

        ## Round-trip
        result = con.to_graph_dict()
        self.assertIn('homeAddress', result)
        self.assertEqual(result['homeAddress']['street'], '123 Maple St')
        self.assertEqual(result['homeAddress']['city'], 'Springfield')

        self.assertIn('businessAddress', result)
        self.assertEqual(result['businessAddress']['street'], '456 Oak Ave')

    def test_notes_round_trip (self):
        """Notes survive round-trip."""

        gc = _make_graph_contact(personalNotes='Important meeting notes')
        con = EXContact(self.folder, graph_con=gc)

        self.assertEqual(con.get_notes(), ['Important meeting notes'])

        result = con.to_graph_dict()
        self.assertEqual(result['personalNotes'], 'Important meeting notes')


## ====================================================================
## Test 2: Fields only in Exchange (no Graph native property)
## ====================================================================

class TestFieldsWithNoNativeGraphProperty(unittest.TestCase):
    """Test that fields stored in Open Extension survive round-trips:
    gender, anniversary, alias, personal homepage, faxes."""

    def setUp (self):
        self.folder = _make_mock_folder()

    def test_gender_preserved_via_extension (self):
        """Gender has no native Graph field — it goes into the extension."""

        ext = _make_extension_data(gender='Male')
        gc = _make_graph_contact(extensions=[ext])
        con = EXContact(self.folder, graph_con=gc)

        self.assertEqual(con.get_gender(), 'Male')

        ## Verify it would be in extension data
        ext_data = con.get_extension_data()
        self.assertEqual(ext_data['gender'], 'Male')

    def test_anniversary_preserved_via_extension (self):
        """Anniversary has no native Graph field — extension."""

        ext = _make_extension_data(anniversary='2020-12-25')
        gc = _make_graph_contact(extensions=[ext])
        con = EXContact(self.folder, graph_con=gc)

        self.assertEqual(con.get_anniv(), '2020-12-25')

        ext_data = con.get_extension_data()
        self.assertEqual(ext_data['anniversary'], '2020-12-25')

    def test_alias_preserved_via_extension (self):
        """Alias stored in custom dict, persisted via extension."""

        ext = _make_extension_data(alias='alicew')
        gc = _make_graph_contact(extensions=[ext])
        con = EXContact(self.folder, graph_con=gc)

        self.assertEqual(con.get_custom('alias'), 'alicew')

    def test_personal_homepage_preserved_via_extension (self):
        """Personal homepage has no native Graph field (only business
        homepage exists). It goes into the extension."""

        ext = _make_extension_data(personalHomePage='https://alice.blog.com')
        gc = _make_graph_contact(extensions=[ext])
        con = EXContact(self.folder, graph_con=gc)

        web_home = con.get_web_home()
        self.assertIn('https://alice.blog.com', web_home)

        ext_data = con.get_extension_data()
        self.assertEqual(ext_data['personalHomePage'], 'https://alice.blog.com')

    def test_faxes_preserved_via_extension (self):
        """Faxes have no native Graph field — entirely extension-based."""

        ext = _make_extension_data(
            faxHome=[['HomeFax', '+1-555-FAX1']],
            faxWork=[['WorkFax', '+1-555-FAX2']])
        gc = _make_graph_contact(extensions=[ext])
        con = EXContact(self.folder, graph_con=gc)

        fh = con.get_fax_home()
        self.assertEqual(len(fh), 1)
        self.assertEqual(fh[0], ('HomeFax', '+1-555-FAX1'))

        fw = con.get_fax_work()
        self.assertEqual(len(fw), 1)
        self.assertEqual(fw[0], ('WorkFax', '+1-555-FAX2'))

        ## Verify extension output
        ext_data = con.get_extension_data()
        self.assertEqual(len(ext_data['faxHome']), 1)
        self.assertEqual(len(ext_data['faxWork']), 1)


## ====================================================================
## Test 3: Schema mismatch — fields from other DBs that Exchange
## doesn't natively support
## ====================================================================

class TestSchemaMismatchOtherToExchange(unittest.TestCase):
    """Simulate syncing contacts from Google Contacts or CardDAV to
    Exchange. Some fields the source supports don't have native Graph
    API properties — they must be preserved in the Exchange Open
    Extension and survive a round-trip back."""

    def setUp (self):
        self.folder = _make_mock_folder()

    def test_gc_gender_to_ex_round_trip (self):
        """Google Contacts supports gender natively. Exchange doesn't.
        Syncing GC→EX→GC must preserve gender."""

        ## Simulate a contact coming from Google Contacts with gender
        source_con = self._make_source_contact()
        source_con.set_gender('Female')

        ## "Sync" to Exchange by creating an EXContact from the source
        exc = EXContact(self.folder, con=source_con)

        ## Verify gender is preserved
        self.assertEqual(exc.get_gender(), 'Female')

        ## Get extension data (what would be written to Exchange)
        ext_data = exc.get_extension_data()
        self.assertIn('gender', ext_data)
        self.assertEqual(ext_data['gender'], 'Female')

        ## Simulate reading it back from Exchange
        gc = _make_graph_contact(
            givenName='Test',
            surname='User',
            extensions=[{
                'extensionName': ASYNK_EXTENSION_NAME,
                'gender': 'Female',
            }],
        )
        exc2 = EXContact(self.folder, graph_con=gc)

        ## Gender should survive the round-trip
        self.assertEqual(exc2.get_gender(), 'Female')

    def test_multiple_notes_preservation (self):
        """If a source contact has multiple notes (e.g., BBDB supports this),
        Exchange stores only one in personalNotes. The rest must not be lost."""

        source_con = self._make_source_contact()
        source_con.add_notes('First note')
        source_con.add_notes('Second note')
        source_con.add_notes('Third note')

        exc = EXContact(self.folder, con=source_con)

        ## All notes should be in ASynK props
        self.assertEqual(len(exc.get_notes()), 3)

        ## But only one goes into Graph dict
        graph_dict = exc.to_graph_dict()
        self.assertEqual(graph_dict['personalNotes'], 'First note')

        ## The others are still in get_notes() for potential custom stashing

    def test_many_phones_overflow_preservation (self):
        """Source DB has 5 home phones. Graph only supports an array of
        homePhones but preserves labels in custom overflow."""

        source_con = self._make_source_contact()
        source_con.add_phone_home(('Landline', '+1-111-1111'))
        source_con.add_phone_home(('Home Office', '+1-111-2222'))
        source_con.add_phone_home(('Kitchen', '+1-111-3333'))
        source_con.add_phone_home(('Bedroom', '+1-111-4444'))
        source_con.add_phone_home(('Garage', '+1-111-5555'))
        source_con.add_phone_other(('Pager', '+1-999-0000'))

        exc = EXContact(self.folder, con=source_con)

        ## All 5 home phones should be preserved in ASynK props
        self.assertEqual(len(exc.get_phone_home()), 5)

        ## Graph dict should have all numbers in homePhones
        graph_dict = exc.to_graph_dict()
        self.assertEqual(len(graph_dict['homePhones']), 5)

        ## Labels should be in custom overflow
        ext_data = exc.get_extension_data()
        phones = ext_data.get('customData', {}).get('phones', {})
        self.assertEqual(phones['home']['+1-111-1111'], 'Landline')
        self.assertEqual(phones['home']['+1-111-5555'], 'Garage')
        self.assertEqual(phones['other']['+1-999-0000'], 'Pager')

    def test_many_websites_overflow_preservation (self):
        """Source has 3 work URLs. Graph only has 1 businessHomePage.
        Extras must be preserved."""

        source_con = self._make_source_contact()
        source_con.add_web_work('https://primary.example.com')
        source_con.add_web_work('https://secondary.example.com')
        source_con.add_web_work('https://tertiary.example.com')
        source_con.add_web_home('https://personal.example.com')

        exc = EXContact(self.folder, con=source_con)

        ## All URLs should be in ASynK props
        self.assertEqual(len(exc.get_web_work()), 3)
        self.assertEqual(len(exc.get_web_home()), 1)

        ## Graph dict should have one businessHomePage
        graph_dict = exc.to_graph_dict()
        self.assertEqual(graph_dict['businessHomePage'],
                         'https://primary.example.com')

        ## Extras should be in custom overflow
        ext_data = exc.get_extension_data()
        custom = ext_data.get('customData', {})
        self.assertIn('webs', custom)
        self.assertIn('https://secondary.example.com', custom['webs']['work'])

        ## Personal homepage should be in extension
        self.assertEqual(ext_data['personalHomePage'],
                         'https://personal.example.com')

    def test_anniversary_from_source (self):
        """Source DB has anniversary. Exchange stores in extension."""

        source_con = self._make_source_contact()
        source_con.set_anniv('2018-09-15')

        exc = EXContact(self.folder, con=source_con)
        self.assertEqual(exc.get_anniv(), '2018-09-15')

        ext_data = exc.get_extension_data()
        self.assertEqual(ext_data['anniversary'], '2018-09-15')

    def test_faxes_from_source (self):
        """Source DB has fax numbers. Exchange has no native fax field."""

        source_con = self._make_source_contact()
        source_con.add_fax_home(('HomeFax', '+1-555-FAX1'))
        source_con.add_fax_work(('WorkFax', '+1-555-FAX2'))

        exc = EXContact(self.folder, con=source_con)
        self.assertEqual(len(exc.get_fax_home()), 1)
        self.assertEqual(len(exc.get_fax_work()), 1)

        ext_data = exc.get_extension_data()
        self.assertEqual(ext_data['faxHome'], [('HomeFax', '+1-555-FAX1')])
        self.assertEqual(ext_data['faxWork'], [('WorkFax', '+1-555-FAX2')])

    def _make_source_contact (self):
        """Create a minimal Contact-like object to simulate a source contact
        from another DB (GC, CD, BB)."""

        folder = _make_mock_folder()
        folder.get_dbid.return_value = 'gc'

        ## We need a concrete Contact subclass. EXContact will serve
        ## since the base Contact is abstract. We pass con=None.
        con = EXContact(folder)
        con.set_firstname('Test')
        con.set_lastname('User')
        return con


## ====================================================================
## Test 4: Bidirectional sync — Exchange writes back to source
## ====================================================================

class TestBidirectionalSyncPreservation(unittest.TestCase):
    """The critical scenario: contact is synced from Source→Exchange,
    then modified in Exchange (only some fields changed), then synced
    back Exchange→Source. The source fields that Exchange doesn't
    natively support must NOT be lost."""

    def setUp (self):
        self.folder = _make_mock_folder()

    def test_modify_in_exchange_preserves_source_fields (self):
        """
        Scenario:
        1. Source contact has: gender, anniversary, 5 phone numbers, faxes
        2. Synced to Exchange (stored as native fields + extension)
        3. User edits displayName in Exchange (Outlook)
        4. Contact synced back to source
        5. All original fields must survive
        """

        ## Step 1: Create source contact with rich data
        source = self._make_rich_source_contact()

        ## Step 2: Sync to Exchange
        exc = EXContact(self.folder, con=source)
        graph_dict = exc.to_graph_dict()
        ext_data = exc.get_extension_data()

        ## Step 3: Simulate user editing in Exchange (changed display name)
        graph_dict['displayName'] = 'Alice M. Wonderland-Updated'
        graph_dict['givenName'] = 'Alice-Updated'

        ## The extension data would still be there from the server
        ext_for_read = dict(ext_data)
        ext_for_read['extensionName'] = ASYNK_EXTENSION_NAME
        graph_dict['extensions'] = [ext_for_read]

        ## Step 4: Read back from Exchange
        exc2 = EXContact(self.folder, graph_con=graph_dict)

        ## Step 5: Verify ALL fields survive
        self.assertEqual(exc2.get_firstname(), 'Alice-Updated')   # changed
        self.assertEqual(exc2.get_lastname(), 'Wonderland')        # unchanged
        self.assertEqual(exc2.get_gender(), 'Female')              # from ext
        self.assertEqual(exc2.get_anniv(), '2015-06-20')           # from ext

        ## Phone labels preserved
        home_phones = exc2.get_phone_home()
        self.assertTrue(len(home_phones) >= 2)

        ## Faxes preserved
        fax_home = exc2.get_fax_home()
        self.assertEqual(len(fax_home), 1)
        self.assertEqual(fax_home[0][1], '+1-555-FAX1')

        ## Sync tags preserved
        stags = exc2.get_sync_tags()
        self.assertIn('asynk:profile1:gc', stags)

    def test_copy_constructor_preserves_all_props (self):
        """The Contact copy constructor (con= arg) must deep-copy ALL
        properties, including custom overflow data."""

        source = self._make_rich_source_contact()

        ## Copy via the con= constructor
        copy_con = EXContact(self.folder, con=source)

        ## Verify all fields are present
        self.assertEqual(copy_con.get_firstname(), source.get_firstname())
        self.assertEqual(copy_con.get_lastname(), source.get_lastname())
        self.assertEqual(copy_con.get_gender(), source.get_gender())
        self.assertEqual(copy_con.get_anniv(), source.get_anniv())
        self.assertEqual(copy_con.get_phone_home(), source.get_phone_home())
        self.assertEqual(copy_con.get_fax_home(), source.get_fax_home())
        self.assertEqual(copy_con.get_fax_work(), source.get_fax_work())

        ## Verify deep copy (modifying copy doesn't affect source)
        copy_con.set_firstname('Modified')
        self.assertNotEqual(copy_con.get_firstname(), source.get_firstname())

    def _make_rich_source_contact (self):
        """Create a contact with many fields to test preservation."""

        folder = _make_mock_folder()
        folder.get_dbid.return_value = 'gc'
        con = EXContact(folder)

        con.set_firstname('Alice')
        con.set_lastname('Wonderland')
        con.set_middlename('Marie')
        con.set_gender('Female')
        con.set_anniv('2015-06-20')
        con.set_birthday('1990-03-15')
        con.set_title('Engineer')
        con.set_company('ACME')
        con.set_dept('R&D')
        con.add_phone_home(('Home', '+1-555-0101'))
        con.add_phone_home(('Home2', '+1-555-0102'))
        con.add_phone_work(('Work', '+1-555-0201'))
        con.add_phone_mob(('Mobile', '+1-555-0301'))
        con.add_fax_home(('HomeFax', '+1-555-FAX1'))
        con.add_fax_work(('WorkFax', '+1-555-FAX2'))
        con.add_web_home('https://alice.example.com')
        con.add_web_work('https://acme.example.com')
        con.add_email_home('alice@home.com')
        con.add_email_work('alice@work.com')
        con.add_im('Jabber', 'alice@im.com')
        con.update_sync_tags('asynk:profile1:gc', 'gc_id_123')

        return con


## ====================================================================
## Test 5: Empty/None field handling
## ====================================================================

class TestEmptyFieldHandling(unittest.TestCase):
    """Test that None and empty values are handled gracefully."""

    def setUp (self):
        self.folder = _make_mock_folder()

    def test_graph_contact_with_minimal_fields (self):
        """A Graph contact with only id and displayName should not crash."""

        gc = {
            'id'          : 'minimal_001',
            'displayName' : 'Just A Name',
            'extensions'  : [],
        }
        con = EXContact(self.folder, graph_con=gc)
        self.assertEqual(con.get_itemid(), 'minimal_001')
        self.assertIsNotNone(con.get_name())

        ## to_graph_dict should work without errors
        result = con.to_graph_dict()
        self.assertIsNotNone(result)

    def test_empty_extension (self):
        """Contact with no extension data should work fine."""

        gc = _make_graph_contact(extensions=[])
        con = EXContact(self.folder, graph_con=gc)

        ## Sync tags should be empty
        self.assertEqual(con.get_sync_tags(), {})

    def test_empty_phones_and_emails (self):
        """Contact with no phones or emails should produce clean dicts."""

        gc = {
            'id'          : 'nophone_001',
            'displayName' : 'No Phone',
            'extensions'  : [],
        }
        con = EXContact(self.folder, graph_con=gc)

        result = con.to_graph_dict()
        self.assertNotIn('homePhones', result)
        self.assertNotIn('businessPhones', result)
        self.assertNotIn('mobilePhone', result)
        self.assertNotIn('emailAddresses', result)


## ====================================================================
## Test 6: Extension data integrity
## ====================================================================

class TestExtensionDataIntegrity(unittest.TestCase):
    """Test that the extension data round-trips correctly."""

    def setUp (self):
        self.folder = _make_mock_folder()

    def test_sync_tags_in_extension (self):
        """Sync tags are stored in the Open Extension and survive."""

        ext = {
            'extensionName' : ASYNK_EXTENSION_NAME,
            'syncTags'      : {
                'asynk:p1:gc': 'gc_id_001',
                'asynk:p1:cd': 'cd_id_002',
                'asynk:p2:bb': 'bb_id_003',
            },
        }
        gc = _make_graph_contact(extensions=[ext])
        con = EXContact(self.folder, graph_con=gc)

        tags = con.get_sync_tags()
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags['asynk:p1:gc'], 'gc_id_001')
        self.assertEqual(tags['asynk:p1:cd'], 'cd_id_002')
        self.assertEqual(tags['asynk:p2:bb'], 'bb_id_003')

        ## Write back
        ext_data = con.get_extension_data()
        self.assertEqual(ext_data['syncTags']['asynk:p1:gc'], 'gc_id_001')

    def test_custom_data_in_extension (self):
        """Arbitrary custom data survives via the extension."""

        ext = {
            'extensionName' : ASYNK_EXTENSION_NAME,
            'customData'    : {
                'bbdb_field1' : 'value1',
                'bbdb_field2' : ['a', 'b', 'c'],
            },
        }
        gc = _make_graph_contact(extensions=[ext])
        con = EXContact(self.folder, graph_con=gc)

        ## Custom data should be accessible
        self.assertEqual(con.get_custom('bbdb_field1'), 'value1')
        self.assertEqual(con.get_custom('bbdb_field2'), ['a', 'b', 'c'])

        ## And it goes back into the extension
        ext_data = con.get_extension_data()
        custom = ext_data['customData']
        self.assertEqual(custom['bbdb_field1'], 'value1')


## ====================================================================
## Test 7: IM address handling
## ====================================================================

class TestIMAddressHandling(unittest.TestCase):
    """Test IM address field preservation with labels."""

    def setUp (self):
        self.folder = _make_mock_folder()

    def test_ims_with_labels_round_trip (self):
        """IM addresses + their labels survive round-trip."""

        ext = {
            'extensionName' : ASYNK_EXTENSION_NAME,
            'customData'    : {
                'ims': {
                    'alice@jabber.org' : 'Jabber',
                    'alice@skype.com'  : 'Skype',
                },
            },
        }
        gc = _make_graph_contact(
            imAddresses=['alice@jabber.org', 'alice@skype.com'],
            extensions=[ext])

        con = EXContact(self.folder, graph_con=gc)

        ims = con.get_im()
        self.assertEqual(len(ims), 2)
        self.assertIn('Jabber', ims)
        self.assertIn('Skype', ims)
        self.assertEqual(ims['Jabber'], 'alice@jabber.org')
        self.assertEqual(ims['Skype'], 'alice@skype.com')

        ## Primary should be first one
        self.assertEqual(con.get_im_prim(), 'Jabber')

    def test_ims_without_labels (self):
        """IM addresses without label data get default labels."""

        gc = _make_graph_contact(
            imAddresses=['user@example.com', 'user2@example.com'],
            extensions=[])

        con = EXContact(self.folder, graph_con=gc)

        ims = con.get_im()
        self.assertEqual(len(ims), 2)
        ## Default labels should be ImAddress1, ImAddress2
        self.assertIn('ImAddress1', ims)
        self.assertIn('ImAddress2', ims)


if __name__ == '__main__':
    unittest.main()
