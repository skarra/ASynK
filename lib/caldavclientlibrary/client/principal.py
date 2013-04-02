##
# Copyright (c) 2007-2013 Apple Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##

from caldavclientlibrary.client.addressbook import AddressBook
from caldavclientlibrary.client.calendar import Calendar
from caldavclientlibrary.protocol.caldav.definitions import caldavxml
from caldavclientlibrary.protocol.caldav.definitions import headers
from caldavclientlibrary.protocol.carddav.definitions import carddavxml
from caldavclientlibrary.protocol.url import URL
from caldavclientlibrary.protocol.webdav.definitions import davxml

class PrincipalCache(object):

    def __init__(self):
        self.cache = {}


    def getPrincipal(self, session, path, refresh=False):
        if path and path.toString() not in self.cache:
            principal = CalDAVPrincipal(session, path)
            principal.loadDetails()
            self.cache[path.toString()] = principal
            self.cache[principal.principalURL] = principal
            if principal.alternateURIs is not None:
                for uri in principal.alternateURIs:
                    self.cache[uri] = principal
        elif refresh:
            self.cache[path.toString()].loadDetails(refresh=True)
        return self.cache[path.toString()] if path else None


    def invalidate(self, path):
        if path.toString() in self.cache:
            del self.cache[path.toString()]

principalCache = PrincipalCache()



def make_tuple(item):
    return item if isinstance(item, tuple) else (item,)



def make_tuple_from_list(item):
    return item if isinstance(item, tuple) else ((item,) if item else ())



class CalDAVPrincipal(object):


    def __init__(self, session, path):

        self.session = session
        self.principalPath = path
        self._initFields()


    def __str__(self):
        return """
    Principal Path    : %s
    Display Name      : %s
    Principal URL     : %s
    Alternate URLs    : %s
    Group Members     : %s
    Memberships       : %s
    Calendar Homes    : %s
    Outbox URL        : %s
    Inbox URL         : %s
    Calendar Addresses: %s
    Address Book Homes: %s
""" % (
          self.principalPath,
          self.displayname,
          self.principalURL,
          self.alternateURIs,
          self.memberset,
          self.memberships,
          self.homeset,
          self.outboxURL,
          self.inboxURL,
          self.cuaddrs,
          self.adbkhomeset,
      )


    def _initFields(self):
        self.loaded = False
        self.valid = False
        self.displayname = "Invalid Principal"
        self.principalURL = ""
        self.alternateURIs = ()
        self.memberset = ()
        self.memberships = ()
        self.homeset = ()
        self.outboxURL = ""
        self.inboxURL = ""
        self.cuaddrs = ()
        self.adbkhomeset = ()

        self.proxyFor = None
        self.proxyreadURL = ""
        self.proxywriteURL = ""


    def loadDetails(self, refresh=False):
        if self.loaded and not refresh:
            return
        self._initFields()

        results, _ignore_bad = self.session.getProperties(
            self.principalPath,
            (
                davxml.resourcetype,
                davxml.displayname,
                davxml.principal_URL,
                davxml.alternate_URI_set,
                davxml.group_member_set,
                davxml.group_membership,
                caldavxml.calendar_home_set,
                caldavxml.schedule_outbox_URL,
                caldavxml.schedule_inbox_URL,
                caldavxml.calendar_user_address_set,
                carddavxml.addressbook_home_set,
            ),
        )
        if results:
            # First check that we have a valid principal and see if its a proxy principal too
            type = results.get(davxml.resourcetype, None)
            self.valid = type.find(str(davxml.principal)) is not None
            if (self.session.hasDAVVersion(headers.calendar_proxy) and
                (type.find(str(caldavxml.calendar_proxy_read)) is not None or
                 type.find(str(caldavxml.calendar_proxy_write)) is not None)):
                parentPath = self.principalPath.dirname()
                self.proxyFor = principalCache.getPrincipal(self.session, parentPath, refresh)

            if self.valid:
                self.displayname = results.get(davxml.displayname, None)
                self.principalURL = results.get(davxml.principal_URL, None)
                self.alternateURIs = make_tuple(results.get(davxml.alternate_URI_set, ()))
                self.memberset = make_tuple_from_list(results.get(davxml.group_member_set, ()))
                self.memberships = make_tuple_from_list(results.get(davxml.group_membership, ()))
                self.homeset = make_tuple(results.get(caldavxml.calendar_home_set, ()))
                self.outboxURL = results.get(caldavxml.schedule_outbox_URL, None)
                self.inboxURL = results.get(caldavxml.schedule_inbox_URL, None)
                self.cuaddrs = make_tuple(results.get(caldavxml.calendar_user_address_set, ()))
                self.adbkhomeset = make_tuple(results.get(carddavxml.addressbook_home_set, ()))

        # Get proxy resource details if proxy support is available
        if self.session.hasDAVVersion(headers.calendar_proxy) and not self.proxyFor:
            results = self.session.getPropertiesOnHierarchy(self.principalPath, (davxml.resourcetype,))
            for path, items in results.iteritems():
                if davxml.resourcetype in items:
                    rtype = items[davxml.resourcetype]
                    if rtype.find(str(caldavxml.calendar_proxy_read)) is not None:
                        self.proxyreadURL = URL(url=path)
                    elif rtype.find(str(caldavxml.calendar_proxy_write)) is not None:
                        self.proxywriteURL = URL(url=path)

        self.loaded = True


    def getSmartDisplayName(self):
        if self.proxyFor:
            return "%s#%s" % (self.proxyFor.displayname, self.displayname,)
        else:
            return self.displayname


    def listCalendars(self, root=None):
        calendars = []
        home = self.homeset[0]
        if not home.path.endswith("/"):
            home.path += "/"

        results = self.session.getPropertiesOnHierarchy(home, (davxml.resourcetype,))
        for path, items in results.iteritems():
            if davxml.resourcetype in items:
                rtype = items[davxml.resourcetype]
                if rtype.find(str(davxml.collection)) is not None and rtype.find(str(caldavxml.calendar)) is not None:
                    calendars.append(Calendar(path=path, session=self.session))
        return calendars


    def listFreeBusySet(self):
        return self._getFreeBusySet()


    def addToFreeBusySet(self, calendars):
        current = self._getFreeBusySet()
        for calendar in calendars:
            current.append(calendar)
        self._setFreeBusySet(current)


    def removeFromFreeBusySet(self, calendars):
        calendar_paths = [calendar.path for calendar in calendars]
        current = self._getFreeBusySet()
        current = [cal for cal in current if cal.path not in calendar_paths]
        self._setFreeBusySet(current)


    def cleanFreeBusySet(self):
        fbset = self.listFreeBusySet()
        badfbset = []
        for calendar in fbset:
            if not calendar.exists():
                badfbset.append(calendar)

        if badfbset:
            self.removeFromFreeBusySet(badfbset)


    def _getFreeBusySet(self):
        hrefs = self.session.getHrefListProperty(self.inboxURL, caldavxml.calendar_free_busy_set)
        return [Calendar(href.relativeURL(), session=self.session) for href in hrefs]


    def _setFreeBusySet(self, calendars):
        hrefs = [URL(url=calendar.path) for calendar in calendars]
        self.session.setProperties(self.inboxURL, ((caldavxml.calendar_free_busy_set, hrefs),))


    def getReadProxies(self, refresh=True):
        if not self.proxyreadURL:
            return ()

        principal = principalCache.getPrincipal(self.session, self.proxyreadURL, refresh=refresh)
        return [principalCache.getPrincipal(self.session, member) for member in principal.memberset]


    def setReadProxies(self, principals):
        if not self.proxyreadURL:
            return ()

        self.session.setProperties(self.proxyreadURL, ((davxml.group_member_set, principals),))
        principalCache.invalidate(self.proxyreadURL)


    def getWriteProxies(self, refresh=True):
        if not self.proxywriteURL:
            return ()

        principal = principalCache.getPrincipal(self.session, self.proxywriteURL, refresh=refresh)
        return [principalCache.getPrincipal(self.session, member) for member in principal.memberset]


    def setWriteProxies(self, principals):
        if not self.proxywriteURL:
            return ()

        self.session.setProperties(self.proxywriteURL, ((davxml.group_member_set, principals),))
        principalCache.invalidate(self.proxywriteURL)


    def listAddressBooks(self, root=None):
        adbks = []
        home = self.adbkhomeset[0]
        if not home.path.endswith("/"):
            home.path += "/"

        results = self.session.getPropertiesOnHierarchy(home, (davxml.resourcetype,))
        for path, items in results.iteritems():
            if davxml.resourcetype in items:
                rtype = items[davxml.resourcetype]
                if rtype.find(str(davxml.collection)) is not None and rtype.find(str(carddavxml.addressbook)) is not None:
                    adbks.append(AddressBook(path=path, session=self.session))
        return adbks
