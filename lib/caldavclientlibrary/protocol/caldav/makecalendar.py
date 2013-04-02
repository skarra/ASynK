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
from caldavclientlibrary.protocol.caldav.definitions import methods
from StringIO import StringIO
from caldavclientlibrary.protocol.http.data.string import RequestDataString
from xml.etree.ElementTree import Element
from caldavclientlibrary.protocol.caldav.definitions import caldavxml
from xml.etree.ElementTree import SubElement
from caldavclientlibrary.protocol.webdav.definitions import davxml
from caldavclientlibrary.protocol.utils.xmlhelpers import BetterElementTree

class MakeCalendar(RequestResponse):

    def __init__(self, session, url, displayname=None, description=None, timezone=None):
        super(MakeCalendar, self).__init__(session, methods.MKCALENDAR, url)
        self.displayname = displayname
        self.description = description
        self.timezone = timezone

        self.initRequestData()


    def initRequestData(self):
        if self.displayname or self.description or self.timezone:
            # Write XML info to a string
            os = StringIO()
            self.generateXML(os)
            self.request_data = RequestDataString(os.getvalue(), "text/xml charset=utf-8")


    def generateXML(self, os):
        # Structure of document is:
        #
        # <CALDAV:mkcalendar>
        #   <DAV:prop>
        #     <<each property as elements>>
        #   </DAV:prop>
        # </CALDAV:mkcalendar>

        # <CALDAV:mkcalendar> element
        mkcalendar = Element(caldavxml.mkcalendar)

        # <DAV:prop> element
        prop = SubElement(mkcalendar, davxml.prop)

        # <DAV:displayname> element
        if self.displayname:
            displayname = SubElement(prop, davxml.displayname)
            displayname.text = self.displayname

        # <CalDAV:calendar-description> element
        if self.description:
            description = SubElement(prop, caldavxml.calendar_description)
            description.text = self.description

        # <CalDAV:timezone> element
        if self.timezone:
            timezone = SubElement(prop, caldavxml.calendar_timezone)
            timezone.text = self.timezone

        # Now we have the complete document, so write it out (no indentation)
        xmldoc = BetterElementTree(mkcalendar)
        xmldoc.writeUTF8(os)
