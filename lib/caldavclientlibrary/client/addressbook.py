##
# Copyright (c) 2006-2013 Apple Inc. All rights reserved.
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

from caldavclientlibrary.protocol.carddav.definitions import carddavxml
from caldavclientlibrary.protocol.url import URL
from caldavclientlibrary.protocol.webdav.definitions import davxml

class AddressBook(object):

    def __init__(self, path=None, session=None):
        self.path = path
        if not path.endswith("/"):
            self.path += "/"
        self.session = session
        self.displayname = None
        self.description = None


    def __str__(self):
        return "AddressBook: %s" % (self.path,)


    def __repr__(self):
        return "AddressBook: %s" % (self.path,)


    def exists(self):
        return self.session.testResource(URL(url=self.path))


    def readAddressBook(self):
        pass


    def writeAddressBook(self, adbk):
        pass


    def readComponent(self, name=None, uid=None):
        pass


    def writeComponent(self, component, name=None):
        pass


    def getDisplayName(self):
        if self.displayname is None and self.session:
            self._getProperties()
        return self.displayname


    def getDescription(self):
        if self.description is None and self.session:
            self._getProperties()
        return self.description


    def _getProperties(self):
        assert(self.session is not None)

        results, _ignore_bad = self.session.getProperties(URL(url=self.path), (davxml.displayname, carddavxml.addressbook_description,))
        self.displayname = results.get(davxml.displayname, "")
        self.description = results.get(carddavxml.addressbook_description, "")
