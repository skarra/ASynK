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
from caldavclientlibrary.protocol.caldav.makecalendar import MakeCalendar
from StringIO import StringIO
import unittest

class TestRequest(unittest.TestCase):


    def test_Method(self):

        server = Session("www.example.com")
        request = MakeCalendar(server, "/")
        self.assertEqual(request.getMethod(), "MKCALENDAR")



class TestRequestHeaders(unittest.TestCase):
    pass



class TestRequestBody(unittest.TestCase):

    def test_GenerateXMLDisplayname(self):

        server = Session("www.example.com")
        request = MakeCalendar(server, "/", "home")
        os = StringIO()
        request.generateXML(os)
        self.assertEqual(os.getvalue(), """<?xml version='1.0' encoding='utf-8'?>
<ns0:mkcalendar xmlns:ns0="urn:ietf:params:xml:ns:caldav">
  <ns1:prop xmlns:ns1="DAV:">
    <ns1:displayname>home</ns1:displayname>
  </ns1:prop>
</ns0:mkcalendar>
""".replace("\n", "\r\n")
)


    def test_GenerateXMLMultipleProperties(self):

        server = Session("www.example.com")
        request = MakeCalendar(server, "/", "home", "my personal calendar")
        os = StringIO()
        request.generateXML(os)
        self.assertEqual(os.getvalue(), """<?xml version='1.0' encoding='utf-8'?>
<ns0:mkcalendar xmlns:ns0="urn:ietf:params:xml:ns:caldav">
  <ns1:prop xmlns:ns1="DAV:">
    <ns1:displayname>home</ns1:displayname>
    <ns0:calendar-description>my personal calendar</ns0:calendar-description>
  </ns1:prop>
</ns0:mkcalendar>
""".replace("\n", "\r\n")
)


    def test_GenerateXMLCDATAProperty(self):

        server = Session("www.example.com")
        timezone = """BEGIN:VCALENDAR
PRODID:-//Example Corp.//CalDAV Client//EN
VERSION:2.0
BEGIN:VTIMEZONE
TZID:US-Eastern
LAST-MODIFIED:19870101T000000Z
BEGIN:STANDARD
DTSTART:19671029T020000
RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:Eastern Standard Time (US & Canada)
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:19870405T020000
RRULE:FREQ=YEARLY;BYDAY=1SU;BYMONTH=4
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:Eastern Daylight Time (US & Canada)
END:DAYLIGHT
END:VTIMEZONE
END:VCALENDAR
""".replace("\n", "\r\n")
        request = MakeCalendar(server, "/", timezone=timezone)
        os = StringIO()
        request.generateXML(os)
        self.assertEqual(os.getvalue(), """<?xml version='1.0' encoding='utf-8'?>
<ns0:mkcalendar xmlns:ns0="urn:ietf:params:xml:ns:caldav">
  <ns1:prop xmlns:ns1="DAV:">
    <ns0:calendar-timezone>%s</ns0:calendar-timezone>
  </ns1:prop>
</ns0:mkcalendar>
""".replace("\n", "\r\n") % (timezone.replace("&", "&amp;"),)
)



class TestResponse(unittest.TestCase):
    pass



class TestResponseHeaders(unittest.TestCase):
    pass



class TestResponseBody(unittest.TestCase):
    pass
