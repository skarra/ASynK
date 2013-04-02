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

from caldavclientlibrary.protocol.webdav.session import Session
from caldavclientlibrary.protocol.caldav.multiget import Multiget
from StringIO import StringIO
from caldavclientlibrary.protocol.webdav.definitions import davxml
import unittest

class TestRequest(unittest.TestCase):


    def test_Method(self):

        server = Session("www.example.com")
        request = Multiget(server, "/", ())
        self.assertEqual(request.getMethod(), "REPORT")



class TestRequestHeaders(unittest.TestCase):
    pass



class TestRequestBody(unittest.TestCase):

    def test_GenerateXMLOneHrefOnly(self):

        server = Session("www.example.com")
        request = Multiget(server, "/", ("/a",))
        os = StringIO()
        request.generateXML(os)
        self.assertEqual(os.getvalue(), """<?xml version='1.0' encoding='utf-8'?>
<ns0:calendar-multiget xmlns:ns0="urn:ietf:params:xml:ns:caldav">
  <ns1:href xmlns:ns1="DAV:">/a</ns1:href>
</ns0:calendar-multiget>
""".replace("\n", "\r\n")
)


    def test_GenerateXMLMultipleHrefsOnly(self):

        server = Session("www.example.com")
        request = Multiget(server, "/", ("/a", "/b",))
        os = StringIO()
        request.generateXML(os)
        self.assertEqual(os.getvalue(), """<?xml version='1.0' encoding='utf-8'?>
<ns0:calendar-multiget xmlns:ns0="urn:ietf:params:xml:ns:caldav">
  <ns1:href xmlns:ns1="DAV:">/a</ns1:href>
  <ns1:href xmlns:ns1="DAV:">/b</ns1:href>
</ns0:calendar-multiget>
""".replace("\n", "\r\n")
)


    def test_GenerateXMLMultipleHrefsOneProperty(self):

        server = Session("www.example.com")
        request = Multiget(server, "/", ("/a", "/b",), (davxml.getetag,))
        os = StringIO()
        request.generateXML(os)
        self.assertEqual(os.getvalue(), """<?xml version='1.0' encoding='utf-8'?>
<ns0:calendar-multiget xmlns:ns0="urn:ietf:params:xml:ns:caldav">
  <ns1:prop xmlns:ns1="DAV:">
    <ns1:getetag />
  </ns1:prop>
  <ns1:href xmlns:ns1="DAV:">/a</ns1:href>
  <ns1:href xmlns:ns1="DAV:">/b</ns1:href>
</ns0:calendar-multiget>
""".replace("\n", "\r\n")
)


    def test_GenerateXMLMultipleHrefsMultipleProperties(self):

        server = Session("www.example.com")
        request = Multiget(server, "/", ("/a", "/b",), (davxml.getetag, davxml.displayname,))
        os = StringIO()
        request.generateXML(os)
        self.assertEqual(os.getvalue(), """<?xml version='1.0' encoding='utf-8'?>
<ns0:calendar-multiget xmlns:ns0="urn:ietf:params:xml:ns:caldav">
  <ns1:prop xmlns:ns1="DAV:">
    <ns1:getetag />
    <ns1:displayname />
  </ns1:prop>
  <ns1:href xmlns:ns1="DAV:">/a</ns1:href>
  <ns1:href xmlns:ns1="DAV:">/b</ns1:href>
</ns0:calendar-multiget>
""".replace("\n", "\r\n")
)



class TestResponse(unittest.TestCase):
    pass



class TestResponseHeaders(unittest.TestCase):
    pass



class TestResponseBody(unittest.TestCase):
    pass
