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

from caldavclientlibrary.protocol.webdav.requestresponse import RequestResponse
from caldavclientlibrary.protocol.webdav.definitions import methods
from StringIO import StringIO
from caldavclientlibrary.protocol.http.data.string import RequestDataString
from caldavclientlibrary.protocol.webdav.definitions import davxml
from xml.etree.ElementTree import Element
from caldavclientlibrary.protocol.utils.xmlhelpers import BetterElementTree

class ACL(RequestResponse):

    def __init__(self, session, url, acls):
        super(ACL, self).__init__(session, methods.ACL, url)
        self.acls = acls

        self.initRequestData()


    def initRequestData(self):
        # Write XML info to a string
        os = StringIO()
        self.generateXML(os)
        self.request_data = RequestDataString(os.getvalue(), "text/xml charset=utf-8")


    def generateXML(self, os):
        # Structure of document is:
        #
        # <DAV:acl>
        #   <DAV:ace>
        #     <S:inheritable xmlns:S="http:#jakarta.apache.org/slide/"> / <S:non-inheritable xmlns:S="http:#jakarta.apache.org/slide/">
        #     <DAV:principal>...</DAV:principal>
        #       <DAV:grant>...</DAV:grant>
        #   </DAV:ace>
        #   ...
        # </DAV:acl>

        # <DAV:acl> element
        acl = Element(davxml.acl)

        # Do for each ACL
        if self.acls:

            for ace in self.acls:
                # Cannot do if change not allowed
                if not ace.canChange():
                    continue

                # <DAV:ace> element
                ace.generateACE(acl)

        # Now we have the complete document, so write it out (no indentation)
        xmldoc = BetterElementTree(acl)
        xmldoc.writeUTF8(os)
