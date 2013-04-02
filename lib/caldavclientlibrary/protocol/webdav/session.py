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

from caldavclientlibrary.protocol.http.data.string import ResponseDataString
from caldavclientlibrary.protocol.http.definitions import methods
from caldavclientlibrary.protocol.http.definitions import statuscodes
from caldavclientlibrary.protocol.http.requestresponse import RequestResponse
from caldavclientlibrary.protocol.http.session import Session as HTTPSession
from caldavclientlibrary.protocol.webdav.definitions import headers

class Session(HTTPSession):

    def __init__(self, server, port=None, ssl=False, log=None):
        super(Session, self).__init__(server, port, ssl, log)
        self.initialised = False
        self.version = ()

        # Features for entire session
        self.useBriefHeader = True


    def initialise(self, host, base_uri):
        # Set host change
        self.setServer(host)

        # Loop repeating until we can do it or get a fatal error
        first_time = True
        while True:

            # Create OPTIONS request for the base_uri
            request = RequestResponse(self, methods.OPTIONS, base_uri)
            request.setSession(self)
            sout = ResponseDataString()
            request.setData(None, sout)

            # Add request and process it
            self.sendRequest(request)

            # Check response
            if request.getStatusCode() == statuscodes.Unauthorized:

                # If we had authorization before, then chances are auth details are wrong - so delete and try again with new auth
                if self.hasAuthorization():

                    self.authorization = None

                    # Display error so user knows why the prompt occurs again
                    self.displayHTTPError(request)

                # Get authorization object (prompt the user) and redo the request
                self.authorization, cancelled = self.getAuthorizor(first_time, request.getResponseHeaders(headers.WWWAuthenticate))

                # Check for auth cancellation
                if cancelled:

                    self.authorization = None
                    return False

                first_time = False

                # Repeat the request loop with new authorization
                continue

            # Look for success and exit loop for further processing
            if request.getStatusCode() in (statuscodes.OK, statuscodes.NoContent):

                # Grab the server string
                if request.hasResponseHeader(headers.Server):
                    self.setServerDescriptor = self.setServerDescriptor(request.getResponseHeader(headers.Server))

                # Now check the response headers for a DAV version (may be more than one)
                self.version = ()
                for dav_version in request.getResponseHeaders(headers.DAV):

                    # Tokenize on commas
                    for token in dav_version.split(","):

                        token = token.strip()
                        self.addVersion(token)

                self.setServerType(self.version)

                # Put other strings into capability
                capa = ""
                for name, value in request.getResponseHeaders().iteritems():

                    if (not name.lower().startswith(headers.Server) and
                        not name.lower().startswith(headers.Date) and
                        name.lower().startswith("Content-")):

                        capa += "%s: %s\n" % (name, value,)

                self.setServerCapability(capa)

                # Just assume any version is fine for now
                break

            # If we get here we had some kind of fatal error
            self.handleHTTPError(request)
            return False

        self.initialised = True

        return True


    def addVersion(self, token):
        self.version += (token,)


    def hasDAVVersion(self, version):
        return version in self.version


    def hasDAV(self):
        return self.hasDAVVersion(headers.DAV1)


    def hasDAVLocking(self):
        return self.hasDAVVersion(headers.DAV2) or self.hasDAVVersion(headers.DAVbis)


    def hasDAVACL(self):
        return self.hasDAVVersion(headers.DAVACL)


    def getAuthorizor(self, first_time, www_authenticate):
        raise NotImplementedError


    def setServerType(self, type):
        raise NotImplementedError


    def setServerDescriptor(self, txt):
        raise NotImplementedError


    def setServerCapability(self, txt):
        raise NotImplementedError
