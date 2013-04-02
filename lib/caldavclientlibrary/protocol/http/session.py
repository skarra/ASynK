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

from httplib import InvalidURL
import httplib

class Session(object):

    STATE_OPEN = 0
    STATE_CLOSED = 1

    def __init__(self, server, port=None, ssl=False, log=None):

        self.server = server
        self.port = port
        self.ssl = ssl
        if not self.port:
            self.port = httplib.HTTPS_PORT if ssl else httplib.HTTP_PORT
        self.authorization = None
        self.connection_state = Session.STATE_CLOSED
        self.log = log


    def hasAuthorization(self):
        return self.authorization != None


    def getAuthorization(self):
        return self.authorization


    def addHeaders(self, hdrs, request):
        if self.hasAuthorization():
            self.getAuthorization().addHeaders(hdrs, request)


    def setServer(self, server, port=None):

        if port is None:
            i = server.rfind(':')
            j = server.rfind(']')
            if i > j:
                try:
                    port = int(server[i + 1:])
                except ValueError:
                    raise InvalidURL("nonnumeric port: '%s'" % server[i + 1:])
                server = server[:i]
            else:
                port = httplib.HTTPS_PORT if self.ssl else httplib.HTTP_PORT
            if server and server[0] == '[' and server[-1] == ']':
                server = server[1:-1]

        if self.server != server:
            self.server = server
            self.port = port

            # Always clear out authorization when host changes
            self.authorization = None


    def sendRequest(self, request):
        try:

            # First need a connection
            self.needConnection()

            # Now do the connection
            self.doRequest(request)

            # Check the final connection state and close if that's what the server wants
            if request.getConnectionClose():
                self.closeConnection()

        except Exception:

            # log.err(e)
            self.connection_state = Session.STATE_CLOSED
            raise


    def handleHTTPError(self, request):
        raise NotImplementedError


    def displayHTTPError(self, request):
        raise NotImplementedError


    def isConnectionOpen(self):
        return self.connection_state == Session.STATE_OPEN


    def needConnection(self):
        if not self.isConnectionOpen():
            self.openConnection()


    def openConnection(self):
        if not self.isConnectionOpen():
            self.openSession()
            self.connection_state = Session.STATE_OPEN


    def closeConnection(self):
        if self.isConnectionOpen():
            self.closeSession()
            self.connection_state = Session.STATE_CLOSED


    def openSession(self):
        raise NotImplementedError


    def closeSession(self):
        raise NotImplementedError


    def runSession(self, request):
        raise NotImplementedError


    def doRequest(self, request):
        raise NotImplementedError
