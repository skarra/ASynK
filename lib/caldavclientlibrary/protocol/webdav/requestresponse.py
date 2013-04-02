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

from caldavclientlibrary.protocol.http.requestresponse import RequestResponse as HTTPRequestResponse
from caldavclientlibrary.protocol.http.requestresponse import RequestResponse
from caldavclientlibrary.protocol.webdav.definitions import headers

class RequestResponse(HTTPRequestResponse):

    def __init__(self, session, method, ruri, etag=None, etag_match=False, lock=None):
        super(RequestResponse, self).__init__(session, method, ruri, etag, etag_match)
        self.lock = lock


    def setLock(self, lock):
        self.lock = lock


    def addHeaders(self, hdrs):
        # Do inherited
        super(RequestResponse, self).addHeaders(hdrs)

        # Do Lock matching
        if self.lock:
            # This is an untagged token - i.e. it applies to the resource being addressed
            hdrs.append((headers.If, "(<%s>)" % (self.lock,)))
