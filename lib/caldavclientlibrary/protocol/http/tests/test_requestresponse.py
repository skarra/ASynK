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

from caldavclientlibrary.protocol.http.requestresponse import RequestResponse
from caldavclientlibrary.protocol.http.session import Session
from caldavclientlibrary.protocol.http.data.string import RequestDataString
from caldavclientlibrary.protocol.http.authentication.basic import Basic
from caldavclientlibrary.protocol.http.definitions import methods

import unittest

class TestRequestHeaders(unittest.TestCase):

    def test_NoEtag(self):

        server = Session("www.example.com")
        request = RequestResponse(server, methods.GET, "/")
        self.assertEqual(request.generateRequestHeader(), """GET / HTTP/1.1
Host: www.example.com

""".replace("\n", "\r\n")
)


    def test_EtagMatch(self):

        server = Session("www.example.com")
        request = RequestResponse(server, methods.GET, "/", "\"etag\"", True)
        self.assertEqual(request.generateRequestHeader(), """GET / HTTP/1.1
Host: www.example.com
If-Match: "etag"

""".replace("\n", "\r\n")
)


    def test_EtagNoneMatch(self):

        server = Session("www.example.com")
        request = RequestResponse(server, methods.GET, "/", "\"etag\"", False)
        self.assertEqual(request.generateRequestHeader(), """GET / HTTP/1.1
Host: www.example.com
If-None-Match: "etag"

""".replace("\n", "\r\n")
)


    def test_Content(self):

        server = Session("www.example.com")
        request = RequestResponse(server, methods.GET, "/")
        rawdata = "Here is some data\r\non multiple lines."
        data = RequestDataString(rawdata, "text/plain")
        request.setData(data, None)
        self.assertEqual(request.generateRequestHeader(), """GET / HTTP/1.1
Host: www.example.com
Content-Length: %d
Content-Type: text/plain

""".replace("\n", "\r\n") % (len(rawdata),)
)


    def test_ContentAndAuthorization(self):

        server = Session("www.example.com")
        server.authorization = Basic("user", "pswd")
        request = RequestResponse(server, methods.GET, "/")
        rawdata = "Here is some data\r\non multiple lines."
        data = RequestDataString(rawdata, "text/plain")
        request.setData(data, None)
        self.assertEqual(request.generateRequestHeader(), """GET / HTTP/1.1
Host: www.example.com
Authorization: Basic dXNlcjpwc3dk
Content-Length: %d
Content-Type: text/plain

""".replace("\n", "\r\n") % (len(rawdata),)
)
