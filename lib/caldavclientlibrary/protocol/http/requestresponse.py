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

from StringIO import StringIO
from caldavclientlibrary.protocol.http.definitions import headers
from caldavclientlibrary.protocol.http.definitions import methods
from caldavclientlibrary.protocol.http.definitions import statuscodes

class ResponseError(Exception):
    pass



class RequestResponse(object):

    def __init__(self, session, method, url, etag=None, etag_match=False):
        self._initResponse()
        self.session = session
        self.method = method
        self.url = url
        self.etag = etag
        self.etag_match = etag_match


    def _initResponse(self):
        self.session = None
        self.request_data = None
        self.request_headers = {}
        self.response_data = None
        self.method = methods.GET
        self.url = None
        self.etag = None
        self.etag_match = False
        self.status_code = statuscodes.Unknown
        self.status_reason = None
        self.headers = {}
        self.connection_close = False
        self.content_length = 0
        self.chunked = False
        self.completed = False


    def setSession(self, session):
        self.session = session


    def getSession(self):
        return self.session


    def getMethod(self):
        return self.method


    def setURL(self, ruri):
        self.url = ruri


    def getURL(self):
        return self.url


    def setETag(self, etag, etag_match):
        self.etag = etag
        self.etag_match = etag_match


    def queuedForSending(self, session):
        self.session = session


    def setRequestHeader(self, name, value):
        self.request_headers[name] = value


    def setData(self, request_data, response_data):
        self.request_data = request_data
        self.response_data = response_data


    def hasRequestData(self):
        return self.request_data != None


    def hasResponseData(self):
        return self.response_data != None


    def getRequestData(self):
        if self.request_data:
            return self.request_data
        else:
            return None


    def getResponseData(self):
        if self.response_data:
            return self.response_data
        else:
            return None


    def getRequestStartLine(self):
        return "%s %s HTTP/1.1" % (self.method, self.url,)


    def getRequestHeaders(self):
        # This will be overridden by sub-classes that add headers - those classes should
        # call this class's implementation to write out the basic set of headers
        result = []
        self.addHeaders(result)
        return tuple(result)


    def generateRequestHeader(self):
        os = StringIO()
        os.write("%s\r\n" % (self.getRequestStartLine(),))
        for header, value in self.getRequestHeaders():
            os.write("%s: %s\r\n" % (header, value,))
        os.write("\r\n")
        return os.getvalue()


    def addHeaders(self, hdrs):

        # Write host
        hdrs.append((headers.Host, "%s:%s" % (self.session.server, self.session.port,)))

        # Do ETag matching
        if self.etag:
            if self.etag_match:
                hdrs.append((headers.IfMatch, self.etag))
            else:
                hdrs.append((headers.IfNoneMatch, self.etag))

        # Do session global headers
        self.session.addHeaders(hdrs, self)

        # Check for content
        self.addContentHeaders(hdrs)

        # Do custom headers
        for name, value in self.request_headers.items():
            hdrs.append((name, value))


    def addContentHeaders(self, hdrs):
        # Check for content
        if self.hasRequestData():
            hdrs.append((headers.ContentLength, str(self.request_data.getContentLength())))
            hdrs.append((headers.ContentType, self.request_data.getContentType()))


    def setResponseStatus(self, version, status, reason):
        self.status_code = status
        self.status_reason = reason


    def setResponseHeaders(self, hdrs):
        for header in hdrs:
            splits = header.split(":", 1)
            self.headers.setdefault(splits[0].strip().lower(), []).append(splits[1].strip())

        # Now cache some useful header values
        self.cacheHeaders()


    def clearResponse(self):
        self.etag_match = False
        self.status_code = statuscodes.Unknown
        self.status_reason = None
        self.headers = {}
        self.connection_close = False
        self.content_length = 0
        self.chunked = False
        self.completed = False

        if self.response_data:
            self.response_data.clear()


    def getStatusCode(self):
        return self.status_code


    def getStatusReason(self):
        return self.status_reason


    def getConnectionClose(self):
        return self.connection_close


    def getContentLength(self):
        return self.content_length


    def getChunked(self):
        return self.chunked


    def setComplete(self):
        self.completed = True


    def getCompleted(self):
        return self.completed


    def hasResponseHeader(self, hdr):
        return hdr.lower() in self.headers


    def getResponseHeader(self, hdr):
        if hdr.lower() in self.headers:
            return self.headers[hdr.lower()][0]
        else:
            return ""


    def getResponseHeaders(self, hdr=None):
        if hdr:
            if hdr.lower() in self.headers:
                return self.headers[hdr.lower()]
            else:
                return ()
        else:
            return self.headers


    def isRedirect(self):
        # Only these are allowed
        return self.status_code in (statuscodes.MovedPermanently, statuscodes.Found, statuscodes.TemporaryRedirect)


    def parseStatusLine(self, line):

        # Must have 'HTTP/' version at start
        if line[0:5] != "HTTP/":
            raise ResponseError("status line incorrect at start")

        # Must have version '1.1 '
        if line[5:9] != "1.1 ":
            raise ResponseError("incorrect http version in status line")

        # Must have three digits followed by nothing or one space
        if not line[9:12].isdigit() or (len(line) > 12 and line[12] != " "):
            raise ResponseError("invalid status response code syntax")

        # Read in the status code
        self.status_code = int(line[9:12])

        # Remainder is reason
        if len(line) > 13:
            self.status_reason = line[13:]


    def readFoldedLine(self, instream, line1, line2, log):
        # If line2 already has data, transfer that into line1
        if line2 or line1:
            line1 = line2
        else:
            # Fill first line
            line1 = instream.readline()
            if not line1:
                return False, line1, line2
            line1 = line1.rstrip("\r\n")

            if log:
                log.write("%s\n" % (line1,))

        # Terminate on blank line which is end of headers
        if not line1:
            return True, line1, line2

        # Now loop looking ahead at the next line to see if it is folded
        while True:
            # Get next line
            line2 = instream.readline()
            if not line2:
                return True, line1, line2
            line2 = line2.rstrip("\r\n")

            if log:
                log.write("%s\n" % (line2,))

            # Does it start with a space => folded
            if line2 and line2[0].isspace():
                # Copy folded line (without space) to current line and cycle for more
                line1 += line2[1:]
            else:
                # Not folded - just exit loop
                break

        return True, line1, line2


    def cacheHeaders(self):
        # Connection
        if headers.Connection in self.headers:
            value = self.headers[headers.Connection][0]
            self.connection_close = (value.lower() == headers.ConnectionClose)

        # Content-Length
        if headers.ContentLength in self.headers:
            value = self.headers[headers.ContentLength][0]
            self.content_length = int(value)

        # Transfer encoding
        if headers.TransferEncoding in self.headers:
            value = self.headers[headers.TransferEncoding][0]
            self.chunked = (value == headers.TransferEncodingChunked)
