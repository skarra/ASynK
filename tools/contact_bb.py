##
## Created       : Fri Apr 06 19:08:32 IST 2012
## Last Modified : Tue Apr 10 13:26:39 IST 2012
##
## Copyright (C) 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
##
## This file defines a wrapper class around a BBDB Contact entry, by extending
## the Contact abstract base Contact class. BBDB is, of course, the Insidious
## Big Brother Data Base
##

import copy, logging, re, uuid
from   contact    import Contact
from   utils      import chompq, unchompq
import folder_bb, utils

class BBContact(Contact):
    """This class extends the Contact abstract base class to wrap a BBDB
    Contact"""

    def __init__ (self, folder, con=None, rec=None):
        """rec is the native string vector representation of a BBDB contact
        entry on disk."""

        Contact.__init__(self, folder, con)

        ## Sometimes we might be creating a contact object from a Google
        ## contact object or other entry which might have the ID in its sync
        ## tags field. if that is present, we should use it to initialize the
        ## itemid field for the current object

        if con:
            try:
                label = utils.get_sync_label_from_dbid(self.get_config(),
                                                       self.get_dbid())
                itemid = con.get_sync_tags(label)
                self.set_itemid(itemid)
            except Exception, e:
                pass

        if rec:
            self.set_rec(rec)
            self.init_props_from_rec(rec)
            if not self.get_itemid():
                iid = uuid.uuid1()
                logging.info('bbdbid not found for %s. Assigning %s',
                             self.get_name(), iid)
                self.set_itemid(iid)

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
            return

        d = parse_res.groupdict()
        self._snarf_names_from_parse_res(d)
        self._snarf_aka_from_parse_res(d)
        self._snarf_company_from_parse_res(d)
        self._snarf_emails_from_parse_res(d)
        self._snarf_postal_from_parse_res(d)
        self._snarf_phones_from_parse_res(d)
        self._snarf_notes_from_parse_res(d)

    def init_rec_from_props (self):
        rec = '['
        rec += self._get_names_as_string()   + ' '
        rec += self._get_aka_as_string()     + ' '
        rec += self._get_company_as_string() + ' '
        rec += self._get_phones_as_string()  + ' '
        rec += self._get_postal_as_string()  + ' '
        rec += self._get_emails_as_string()  + ' '
        rec += self._get_notes_as_string()
        rec += ' nil]'

        return rec

    def _snarf_names_from_parse_res (self, pr):
        n = pr['firstname']
        if n and n != 'nil':
            self.set_firstname(chompq(n))

        n = pr['lastname']
        if n and n != 'nil':
            self.set_lastname(chompq(n))

        # FIXME: Just what the hell is an 'Affix'? Just use the first one and
        # ditch the rest.
        affix = pr['affix']
        if affix and affix != 'nil':
            self.set_suffix(chompq(affix[0]))

    def _snarf_aka_from_parse_res (self, pr):
        aka = pr['aka']
        if aka and aka != 'nil':
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

        if cs and cs != 'nil':
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
        ph_re = self.get_db().get_ph_re()
        phs   = re.findall(ph_re, pr['phones']) if pr['phones'] else None

        if phs:
            for ph in phs:
                res = re.search(ph_re, '[' + ph[0] + ']')

                if res:
                    resg = res.groupdict()

                    if resg['structured']:
                        phnum = '+1 ' + resg['structured']
                    else:
                        phnum = chompq(resg['unstructured'])

                    label = chompq(resg['phlabel'])
                    self._classify_and_add_phone(label, (label, phnum))
                else:
                    logging.debug('Could not parse phone: %s', ph[0])

    def _classify_and_add_phone (self, label, num):
        nmap = self.get_phones_map()

        if not nmap:
            logging.error('Mapping of phone labels is not in Config. ' +
                          'Adding phone %s as Home phone')
            self.add_phone_home(num)
            return

        if re.search(nmap['phone_home'], label):
            self.add_phone_home(num)
        elif re.search(nmap['phone_work'], label):
            self.add_phone_work(num)
        elif re.search(nmap['phone_mob'], label):
            self.add_phone_mob(num)
        elif re.search(nmap['fax_home'], label):
            self.add_fax_home(num)
        elif re.search(nmap['fax_work'], label):
            self.add_fax_work(num)
        elif re.search(nmap['fax_other'], label):
            self.add_fax_other(num)
        else:
            self.add_phone_other(num)

    def _snarf_notes_from_parse_res (self, pr):
        """Parse the BBDB Notes entry; this contains most of the good
        stuff... including sync tags and stuff."""

        noted = self.get_notes_map()
        if not noted:
            logging.error('Error in Config file. No notes_map field for bb')
            return

        stag_re = self.get_db().get_sync_tag_re()
        note_re = self.get_db().get_note_re()
        notes = re.findall(note_re, pr['notes'])
        custom = {}

        # logging.debug('bb:snfpr:stag_re: %s', stag_re)
        # keys = [note[0] for note in notes]
        # logging.debug('bb:snfpr:Keys: %s', keys)

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
            elif re.search(stag_re, key):
                self.update_sync_tags(key.rstrip(), val)
            elif re.search(noted['web_home_re'], key):
                self.add_web_home(val)
            elif re.search(noted['web_work_re'], key):
                self.add_web_work(val)
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

    def _get_names_as_string (self):
        ret = ''
        n = self.get_firstname()
        l = self.get_lastname()

        if (not l) and (not n):
            n = self.get_name()
            if n:
                ret = '"%s" nil' % n
            else:
                ret = 'nil nil'
        else:
            if n:
                ret += unchompq(n) + ' '
            else:
                ret += 'nil '

            if l:
                ret += unchompq(l) + ' '
            else:
                ret += 'nil '

        a = self.get_suffix()
        if a:
            ret += ' ' + unchompq(a)
        else:
            ret += 'nil'

        return ret

    def _get_aka_as_string (self):
        nick = self.get_nickname()
        if not nick:
            return 'nil'

        aka = copy.deepcopy(self.get_custom('aka'))
        if aka:
            aka.insert(0, unchompq(nick))
            return('(' + ' '.join(aka) + ')')
        else:
            return '(' + nick + ')'

    def _get_company_as_string (self):
        comp1 = self.get_company()
        if not comp1:
            return 'nil'

        comp = copy.deepcopy(self.get_custom('company'))
        comp.insert(0, unchompq(comp1))
        return ('(' + ' '.join(comp) + ')')

    def _get_emails_as_string (self):
        ems = [unchompq(e) for e in self.get_email_home()]
        ems.extend([unchompq(e) for e in self.get_email_work()])
        ems.extend([unchompq(e) for e in self.get_email_other()])

        ret = ' '.join(ems)

        if ret == '':
            return 'nil'
        else:
            return '(' + ret + ')'

    def _get_phones_as_string (self):
        ## Note that any BBDB phone number that was structured in the North
        ## Amerial format will be munged into an equivalent string notation
        ## for our convenience

        ph  = self.get_phone_home()
        ph.extend(self.get_phone_work())
        ph.extend(self.get_phone_mob())
        ph.extend(self.get_phone_other())

        phs = ['[%s %s]' % (unchompq(l), unchompq(n)) for l,n in ph]
        ret = ' '.join(phs)
        if ret == '':
            return 'nil'
        else:
            return '(' + ret + ')'

    def _get_postal_as_string (self):
        ret = ''
        for l, a in self.get_postal().iteritems():
            ret += '[' + unchompq(l) + ' '

            if a['street']:
                strts = a['street'].split('\n')
                ret += '(' + ' '.join([unchompq(x) for x in strts]) + ')'
            else:
                ret += 'nil'

            ret += ' ' + (unchompq(a['city'])    if a['city']    else '""')
            ret += ' ' + (unchompq(a['state'])   if a['state']   else '""')
            ret += ' ' + (unchompq(a['zip'])     if a['zip']     else '""')
            ret += ' ' + (unchompq(a['country']) if a['country'] else '""')

            ret += ']'

        if ret == '':
            return 'nil'
        else:
            return '(' + ret + ')'

    def _get_notes_as_string (self):
        noted = self.get_notes_map()
        if not noted:
            logging.error('_ge(): Error in Config. No notes_map field for bb')
            return

        ret =  '(bbdb-id . %s) ' % unchompq(self.get_itemid())
        ret += '(%s . %s) ' % (noted['created'], unchompq(self.get_created()))
        ret += '(%s . %s) ' % (noted['updated'], unchompq(self.get_updated()))

        p = self.get_prefix()
        g = self.get_gender()
        t = self.get_title()
        d = self.get_dept()
        b = self.get_birthday()
        a = self.get_anniv()
        i = self.get_im()
        n = self.get_notes()

        if p:
            ret += '(%s . %s) ' % (noted['prefix'],  unchompq(p))
        if g:
            ret += '(%s . %s) ' % (noted['gender'],  unchompq(g))
        if t:
            ret += '(%s . %s) ' % (noted['title'],   unchompq(t))
        if d:
            ret += '(%s . %s) ' % (noted['dept'],    unchompq(d))
        if i:
            logging.info('IMs not supported in this version')
        if b:
            ret += '(%s . %s) ' % (noted['birthday'], unchompq(b))
        if a:
            ret += '(%s . %s) ' % (noted['anniv'], unchompq(a))
        if n and len(n) > 0:
            ret += '(%s . %s) ' % (noted['notes'], unchompq(n[0]))

        ret += self._get_sync_tags_as_str()

        cnotes = self.get_custom('notes')
        if cnotes:
            for label, note in cnotes.iteritems():
                ret += '(%s . %s) ' % (label, unchompq(note))

        return '(' + ret + ')'

    def _get_sync_tags_as_str (self):
        ret = ''
        i = 0
        for key, val in self.get_sync_tags().iteritems():
            if not val:
                continue

            if i > 0:
                ret += ' '
            i += 1

            ret += '(' + key + ' . ' + unchompq(val) + ')'

        return ret
