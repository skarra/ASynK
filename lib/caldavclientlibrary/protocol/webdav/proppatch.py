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
from caldavclientlibrary.protocol.webdav.definitions import methods
from caldavclientlibrary.protocol.webdav.requestresponse import RequestResponse
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

class PropPatch(RequestResponse):

    def __init__(self, session, url, setprops=None, delprops=None):
        super(PropPatch, self).__init__(session, methods.PROPPATCH, url)
        self.setprops = setprops
        self.delprops = delprops

        self.initRequestData()


    def initRequestData(self):
        # Write XML info to a string
        os = StringIO()
        self.generateXML(os)
        self.request_data = RequestDataString(os.getvalue(), "text/xml; charset=utf-8")


    def setOutput(self, response_data):
        self.response_data = response_data


    def addHeaders(self, hdrs):
        # Do default
        super(PropPatch, self).addHeaders(hdrs)

        # Optional ones
        if self.session.useBriefHeader:
            hdrs.append((headers.Brief, "t"))


    def generateXML(self, os):
        # Structure of document is:
        #
        # <DAV:propertyupdate>
        #   <DAV:set>
        #     <<names/values of each property as elements>>
        #   </DAV:set>
        #   <DAV:remove>
        #     <<names of each property as elements>>
        #   </DAV:remove>
        # </DAV:propertyupdate>

        # <DAV:propertyupdate> element
        propertyupdate = Element(davxml.propertyupdate)

        # <DAV:set> element
        if self.setprops:
            set = SubElement(propertyupdate, davxml.set)
            propel = SubElement(set, davxml.prop)
            for prop in self.setprops:
                propel.append(prop)

        # <DAV:remove> element
        if self.delprops:
            remove = SubElement(propertyupdate, davxml.remove)
            propel = SubElement(remove, davxml.prop)
            for prop in self.delprops:
                propel.append(prop)

        # Now we have the complete document, so write it out (no indentation)
        xmldoc = BetterElementTree(propertyupdate)
        xmldoc.writeUTF8(os)
