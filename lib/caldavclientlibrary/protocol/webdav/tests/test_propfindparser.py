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

from caldavclientlibrary.protocol.webdav.propfindparser import PropFindParser
from xml.etree.ElementTree import XML
from caldavclientlibrary.protocol.webdav.definitions import davxml
import unittest

class TestRequest(unittest.TestCase):

    def parseXML(self, x):

        x = x.replace("\n", "\r\n")

        # Parse the XML data
        p = PropFindParser()
        p.parse(XML(x))
        return p


    def checkResource(self, parser, resource, properties):
        result = parser.getResults().get(resource, None)
        self.assertTrue(result is not None)
        for prop, value in properties:
            self.assertEqual(result.getTextProperties().get(prop, None), value)


    def test_SinglePropSingleResource(self):

        parser = self.parseXML("""<?xml version='1.0' encoding='utf-8'?>
<ns0:multistatus xmlns:ns0="DAV:">
  <ns0:response>
    <ns0:href>/principals/users/a</ns0:href>
    <ns0:propstat>
      <ns0:prop>
        <ns0:getetag>12345</ns0:getetag>
      </ns0:prop>
      <ns0:status>HTTP/1.1 200 OK</ns0:status>
    </ns0:propstat>
  </ns0:response>
</ns0:multistatus>
""")

        self.checkResource(parser, "/principals/users/a", (
            (davxml.getetag, "12345",),
        ))


    def test_MultiplePropsSingleResource(self):

        parser = self.parseXML("""<?xml version='1.0' encoding='utf-8'?>
<ns0:multistatus xmlns:ns0="DAV:">
  <ns0:response>
    <ns0:href>/principals/users/a</ns0:href>
    <ns0:propstat>
      <ns0:prop>
        <ns0:displayname>Name</ns0:displayname>
        <ns0:getetag>12345</ns0:getetag>
      </ns0:prop>
      <ns0:status>HTTP/1.1 200 OK</ns0:status>
    </ns0:propstat>
  </ns0:response>
</ns0:multistatus>
""")

        result = parser.getResults().get("/principals/users/a", None)
        self.assertTrue(result is not None)
        self.assertEqual(result.getTextProperties().get(davxml.getetag, None), "12345")
        self.assertEqual(result.getTextProperties().get(davxml.displayname, None), "Name")

        self.checkResource(parser, "/principals/users/a", (
            (davxml.getetag, "12345",),
            (davxml.displayname, "Name",),
        ))


    def test_MultiplePropsSingleMultipleResources(self):

        parser = self.parseXML("""<?xml version='1.0' encoding='utf-8'?>
<ns0:multistatus xmlns:ns0="DAV:">
  <ns0:response>
    <ns0:href>/principals/users/a</ns0:href>
    <ns0:propstat>
      <ns0:prop>
        <ns0:displayname>Name1</ns0:displayname>
        <ns0:getetag>1</ns0:getetag>
      </ns0:prop>
      <ns0:status>HTTP/1.1 200 OK</ns0:status>
    </ns0:propstat>
  </ns0:response>
  <ns0:response>
    <ns0:href>/principals/users/b</ns0:href>
    <ns0:propstat>
      <ns0:prop>
        <ns0:displayname>Name2</ns0:displayname>
        <ns0:getetag>2</ns0:getetag>
      </ns0:prop>
      <ns0:status>HTTP/1.1 200 OK</ns0:status>
    </ns0:propstat>
  </ns0:response>
</ns0:multistatus>
""")

        self.checkResource(parser, "/principals/users/a", (
            (davxml.getetag, "1",),
            (davxml.displayname, "Name1",),
        ))

        self.checkResource(parser, "/principals/users/b", (
            (davxml.getetag, "2",),
            (davxml.displayname, "Name2",),
        ))


    def test_ResourceNotFound(self):
        parser = self.parseXML("""<?xml version='1.0' encoding='UTF-8'?>
<multistatus xmlns='DAV:'>
  <response>
    <href>/calendars/__uids__/user01/inbox/event.ics</href>
    <status>HTTP/1.1 404 Not Found</status>
  </response>
</multistatus>
""")
        results = parser.getResults()
        result = results["/calendars/__uids__/user01/inbox/event.ics"]
        self.assertEqual("HTTP/1.1 404 Not Found", result.getStatus())
