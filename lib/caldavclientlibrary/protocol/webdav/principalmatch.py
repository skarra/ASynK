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

from caldavclientlibrary.protocol.webdav.propfindbase import PropFindBase
from caldavclientlibrary.protocol.webdav.definitions import headers
from caldavclientlibrary.protocol.webdav.definitions import methods
from StringIO import StringIO
from caldavclientlibrary.protocol.http.data.string import RequestDataString
from caldavclientlibrary.protocol.webdav.definitions import davxml
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from caldavclientlibrary.protocol.utils.xmlhelpers import BetterElementTree

class PrincipalMatch(PropFindBase):

    def __init__(self, session, url, props):
        super(PrincipalMatch, self).__init__(session, url, headers.Depth0)
        self.props = props
        self.method = methods.REPORT

        self.initRequestData()


    def initRequestData(self):
        # Write XML info to a string
        os = StringIO()
        self.generateXML(os)
        self.request_data = RequestDataString(os.getvalue(), "text/xml charset=utf-8")


    def generateXML(self, os):
        # Structure of document is:
        #
        # <DAV:principal-match>
        #   <DAV:self/>
        #   <DAV:prop>
        #     <<names of each property as elements>>
        #   </DAV:prop>
        # </DAV:principal-match>

        # <DAV:principal-match> element
        principalmatch = Element(davxml.principal_match)

        # <DAV:self> element
        SubElement(principalmatch, davxml.self)

        if self.props:

            # <DAV:prop> element
            prop = SubElement(principalmatch, davxml.prop)

            # Now add each property
            for item in self.props:

                # Add property element taking namespace into account

                # Look for DAV namespace and reuse that one
                SubElement(prop, item)

        # Now we have the complete document, so write it out (no indentation)
        xmldoc = BetterElementTree(principalmatch)
        xmldoc.writeUTF8(os)
