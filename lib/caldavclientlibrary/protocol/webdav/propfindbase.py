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
from caldavclientlibrary.protocol.webdav.definitions import headers
from caldavclientlibrary.protocol.webdav.definitions import methods
from caldavclientlibrary.protocol.webdav.requestresponse import RequestResponse

class PropFindBase(RequestResponse):

    def __init__(self, session, url, depth):
        assert(depth in (headers.Depth0, headers.Depth1, headers.DepthInfinity))

        super(PropFindBase, self).__init__(session, methods.PROPFIND, url)
        self.depth = depth


    def initRequestData(self):
        # Write XML info to a string
        os = StringIO()
        self.generateXML(os)
        self.request_data = RequestDataString(os.getvalue(), "text/xml; charset=utf-8")


    def setOutput(self, response_data):
        self.response_data = response_data


    def addHeaders(self, hdrs):
        # Do default
        super(PropFindBase, self).addHeaders(hdrs)

        # Add depth header
        hdrs.append((headers.Depth, self.depth))

        # Optional ones
        if self.session.useBriefHeader:
            hdrs.append((headers.Brief, "t"))


    def generateXML(self, os):
        raise NotImplementedError
