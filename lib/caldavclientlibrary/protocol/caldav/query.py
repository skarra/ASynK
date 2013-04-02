##
# Copyright (c) 2012-2013 Apple Inc. All rights reserved.
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
from caldavclientlibrary.protocol.caldav.definitions import caldavxml
from caldavclientlibrary.protocol.http.data.string import RequestDataString
from caldavclientlibrary.protocol.utils.xmlhelpers import BetterElementTree
from caldavclientlibrary.protocol.webdav.definitions import davxml
from caldavclientlibrary.protocol.webdav.report import Report
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

class Query(Report):

    def __init__(self, session, url, props=()):
        super(Query, self).__init__(session, url)
        self.props = props

        self.initRequestData()


    def initRequestData(self):
        # Write XML info to a string
        os = StringIO()
        self.generateXML(os)
        self.request_data = RequestDataString(os.getvalue(), "text/xml charset=utf-8")


    def generateXML(self, os):
        # Structure of document is:
        #
        # <CalDAV:calendar-query>
        #   <DAV:prop>
        #     <<names of each property as elements>>
        #   </DAV:prop>
        #   <CALDAV:filter>...</CALDAV:filter>
        # </CalDAV:calendar-query>

        # <CalDAV:calendar-query> element
        query = Element(caldavxml.calendar_query)

        self.addProps(query)

        # Now add each href
        self.addFilterElement(query)

        # Now we have the complete document, so write it out (no indentation)
        xmldoc = BetterElementTree(query)
        xmldoc.writeUTF8(os)


    def addProps(self, query):
        """
        Add properties to the query XML.
        """

        if self.props:
            # <DAV:prop> element
            prop = SubElement(query, davxml.prop)

            # Now add each property
            for propname in self.props:
                # Add property element taking namespace into account
                SubElement(prop, propname)


    def addFilterElement(self, query):
        """
        Add a CALDAV:filter element to the specified CALDAV:calendar-query element.
        Sub-classes must override to add specific types of query
        """
        raise NotImplementedError



class QueryVEVENTTimeRange(Query):

    def __init__(self, session, url, trstart, trend, expand, props=()):

        self.trstart = trstart
        self.trend = trend
        self.expand = expand

        super(QueryVEVENTTimeRange, self).__init__(session, url, props)


    def addProps(self, query):
        """
        Add properties to the query XML.
        """

        if self.props or self.expand:
            # <DAV:prop> element
            prop = SubElement(query, davxml.prop)

            # Now add each property
            for propname in self.props:
                # Add property element taking namespace into account
                SubElement(prop, propname)

            # Now do expand
            if self.expand:
                cdata = SubElement(prop, caldavxml.calendar_data)
                SubElement(cdata, caldavxml.expand, {"start": self.trstart, "end": self.trend})


    def addFilterElement(self, query):
        """
        Add a CALDAV:filter element to the specified CALDAV:calendar-query element.
        Sub-classes must override to add specific types of query
        """

        # Structure of document is:
        #
        # <CalDAV:filter>
        #   <CALDAV:component-filter name="VCALENDAR">
        #     <CALDAV:component-filter name="VEVENT">
        #       <CALDAV:time-range start="..." end="...">
        #       </CALDAV:time-range>
        #     </CALDAV:component-filter>
        #   </CALDAV:component-filter>
        # </CalDAV:filter>

        filter = SubElement(query, caldavxml.filter)
        calcompfilter = SubElement(filter, caldavxml.comp_filter, {"name": "VCALENDAR"})
        eventcompfilter = SubElement(calcompfilter, caldavxml.comp_filter, {"name": "VEVENT"})

        tr = {}
        if self.trstart:
            tr["start"] = self.trstart
        if self.trend:
            tr["end"] = self.trend
        SubElement(eventcompfilter, caldavxml.time_range, tr)
