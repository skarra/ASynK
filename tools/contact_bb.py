##
## Created       : Fri Apr 06 19:08:32 IST 2012
## Last Modified : Sun Apr 08 09:19:16 IST 2012
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


        self.set_db_config(self.get_config().get_db_config(self.get_dbid()))
        self.set_email_domains(self.get_db_config()['email_domains'])

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

    def _snarf_names_from_parse_res (self, pr):
        n = pr['firstname']
        if n:
            self.set_firstname(chompq(n))

        n = pr['lastname']
        if n:
            self.set_lastname(chompq(n))

        # FIXME: Just what the hell is an 'Affix'? Just use the first one and
        # ditch the rest.
        affix = pr['affix']
        if affix:
            self.set_suffix(chompq(affix[0]))

    def _snarf_aka_from_parse_res (self, pr):
        self.add_custom('aka', pr['aka'])

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
        ## FIXME: Need to fix this, for sure. LIke right now.
        pass
