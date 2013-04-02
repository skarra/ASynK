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
from caldavclientlibrary.protocol.http.data.string import RequestDataString
from caldavclientlibrary.protocol.utils.xmlhelpers import BetterElementTree
from caldavclientlibrary.protocol.webdav.definitions import davxml, headers
from caldavclientlibrary.protocol.webdav.report import Report
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

class SyncCollection(Report):

    def __init__(self, session, url, level, synctoken, props=()):
        assert(level in (davxml.sync_level_1, davxml.sync_level_infinite,))

        super(SyncCollection, self).__init__(session, url)
        self.level = level
        self.synctoken = synctoken
        self.props = props

        self.initRequestData()


    def initRequestData(self):
        # Write XML info to a string
        os = StringIO()
        self.generateXML(os)
        self.request_data = RequestDataString(os.getvalue(), "text/xml charset=utf-8")


    def addHeaders(self, hdrs):
        # Do default
        super(SyncCollection, self).addHeaders(hdrs)

        # Add depth header
        hdrs.append((headers.Depth, headers.Depth0))


    def generateXML(self, os):
        # Structure of document is:
        #
        # <DAV:sync-collection>
        #   <DAV:sync-token>xxx</DAV:sync-token>
        #   <DAV:sync-level>xxx</DAV:sync-level>
        #   <DAV:prop>
        #     <<names of each property as elements>>
        #   </DAV:prop>
        # </DAV:sync-collection>

        # <DAV:sync-collection> element
        synccollection = Element(davxml.sync_collection)

        # Add sync-token element
        SubElement(synccollection, davxml.sync_token).text = self.synctoken

        # Add sync-token element
        SubElement(synccollection, davxml.sync_level).text = self.level

        # <DAV:prop> element
        prop = SubElement(synccollection, davxml.prop)

        if self.props:
            # Now add each property
            for propname in self.props:
                # Add property element taking namespace into account
                SubElement(prop, propname)

        # Now we have the complete document, so write it out (no indentation)
        xmldoc = BetterElementTree(synccollection)
        xmldoc.writeUTF8(os)
