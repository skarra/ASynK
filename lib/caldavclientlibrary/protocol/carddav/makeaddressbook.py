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

from StringIO import StringIO
from caldavclientlibrary.protocol.carddav.definitions import carddavxml
from caldavclientlibrary.protocol.http.data.string import RequestDataString
from caldavclientlibrary.protocol.utils.xmlhelpers import BetterElementTree
from caldavclientlibrary.protocol.webdav.definitions import davxml, methods
from caldavclientlibrary.protocol.webdav.requestresponse import RequestResponse
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

class MakeAddressBook(RequestResponse):

    def __init__(self, session, url, displayname=None, description=None):
        super(MakeAddressBook, self).__init__(session, methods.MKCOL, url)
        self.displayname = displayname
        self.description = description

        self.initRequestData()


    def initRequestData(self):
        # Write XML info to a string
        os = StringIO()
        self.generateXML(os)
        self.request_data = RequestDataString(os.getvalue(), "text/xml charset=utf-8")


    def generateXML(self, os):
        # Structure of document is:
        #
        # <WEBDAV:mkcol>
        #   <DAV:set>
        #     <DAV:prop>
        #       <DAV:resourcetype><DAV:collection/><CARDDAV:addressbook/></DAV:resourcetype>
        #       <<each property as elements>>
        #     </DAV:prop>
        #   </DAV:set>
        # </WEBDAV:mkcol>

        # <CALDAV:mkcalendar> element
        mkcol = Element(davxml.mkcol)

        # <DAV:set> element
        set = SubElement(mkcol, davxml.set)

        # <DAV:prop> element
        prop = SubElement(set, davxml.prop)

        # <WebDAV:resourcetype> element
        resourcetype = SubElement(prop, davxml.resourcetype)
        SubElement(resourcetype, davxml.collection)
        SubElement(resourcetype, carddavxml.addressbook)

        # <DAV:displayname> element
        if self.displayname:
            displayname = SubElement(prop, davxml.displayname)
            displayname.text = self.displayname

        # <CardDAV:addressbook-description> element
        if self.description:
            description = SubElement(prop, carddavxml.addressbook_description)
            description.text = self.description

        # Now we have the complete document, so write it out (no indentation)
        xmldoc = BetterElementTree(mkcol)
        xmldoc.writeUTF8(os)
