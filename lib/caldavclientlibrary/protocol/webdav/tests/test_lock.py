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

from caldavclientlibrary.protocol.http.session import Session
from caldavclientlibrary.protocol.webdav.lock import Lock
from caldavclientlibrary.protocol.webdav.definitions import headers
from StringIO import StringIO

import unittest

class TestRequest(unittest.TestCase):

    def test_Method(self):

        server = Session("www.example.com")
        request = Lock(server, "/", headers.Depth0, Lock.eExclusive, "user@example.com", -1)
        self.assertEqual(request.getMethod(), "LOCK")



class TestRequestHeaders(unittest.TestCase):

    def test_NoSpecialHeaders(self):

        server = Session("www.example.com")
        request = Lock(server, "/", headers.Depth0, Lock.eExclusive, "user@example.com", -1, exists=Lock.eResourceMayExist)
        hdrs = request.generateRequestHeader()
        self.assertFalse("If-None-Match:" in hdrs)
        self.assertFalse("If-Match:" in hdrs)


    def test_IfMatchHeader(self):

        server = Session("www.example.com")
        request = Lock(server, "/", headers.Depth0, Lock.eExclusive, "user@example.com", -1, exists=Lock.eResourceMustExist)
        hdrs = request.generateRequestHeader()
        self.assertFalse("If-None-Match:" in hdrs)
        self.assertTrue("If-Match: *" in hdrs)


    def test_IfNoneMatchHeader(self):

        server = Session("www.example.com")
        request = Lock(server, "/", headers.Depth0, Lock.eExclusive, "user@example.com", -1, exists=Lock.eResourceMustNotExist)
        hdrs = request.generateRequestHeader()
        self.assertTrue("If-None-Match: *" in hdrs)
        self.assertFalse("If-Match:" in hdrs)


    def test_Depth0Headers(self):

        server = Session("www.example.com")
        request = Lock(server, "/", headers.Depth0, Lock.eExclusive, "user@example.com", -1, exists=Lock.eResourceMustNotExist)
        hdrs = request.generateRequestHeader()
        self.assertTrue("Depth: 0" in hdrs)
        self.assertFalse("Depth: 1" in hdrs)
        self.assertFalse("Depth: infinity" in hdrs)


    def test_Depth1Headers(self):

        server = Session("www.example.com")
        request = Lock(server, "/", headers.Depth1, Lock.eExclusive, "user@example.com", -1, exists=Lock.eResourceMustNotExist)
        hdrs = request.generateRequestHeader()
        self.assertFalse("Depth: 0" in hdrs)
        self.assertTrue("Depth: 1" in hdrs)
        self.assertFalse("Depth: infinity" in hdrs)


    def test_DepthInfinityHeaders(self):

        server = Session("www.example.com")
        request = Lock(server, "/", headers.DepthInfinity, Lock.eExclusive, "user@example.com", -1, exists=Lock.eResourceMustNotExist)
        hdrs = request.generateRequestHeader()
        self.assertFalse("Depth: 0" in hdrs)
        self.assertFalse("Depth: 1" in hdrs)
        self.assertTrue("Depth: infinity" in hdrs)



class TestRequestBody(unittest.TestCase):

    def test_GenerateXML(self):

        server = Session("www.example.com")
        request = Lock(server, "/", headers.Depth0, Lock.eExclusive, "user@example.com", -1)
        os = StringIO()
        request.generateXML(os)
        self.assertEqual(os.getvalue(), """<?xml version='1.0' encoding='utf-8'?>
<ns0:lockinfo xmlns:ns0="DAV:">
  <ns0:lockscope>
    <ns0:exclusive />
  </ns0:lockscope>
  <ns0:locktype>
    <ns0:write />
  </ns0:locktype>
  <ns0:owner>user@example.com</ns0:owner>
</ns0:lockinfo>
""".replace("\n", "\r\n")
)



class TestResponse(unittest.TestCase):
    pass



class TestResponseHeaders(unittest.TestCase):

    def test_OneHeader(self):

        server = Session("www.example.com")
        request = Lock(server, "/", headers.Depth0, Lock.eExclusive, "user@example.com", -1)
        request.getResponseHeaders().update({
            "Lock-Token": ("<user@example.com>",),
        })
        self.assertEqual(request.getLockToken(), "user@example.com")
