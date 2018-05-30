##
## Created : Fri Apr 06 19:08:32 IST 2012
##
## Copyright (C) 2012, 2013 Sriram Karra <karra.etc@gmail.com>
##
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero GPL (GNU AGPL) as published by the
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
## This file defines a wrapper class around a BBDB Contact entry, by extending
## the Contact abstract base Contact class. BBDB is, of course, the Insidious
## Big Brother Data Base
##

import copy, logging, re, string, uuid
from   contact    import Contact
from   utils      import chompq, unchompq, classify_email_addr
import demjson, pimdb_bb, folder_bb

def esc_str (x):
    """This takes a raw string and ensures all problematic characters are
    escaped appropriately so it is safe to be written to BBDB store."""

    if not x:
        return x

    x = x.replace('\\', '\\\\')
    x = x.replace('\r\n', '\\n')
    x = x.replace('\n', '\\n')
    return x.replace('"', r'\"')

def unesc_str (x):
    """This is the inverse of escape_str. i.e. this undoes any escaping
    that is present in the string x that had to be done to make it safe to
    write to BBDB store."""

    if not x:
        return x

    x = x.replace('\\n', '\n')
    x = x.replace(r'\"', '"')
    x = x.replace('\\\\', '\\')
    return x

class BBDBParseError(Exception):
    pass

class BBContact(Contact):
    """This class extends the Contact abstract base class to wrap a BBDB
    Contact"""

    def __init__ (self, folder, con=None, con_itemid=None, rec=None):
        """rec is the native string vector representation of a BBDB contact
        entry on disk."""

        Contact.__init__(self, folder, con)
        self.atts.update({'bbdb_folder' : None,})

        conf = self.get_config()
        if con:
            if con_itemid:
                self.set_itemid(con_itemid)
            else:
                logging.debug('Potential new BBContact: %s', con.get_name())

        if folder.get_name():
            self.set_bbdb_folder(folder.get_name())

        if rec:
            self.set_rec(rec)
            self.init_props_from_rec(rec)

        if not self.get_itemid():
            iid = ('%s' % uuid.uuid1())
            logging.debug('Assigning UUID %s for new contact: %s', iid, 
                          self.get_name())
            self.set_itemid(iid)

        self.in_init(False)

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

        return self.get_disp_name()

    ##
    ## Now onto the non-abstract methods.
    ##

    def get_bbdb_folder (self):
        return self._get_att('bbdb_folder')

    def set_bbdb_folder (self, bbdb_folder):
        return self._set_att('bbdb_folder', bbdb_folder)

    def get_rec (self):
        return self._get_att('rec')

    def set_rec (self, rec):
        return self._set_att('rec', rec)

    def init_props_from_rec (self, rec):
        con_re = self.get_store().get_con_re()
        parse_res = re.search(con_re, rec)

        if not parse_res:
            raise BBDBParseError('Could not Parse BBDB contact entry: %s' %rec)

        d = parse_res.groupdict()
        self._snarf_names_from_parse_res(d)
        self._snarf_aka_from_parse_res(d)
        self._snarf_company_from_parse_res(d)
        self._snarf_emails_from_parse_res(d)
        self._snarf_postal_from_parse_res(d)
        self._snarf_phones_from_parse_res(d)
        self._snarf_notes_from_parse_res(d)
        self._snarf_created_updated_from_parse_res(d)

    def init_rec_from_props (self):
        if self.dirty():
            self.set_updated(pimdb_bb.BBPIMDB.get_bbdb_time())

        rec = '['
        rec += self._get_names_as_string()   + ' '
        rec += self._get_aka_as_string()     + ' '
        rec += self._get_company_as_string() + ' '
        rec += self._get_phones_as_string()  + ' '
        rec += self._get_postal_as_string()  + ' '
        rec += self._get_emails_as_string()  + ' '
        rec += self._get_notes_as_string()   + ' '
        rec += self._get_ver9_fields_as_string() + ' '
        rec += ' nil]'

        self.dirty(False)
        return rec

    def _snarf_names_from_parse_res (self, pr):
        n = pr['firstname']
        if n and n != 'nil':
            self.set_firstname(unesc_str(chompq(n)))

        n = pr['lastname']
        if n and n != 'nil':
            self.set_lastname(unesc_str(chompq(n)))

        try:
            affix = pr['affix']
            if affix and affix != 'nil':
                str_re = self.get_store().get_str_re()
                affix = re.findall(str_re, affix)
                self.set_suffix(unesc_str(chompq(affix[0])))

                if len(affix) > 1:
                    aff = demjson.encode([unesc_str(chompq(x)) for x in affix[1:]])
                    ## FIXME: Do we need to escape the quotes in json encoding
                    ## as in the except clause?
                    self.add_custom('affix', aff)
        except KeyError, e:
            ## FIXME: There should be a better way to handle the format
            ## differences.... for now we'll put up with the hacks
            affix = self.get_custom('affix')

            if affix:
                affix = demjson.decode(affix)
                if len(affix) > 0:
                    self.set_suffix(affix[0])
                    affix = affix[1:]
                    if len(affix) > 0:
                        aff = demjson.encode(affix)
                        self.add_custom('affix', aff)

    def _snarf_aka_from_parse_res (self, pr):
        aka = pr['aka']
        if aka and aka != 'nil':
            str_re = self.get_store().get_str_re()
            aka    = re.findall(str_re, aka)
            nick   = aka[0]
            rest   = aka[1:]
            if nick:
                self.set_nickname(unesc_str(chompq(nick)))

            if rest and len(rest) > 0:
                ## Note that 'rest' is an array, and it will not be possible
                ## to serialize it when sending to Google or saving to Outlook
                ## etc. So let's just encode it in json format - our goto
                ## solution for such problems.
                self.add_custom('aka', demjson.encode(rest))

    def _snarf_company_from_parse_res (self, pr):
        cs = pr['company']

        if cs and cs != 'nil':
            ## The first company goes into the Company field, the rest we will
            ## push into the custom field (as aa json encoded string)
            str_re = self.get_store().get_str_re()
            cs = re.findall(str_re, cs)
            
            ## FIXME: This is an egregious hack. The right way to do this is
            ## to have field specific parsing routine in the BBPIMDB just like
            ## we have the regexes there. for now, let's move on with ugly
            ## hacks. 
            ver = self.get_store().get_file_format()
            if ver == '6':
                cs = chompq(cs[0]).split('; ')

            self.set_company(unesc_str(chompq(cs[0])))
            rest = cs[1:]

            if rest and len(rest) > 0:
                self.add_custom('company', demjson.encode(rest))

    def _snarf_emails_from_parse_res (self, pr):
        ems = pr['emails']

        if ems:
            str_re = self.get_store().get_str_re()
            ems = re.findall(str_re, ems)
            ems = [chompq(x) for x in ems]

            domains = self.get_email_domains()

            for em in ems:
                if em == 'nil':
                    continue

                home, work, other = classify_email_addr(em, domains)

                if home:
                    self.add_email_home(em)
                elif work:
                    self.add_email_work(em)
                elif other:
                    self.add_email_other(em)
                else:
                    self.add_email_work(em)

                if not self.get_email_prim():
                    self.set_email_prim(em)

    def _snarf_postal_from_parse_res (self, pr):
        adr_re = self.get_store().get_adr_re()
        str_re = self.get_store().get_str_re()
        addrs  = re.findall(adr_re, pr['addrs'])

        for i, addr in enumerate(addrs):
            label, val = addr[:2]
            add = '[' + label + ' ' + val + ']'
            res = re.search(adr_re, add)

            if res:
                addict = {'street'  : None,
                          'city'    : None,
                          'state'   : None,
                          'country' : None,
                          'zip'     : None,}
                fields = res.groupdict()

                streets = fields['streets']
                sts = re.findall(str_re, streets)
                sts = map(unesc_str, [chompq(x) for x in sts])

                if sts:
                    addict.update({'street' : '\n'.join(sts)})

                city = fields['city']
                if city:
                    addict.update({'city' : unesc_str(chompq(city))})

                state = fields['state']
                if state:
                    addict.update({'state' : unesc_str(chompq(state))})

                country = fields['country']
                if country:
                    addict.update({'country' : unesc_str(chompq(country))})

                pin = fields['zip']
                if pin:
                    addict.update({'zip' : unesc_str(chompq(pin))})

                self.add_postal(chompq(label), addict)
                if i == 0:
                    self.set_postal_prim_label(label)
            else:
                logging.error('bb:snarf_postal(): Huh? No match for add %s.',
                              add)

    def _snarf_phones_from_parse_res (self, pr):
        ph_re = self.get_store().get_ph_re()
        phs   = re.findall(ph_re, pr['phones']) if pr['phones'] else None

        first = True
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
                    if first:
                        self.set_phone_prim(phnum)
                        first = False
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
            self.add_fax_home(num)
        else:
            self.add_phone_other(num)

    def _add_im (self, label_re, label, value):
        res = re.search(label_re, label)
        if res:
            try:
                tag = res.group(1)
            except IndexError, e:
                tag = res.group(0)
        else:
            tag = label

        if len(self.get_im()) == 0:
            self.set_im_prim(tag)

        self.add_im(tag, value)

    def _snarf_notes_from_parse_res (self, pr):
        """Parse the BBDB Notes entry; this contains most of the good
        stuff... including sync tags and stuff."""

        noted = self.get_notes_map()

        if not noted:
            logging.error('Error in Config file. No notes_map field for bb')
            return

        stag_re = self.get_store().get_sync_tag_re()
        note_re = self.get_store().get_note_re()
        notes = re.findall(note_re, pr['notes'])
        custom = {}

        self.set_bbdb_folder(None)

        # logging.debug('bb:snfpr:stag_re: %s', stag_re)
        # keys = [note[0] for note in notes]
        # logging.debug('bb:snfpr:Keys: %s', keys)

        for note in notes:
            (key, val) = note[:2]

            key = key.rstrip()
            val = unesc_str(chompq(val))

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
            elif re.search(noted['ims'], key):
                self._add_im(noted['ims'], key, val)
            elif key == noted['notes']:
                self.add_notes(val)
            elif key == noted['birthday']:
                if self._is_valid_date(val, noted['birthday']):
                    self.set_birthday(val)
            elif key == noted['anniv']:
                if self._is_valid_date(val, noted['anniv']):
                    self.set_anniv(val)
            elif re.search(stag_re, key):
                self.update_sync_tags(key.rstrip(), val)
            elif re.search(noted['web_home_re'], key):
                self.add_web_home(val)
            elif re.search(noted['web_work_re'], key):
                self.add_web_work(val)
            elif re.search(noted['middle_name'], key):
                self.set_middlename(val)
            elif re.search('affix', key):
                affix = demjson.decode(val)
                if len(affix) > 0:
                    self.set_suffix(affix[0])
                if len(affix) > 1:
                    custom.update({key : demjson.encode(affix[1:])})
            elif re.search(noted['folder'], key):
                self.set_bbdb_folder(val)
            else:
                ## The rest of the stuff go into the 'Custom' field...
                custom.update({key : val})

        if len(custom.keys()) > 0:
            self.update_custom(custom)

    def _snarf_created_updated_from_parse_res (self, pr):
        """In file format ver 9 some fields were made first class citizens in
        the schema, which were parts of the notes field in earlier
        versions. Such fields need to be read and processed separately."""

        ## For earlier versions of the file format this would have
        ## been handled already as part of the notes section.
        bbdb_ver = int(self.get_store().get_file_format())
        if bbdb_ver < 9:
            return

        # FIXME: We may also want to read and use the native bbdbid...
        created_on = pr['createdon']
        if created_on and created_on != 'nil':
            self.set_created(unesc_str(chompq(created_on)))

        last_updated = pr['lastupdated']
        if last_updated and last_updated != 'nil':
            self.set_updated(unesc_str(chompq(last_updated)))

    def _is_valid_date (self, date, label):
        res = re.search('((\d\d\d\d)|-)-(\d\d)-(\d\d)', date)
        if not res:
            logging.error(('%s for %s should be yyyy-mm-dd ' +
                           'format. Actual value: %s'),
                           label, self.get_name(), date)
            return False
        elif int(res.group(3)) > 12:
            logging.error('Invalid month (%d) in %s for %s',
                          int(res.group(3)), label, self.get_name())
            return False
        else:
            ## We should really check the date for validity as well, oh, well,
            ## later. FIXME
            return True

    def _get_names_as_string (self):
        ret = ''
        n = esc_str(self.get_firstname())
        l = esc_str(self.get_lastname())

        if bool(l) != bool(n):
            # A Logical xor to check if one and only one of the two strings is
            # valid. Inspired by: http://stackoverflow.com/a/433161/987738
            n = self.get_name()
            if n:
                ret = '"%s" nil ' % n
            else:
                ret = 'nil nil '
        else:
            if n:
                ret += unchompq(n) + ' '
            else:
                ret += 'nil '

            if l:
                ret += unchompq(l) + ' '
            else:
                ret += 'nil '

        ## Handle the suffix - There is an "Affix" array field in file format
        ## 7+. So if we are in version 7 we should build up an array using the
        ## suffix field and any other stuf we stashed away in custom
        ## field. Othewrise we will just let all the stuff get handled in the
        ## custom handling routine - even the first suffix.

        a = esc_str(self.get_suffix())
        bbdb_ver = self.get_store().get_file_format()
        if not a:
            if bbdb_ver != '6':
                ret += ' nil'

        else:
            suffix = self.get_custom('affix')
            suffix = demjson.decode(suffix) if suffix else []

            if bbdb_ver == '6':
                suffix.insert(0, a)
                self.add_custom('affix', demjson.encode(suffix))
            else:
                suffix.insert(0, a)
                ret += ' (' + ' '.join([unchompq(x) for x in suffix]) + ')'
                self.del_custom('affix')

        return ret

    def _get_aka_as_string (self):
        nick = esc_str(self.get_nickname())
        if not nick:
            return 'nil'
        nick = unchompq(nick)

        aka = copy.deepcopy(self.get_custom('aka'))
        if aka:
            ## Note that we have inserted AKAs an json encoded array of
            ## strings.
            aka = demjson.decode(aka)
            aka.insert(0, nick)
            return('(' + ' '.join(aka) + ')')
        else:
            return '(' + nick + ')'

    def _get_company_as_string (self):
        comp1 = esc_str(self.get_company())
        if not comp1:
            return 'nil'

        comp = copy.deepcopy(self.get_custom('company'))
        ver = self.get_store().get_file_format()
        ## FIXME: This is an egregious design violation, as noted earlier. We
        ## should move all such version specific conversions to pimdb_bb.el
        if ver == '6':
            if comp and len(comp) > 0:
                comp = demjson.decode(comp)
                comp = [chompq(x) for x in comp]
            else:
                comp = []

            comp.insert(0, comp1)
            return unchompq('; '.join(comp))
        else:
            if comp and len(comp) > 0:
                comp = demjson.decode(comp)
                comp.insert(0, unchompq(comp1))
            else:
                comp = [unchompq(comp1)]

            return ('(' + ' '.join(comp) + ')')

    def _get_emails_as_string (self):
        ems = [unchompq(e) for e in self.get_email_home()]
        ems.extend([unchompq(e) for e in self.get_email_work()])
        ems.extend([unchompq(e) for e in self.get_email_other()])

        # The primary email address should be the first in the list.
        emp = self.get_email_prim()
        if emp:
            emp = unchompq(emp)
            if emp in ems:
                ems.remove(emp)
            ems.insert(0, emp)

        ret = ' '.join(ems)

        if ret == '':
            return 'nil'
        else:
            return '(' + ret + ')'

    def _get_websites_as_string (self):
        ## FIXME: What happens to the "get_web_prim()". 

        noted = self.get_notes_map()
        ret = []

        home_label = noted['web_home_re']
        for i, web in enumerate(self.get_web_home()):
            if not web:
                continue

            ## FIXME: Hack Alert. There is no easy way to regenerate proper
            ## labels with the regex. Need to rethink this a bit. Perhaps
            ## there needs to be a patter to match, and a python pattern to
            ## generate them at the remote end.
            if home_label == 'Web.*Home':
                label = 'Web-%02d-Home' % i
            else:
                label = home_label
            value = unchompq(esc_str(web))

            ret.append("(%s . %s)" % (label, value))

        work_label = noted['web_work_re']
        for i, web in enumerate(self.get_web_work()):
            if not web:
                continue

            ## FIXME: Hack Alert. See above
            if work_label == 'Web.*Work':
                label = 'Web-%02d-Work' % i
            else:
                label = work_label
            value = unchompq(esc_str(web))

            ret.append("(%s . %s)" % (label, value))

        return ' '.join(ret)

    def _get_phones_as_string (self):
        ## Note that any BBDB phone number that was structured in the North
        ## Amerial format will be munged into an equivalent string notation
        ## for our convenience

        ph  = copy.deepcopy(self.get_phone_home())
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
        for l, a in self.get_postal(as_array=True):
            ret += '[' + unchompq(l) + ' '

            if 'street' in a and a['street']:
                s = a['street'].split('\n')
                ret += '(' + ' '.join([unchompq(x) for x in map(esc_str, s)]) + ')'
            else:
                ret += 'nil'

            arr = [a['city'], a['state'], a['zip'], a['country']]
            ret += ' ' + ' '.join([unchompq(x) for x in map(esc_str, arr)])
            ret += ']'

        if ret == '':
            return 'nil'
        else:
            return '(' + ret + ')'

    def _get_ims_as_string (self, ims=None):
        if not ims:
            ims = self.get_im()

        # This is a trcky bit. If the IM label was a regular expression, then
        # we need to generate the correctly formatted IM notes field... Hm.

        im_label_re  = self.get_notes_map()['ims']
        if re.search(r'(.*)', im_label_re):
            im_label_fmt = string.replace(im_label_re, '(.*)', '%s')
        else:
            im_label_fmt = '%s'

        ret = ''
        for l, v in ims.iteritems():
            ret += ' ('+ (im_label_fmt % l) + ' . ' + unchompq(esc_str(v)) + ')'

        return ret

    def _get_notes_as_string (self):
        bbdb_ver = self.get_store().get_file_format()

        noted = self.get_notes_map()
        if not noted:
            logging.error('_ge(): Error in Config. No notes_map field for bb')
            return

        ret =  '(bbdb-id . %s) ' % unchompq(self.get_itemid())
        if int(bbdb_ver) <= 9:
            ret += '(%s . %s) ' % (noted['created'],
                                   unchompq(self.get_created()))
            ret += '(%s . %s) ' % (noted['updated'],
                                   unchompq(self.get_updated()))

        p = esc_str(self.get_prefix())
        g = esc_str(self.get_gender())
        t = esc_str(self.get_title())
        d = esc_str(self.get_dept())
        b = esc_str(self.get_birthday())
        a = esc_str(self.get_anniv())
        i = self.get_im()
        n = self.get_notes()
        m = esc_str(self.get_middlename())
        f = esc_str(self.get_bbdb_folder())

        if p:
            ret += '(%s . %s) ' % (noted['prefix'],  unchompq(p))
        if g:
            ret += '(%s . %s) ' % (noted['gender'],  unchompq(g))
        if t:
            ret += '(%s . %s) ' % (noted['title'],   unchompq(t))
        if d:
            ret += '(%s . %s) ' % (noted['dept'],    unchompq(d))
        if i and len(i) > 0:
            ret += self._get_ims_as_string(i)
        if b:
            ret += '(%s . %s) ' % (noted['birthday'], unchompq(b))
        if a:
            ret += '(%s . %s) ' % (noted['anniv'], unchompq(a))
        if n and len(n) > 0 and n[0]:
            ## BBDB cannot handle actual line breaks and double quotes. We
            ## need to quote them. And convert the dos line endings while we
            ## are at it...
            no = esc_str(n[0])
            ret += '(%s . %s) ' % (noted['notes'], unchompq(no))
        if m and m != '':
            ret += '(%s . %s) ' % (noted['middle_name'], unchompq(m))
        if f:
            ret += '(%s . %s) ' % (noted['folder'],  unchompq(f))

        ret += self._get_sync_tags_as_str() + ' '
        ret += self._get_websites_as_string() + ' '

        for label, note in self.get_custom().iteritems():
            if label in ['company', 'aka']:
                continue

            ret += '(%s . %s) ' % (label, unchompq(esc_str(note)))

        return '(' + ret + ')'

    def _get_ver9_fields_as_string (self):
        """Prior to file format ver 9 these fields were embedded in the notes
           section. Ver 9 onwards they are first class citizens, so we
           need to handle them separately and make sure they are
           available in the record at the appropriate level."""

        bbdb_ver = int(self.get_store().get_file_format())
        if bbdb_ver < 9:
            return ' '           # Handled via the notes section

        return ' '.join([unchompq(x) for x in
                         [self.get_itemid(), self.get_created(),
                          self.get_updated()]])

    def _get_sync_tags_as_str (self):
        conf     = self.get_config()
        pname_re = conf.get_profile_name_re()
        label    = conf.make_sync_label(pname_re, self.get_dbid())

        ret = ''
        i = 0
        for key, val in self.get_sync_tags().iteritems():
            ## FIXME: This was put in here for a reason. I think it had
            ## something to do with "reproducing" sync labels containing the
            ## ID on the local end itself. This was the easiest fix,
            ## IIRC. This clearly conflicts with the present need. We need to
            ## solve this problem - and apply it for all the DBs.

            # # Skip any sync tag with BBDB IDs as values.
            # if re.search(label, key) or not val:
            #     continue

            if i > 0:
                ret += ' '
            i += 1

            ret += '(' + key + ' . ' + unchompq(val) + ')'

        return ret
