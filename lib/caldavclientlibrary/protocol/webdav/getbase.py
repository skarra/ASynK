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


class GetBase(RequestResponse):

    def __init__(self, session, url, lock=None, head=False):
        super(GetBase, self).__init__(session, methods.HEAD if head else methods.GET, url, lock=lock)
        self.head = head


    def setData(self, response_data, etag=None):
        self.request_data = None
        self.response_data = response_data

        # Must have matching ETag
        if etag:
            self.etag = etag
            self.etag_match = True


    def getNewETag(self):
        # Get the ETag header from response headers
        if self.hasResponseHeader(headers.ETag):
            return self.getResponseHeader(headers.ETag)
        else:
            return None


    def getContentLength(self):
        # Always zero to prevent attempt to read response
        return 0 if self.head else self.content_length


    def getChunked(self):
        # Always false to prevent attempt to read response
        return False if self.head else self.chunked
