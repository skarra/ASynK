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

from caldavclientlibrary.client.httpshandler import SmartHTTPConnection
from caldavclientlibrary.protocol.webdav.session import Session
from caldavclientlibrary.protocol.webdav.options import Options

def run(session, request):

    # Create connection
    connect = SmartHTTPConnection(session.server, session.port, session.ssl)
    connect.set_debuglevel(1)

    # Do headers
    connect.putrequest(request.method, request.url, skip_host=True, skip_accept_encoding=True)
    hdrs = request.getRequestHeaders()
    for header, value in hdrs.iteritems():
        connect.putheader(header, value)
    connect.endheaders()

    # Do request body
    stream = request.getRequestDataStream()
    if stream:
        stream.start()
        more = True
        while more:
            data, more = stream.read()
            if data:
                connect.send(data)
        stream.stop()

    # Get response
    response = connect.getresponse()

    # Get response headers
    request.setResponseStatus(response.version, response.status, response.reason)
    request.setResponseHeaders(response.getheaders())

    # Get response body


if __name__ == '__main__':
    session = Session("www.mulberrymail.com")
    request = Options(session, "/")

    run(session, request)
