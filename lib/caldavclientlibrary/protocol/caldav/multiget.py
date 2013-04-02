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
from caldavclientlibrary.protocol.caldav.definitions import caldavxml
from caldavclientlibrary.protocol.http.data.string import RequestDataString
from caldavclientlibrary.protocol.utils.xmlhelpers import BetterElementTree
from caldavclientlibrary.protocol.webdav.definitions import davxml
from caldavclientlibrary.protocol.webdav.report import Report
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

class Multiget(Report):

    def __init__(self, session, url, hrefs, props=()):
        super(Multiget, self).__init__(session, url)
        self.props = props
        self.hrefs = hrefs

        self.initRequestData()


    def initRequestData(self):
        # Write XML info to a string
        os = StringIO()
        self.generateXML(os)
        self.request_data = RequestDataString(os.getvalue(), "text/xml charset=utf-8")


    def generateXML(self, os):
        # Structure of document is:
        #
        # <CalDAV:calendar-multiget>
        #   <DAV:prop>
        #     <<names of each property as elements>>
        #   </DAV:prop>
        #   <DAV:href>...</DAV:href>
        #   ...
        # </CalDAV:calendar-multiget>

        # <CalDAV:calendar-multiget> element
        multiget = Element(caldavxml.calendar_multiget)

        if self.props:
            # <DAV:prop> element
            prop = SubElement(multiget, davxml.prop)

            # Now add each property
            for propname in self.props:
                # Add property element taking namespace into account
                SubElement(prop, propname)

        # Now add each href
        for href in self.hrefs:
            # Add href elements
            SubElement(multiget, davxml.href).text = href

        # Now we have the complete document, so write it out (no indentation)
        xmldoc = BetterElementTree(multiget)
        xmldoc.writeUTF8(os)
