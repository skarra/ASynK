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

class Put(RequestResponse):

    def __init__(self, session, url, lock=None):
        super(Put, self).__init__(session, methods.PUT, url, lock=lock)


    def setData(self, request_data, response_data, etag=None, new_item=False):
        assert(not (etag and new_item))
        self.request_data = request_data
        self.response_data = response_data

        # Must have matching ETag
        if etag:
            self.etag = etag
            self.etag_match = True

        # ETag should be '*' and we add If-None-Match header to ensure we do not overwrite something already there
        if new_item:
            self.etag = "*"
            self.etag_match = False


    def getNewETag(self):
        # Get the ETag header from response headers
        if self.hasResponseHeader(headers.ETag):
            return self.getResponseHeader(headers.ETag)
        else:
            return None
