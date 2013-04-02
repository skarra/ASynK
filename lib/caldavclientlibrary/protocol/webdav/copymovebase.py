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

class CopyMoveBase(RequestResponse):

    def __init__(self, session, url_old, absurl_new, overwrite=False, delete_original=True):
        super(CopyMoveBase, self).__init__(session, methods.MOVE if delete_original else methods.COPY, url_old)
        self.absurl_new = absurl_new
        self.overwrite = overwrite


    def setData(self, etag):
        self.request_data = None
        self.response_data = None

        # Must have matching ETag
        if etag:
            self.etag = etag
            self.etag_match = True


    def addHeaders(self, hdrs):
        # Do default
        super(CopyMoveBase, self).addHeaders(hdrs)

        # Add Destination header
        hdrs.append((headers.Destination, self.absurl_new))

        # Add Overwrite header
        hdrs.append((headers.Overwrite, headers.OverwriteTrue if self.overwrite else headers.OverwriteFalse))
