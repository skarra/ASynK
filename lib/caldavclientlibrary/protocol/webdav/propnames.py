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
from xml.etree.ElementTree import Element
from caldavclientlibrary.protocol.webdav.definitions import davxml
from caldavclientlibrary.protocol.utils.xmlhelpers import BetterElementTree

class PropNames(PropFindBase):

    def __init__(self, session, url, depth):
        super(PropNames, self).__init__(session, url, depth)
        self.initRequestData()


    def generateXML(self, os):
        # Structure of document is:
        #
        # <DAV:propfind>
        #   <DAV:propname/>
        # </DAV:propfind>

        # <DAV:propfind> element
        propfind = Element(davxml.propfind)

        # <DAV:propname> element
        propfind.append(Element(davxml.propname))

        # Now we have the complete document, so write it out (no indentation)
        xmldoc = BetterElementTree(propfind)
        xmldoc.writeUTF8(os)
