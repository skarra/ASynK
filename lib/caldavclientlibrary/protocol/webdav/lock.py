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
from caldavclientlibrary.protocol.webdav.definitions import headers
from StringIO import StringIO
from caldavclientlibrary.protocol.http.data.string import RequestDataString
from caldavclientlibrary.protocol.webdav.definitions import davxml
from xml.etree.ElementTree import Element
from caldavclientlibrary.protocol.utils.xmlhelpers import BetterElementTree

class Lock(RequestResponse):

    eExclusive = 0
    eShared = 1

    eResourceMustExist = 0
    eResourceMustNotExist = 1
    eResourceMayExist = 2

    def __init__(self, session, url, depth, scope, owner, timeout, exists=eResourceMustExist):

        assert(depth in (headers.Depth0, headers.Depth1, headers.DepthInfinity))
        assert(scope in (Lock.eExclusive, Lock.eShared,))
        assert(exists in (Lock.eResourceMustExist, Lock.eResourceMustNotExist, Lock.eResourceMayExist))

        super(Lock, self).__init__(session, methods.LOCK, url)

        self.depth = depth
        self.scope = scope
        self.owner = owner
        self.timeout = timeout

        # Do appropriate etag based on exists
        if exists == Lock.eResourceMustExist:
            self.etag = "*"
            self.etag_match = True
        elif exists == Lock.eResourceMustNotExist:
            self.etag = "*"
            self.etag_match = False
        elif exists == Lock.eResourceMayExist:
            pass

        self.initRequestData()


    def initRequestData(self):
        # Write XML info to a string
        os = StringIO()
        self.generateXML(os)
        self.request_data = RequestDataString(os.getvalue(), "text/xml charset=utf-8")


    def addHeaders(self, hdrs):
        # Do default
        super(Lock, self).addHeaders(hdrs)

        # Add depth header
        hdrs.append((headers.Depth, self.depth))

        # Add timeout header
        if self.timeout == -1:
            hdrs.append((headers.Timeout, headers.TimeoutInfinite))
        elif self.timeout > 0:
            hdrs.append((headers.Timeout, "%s%d" % (headers.TimeoutSeconds, self.timeout)))


    def generateXML(self, os):
        # Structure of document is:
        #
        # <DAV:lockinfo>
        #   <DAV:lockscope>
        #     <DAV:exclusive/> | <DAV:shared/>
        #   </DAV:lockscope>
        #   <DAV:locktype>
        #     <DAV:write/>
        #   </DAV:locktype>
        #   <DAV:owner>
        #     <<owner>>
        #   </DAV:owner>
        # </DAV:lockinfo>

        # <DAV:lockinfo> element
        lockinfo = Element(davxml.lockinfo)

        # <DAV:lockscope> element
        lockscope = Element(davxml.lockscope)
        lockinfo.append(lockscope)

        # <DAV:exclusive/> | <DAV:shared/> element
        lockscope.append(Element(davxml.exclusive if self.scope == Lock.eExclusive else davxml.shared))

        # <DAV:locktype> element
        locktype = Element(davxml.locktype)
        lockinfo.append(locktype)

        # <DAV:write/> element
        locktype.append(Element(davxml.write))

        # <DAV:owner> element is optional
        if self.owner:
            # <DAV:owner> element
            owner = Element(davxml.owner)
            owner.text = self.owner
            lockinfo.append(owner)

        # Now we have the complete document, so write it out (no indentation)
        BetterElementTree(lockinfo).writeUTF8(os)


    def getLockToken(self):

        # Get the Lock-Token header from response headers
        result = ""
        if self.hasResponseHeader(headers.LockToken):

            # Get Coded-URL
            codedurl = self.getResponseHeader(headers.LockToken)

            # Strip leading/trailing <>
            codeurl = codedurl.strip()
            if codeurl.startswith("<") and codeurl.endswith(">"):
                result = codeurl[1:-1]
            else:
                result = codeurl

        return result
