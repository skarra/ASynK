##
## Created       : Fri Apr 06 19:08:32 IST 2012
## Last Modified : Sun Apr 08 14:46:15 IST 2012
##
## Copyright (C) 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
##
## This file defines a wrapper class around a BBDB Contact entry, by extending
## the Contact abstract base Contact class. BBDB is, of course, the Insidious
## Big Brother Data Base
##

import logging, re
from   contact    import Contact
from   utils      import chompq
import folder_bb

class BBContact(Contact):
    """This class extends the Contact abstract base class to wrap a BBDB
    Contact"""

    def __init__ (self, folder, con=None, rec=None):
        """rec is the native string vector representation of a BBDB contact
        entry on disk."""

        Contact.__init__(self, folder, con)

        if rec:
            self.set_rec(rec)
            self.init_props_from_rec(rec)

    ##
    ## First the inherited abstract methods from the base classes
    ##

    def save (self):
        raise NotImplementedError

    ##
    ## Overridden methods
    ##

    def get_name (self):
        ret = self._get_prop('name')
        if ret:
            return ret

        ret = ''
        fn = self.get_firstname()
        if fn:
            ret += (fn + ' ')

        ln = self.get_lastname()
        if ln:
            ret += ln

        return ret

    ##
    ## Now onto the non-abstract methods.
    ##

    def get_rec (self):
        return self._get_att('rec')

    def set_rec (self, rec):
        return self._set_att('rec', rec)

    def init_props_from_rec (self, rec):
        con_re = self.get_db().get_con_re()
        parse_res = re.search(con_re, rec)

        if not parse_res:
            logging.critical('Could not Parse BBDB contact entry: %s', rec)
            logging.critical('Cannnot do anything with this chap...')

            return

        d = parse_res.groupdict()
        self._snarf_names_from_parse_res(d)
        self._snarf_aka_from_parse_res(d)
        self._snarf_company_from_parse_res(d)
        self._snarf_emails_from_parse_res(d)
        self._snarf_postal_from_parse_res(d)
        self._snarf_phones_from_parse_res(d)
        self._snarf_notes_from_parse_res(d)

    def _snarf_names_from_parse_res (self, pr):
        n = pr['firstname']
        if n:
            self.set_firstname(chompq(n))

        n = pr['lastname']
        if n:
            if n != 'nil':
                self.set_lastname(chompq(n))

        # FIXME: Just what the hell is an 'Affix'? Just use the first one and
        # ditch the rest.
        affix = pr['affix']
        if affix:
            self.set_suffix(chompq(affix[0]))

    def _snarf_aka_from_parse_res (self, pr):
        aka = pr['aka']
        if aka:
            str_re = self.get_db().get_str_re()
            aka    = re.findall(str_re, aka)
            nick   = aka[0]
            rest   = aka[1:]
            if nick:
                self.set_nickname(chompq(nick))

            if rest:
                self.add_custom('aka', rest)

    def _snarf_company_from_parse_res (self, pr):
        cs = pr['company']

        if cs:
            ## The first company goes into the Company field, the rest we will
            ## push into the custom field
            str_re = self.get_db().get_str_re()
            cs = re.findall(str_re, cs)
            self.set_company(chompq(cs[0]))
            self.add_custom('company', cs[1:])

    def _snarf_emails_from_parse_res (self, pr):
        ems = pr['emails']

        if ems:
            str_re = self.get_db().get_str_re()
            ems = re.findall(str_re, ems)
            ems = [chompq(x) for x in ems]

            domains = self.get_email_domains()

            for em in ems:
                home, work, other = self._classify_email_addr(em, domains)

                ## Note that the following implementation means if the same
                ## domain is specified in more than one category, it ends up
                ## being copied to every category. In effect this means when
                ## this is synched to google contacts, say, the GC entry will
                ## have the same email address twice for the record

                if home:
                    self.add_email_home(em)
                elif work:
                    self.add_email_work(em)
                elif other:
                    self.add_email_other(em)
                else:
                    self.add_email_work(em)

    def _classify_email_addr (self, addr, domains):
        """Return a tuple of (home, work, other) booleans classifying if the
        specified address falls within one of the domains."""

        res = {'home' : False, 'work' : False, 'other' : False}

        for cat in res.keys():
            try:
                for domain in domains[cat]:
                    if re.search((domain + '$'), addr):
                        res[cat] = True
            except KeyError, e:
                logging.warning('Invalid email_domains specification.')

        return (res['home'], res['work'], res['other'])

    def _snarf_postal_from_parse_res (self, pr):
        adr_re = self.get_db().get_adr_re()
        str_re = self.get_db().get_str_re()
        addrs  = re.findall(adr_re, pr['addrs'])

        for addr in addrs:
            label, val = addr[:2]
            add = '[' + label + ' ' + val + ']'
            res = re.search(adr_re, add)

            if res:
                addict = {}
                fields = res.groupdict()

                streets = fields['streets']
                sts = re.findall(str_re, streets)
                sts = [chompq(x) for x in sts]

                if sts:
                    addict.update({'street' : '\n'.join(sts)})

                city = fields['city']
                if city:
                    addict.update({'city' : chompq(city)})

                state = fields['state']
                if state:
                    addict.update({'state' : chompq(state)})

                country = fields['country']
                if country:
                    addict.update({'country' : chompq(country)})

                pin = fields['zip']
                if pin:
                    addict.update({'zip' : chompq(pin)})

                self.add_postal(chompq(label), addict)
            else:
                logging.error('bb:snarf_postal(): Huh? No match for add %s.',
                              add)

    def _snarf_phones_from_parse_res (self, pr):
        ## FIXME: Need to fix this, for sure. LIke right now.
        pass

    def _snarf_notes_from_parse_res (self, pr):
        noted = self.get_notes_map()
        if not noted:
            logging.error('Error in Config file. No notes_map field for bb')
            return

        note_re = self.get_db().get_note_re()
        notes = re.findall(note_re, pr['notes'])
        custom = {}

        for note in notes:
            (key, val) = note[:2]

            key = key.rstrip()
            val = chompq(val)

            if key == noted['created']:
                self.set_created(val)
            elif key == noted['updated']:
                self.set_updated(val)
            elif key == noted['itemid']:
                self.set_itemid(val)
            elif key == noted['prefix']:
                self.set_prefix(val)
            elif key == noted['gender']:
                self.set_gender(val)
            elif key == noted['title']:
                self.set_title(val)
            elif key == noted['dept']:
                self.set_dept(val)
            elif key == noted['ims']:
                logging.info('IMs not supported in this version.')
            elif key == noted['notes']:
                self.add_notes(val)
            elif key == noted['birthday']:
                if self._is_valid_date(val):
                    self.set_birthday(val)
            elif key == noted['anniv']:
                if self._is_valid_date(val):
                    self.set_anniv(val)
            else:
                ## The rest of the stuff go into the 'Custom' field...
                custom.update({key : val})

        if len(custom.keys()) > 0:
            self.add_custom('notes', custom)

    def _is_valid_date (self, date, label):
        res = re.search('\d\d\d\d-(\d\d)-(\d\d)', date)
        if not res:
            logging.error(('%s for %s should be yyyy-mm-dd ' +
                           'format. Actual value: %s'),
                           label, self.get_name(), date)
            return False
        elif int(res.group(1)) > 12:
            logging.error('Invalid month (%d) in %s for %s',
                          int(res.group(1)), label, self.get_name())
            return False
        else:
            ## We should really check the date for validity as well, oh, well,
            ## later. FIXME
            return True
