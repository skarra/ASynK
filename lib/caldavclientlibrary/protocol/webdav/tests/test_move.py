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

from caldavclientlibrary.protocol.http.session import Session
from caldavclientlibrary.protocol.webdav.move import Move

import unittest

class TestRequest(unittest.TestCase):

    def test_Method(self):

        server = Session("www.example.com")
        request = Move(server, "/a", "http://www.example.com/b")
        self.assertEqual(request.getMethod(), "MOVE")



class TestRequestHeaders(unittest.TestCase):

    def test_NoSpecialHeaders(self):

        server = Session("www.example.com")
        request = Move(server, "/a", "http://www.example.com/b")
        hdrs = request.generateRequestHeader()
        self.assertFalse("If-None-Match:" in hdrs)
        self.assertFalse("If-Match:" in hdrs)
        self.assertTrue("Overwrite: F" in hdrs)
        self.assertTrue("Destination: http://www.example.com/b" in hdrs)


    def test_IfMatchHeader(self):

        server = Session("www.example.com")
        request = Move(server, "/a", "http://www.example.com/b")
        request.setData(etag="\"12345\"")
        hdrs = request.generateRequestHeader()
        self.assertFalse("If-None-Match:" in hdrs)
        self.assertTrue("If-Match: \"12345\"" in hdrs)
        self.assertTrue("Overwrite: F" in hdrs)
        self.assertTrue("Destination: http://www.example.com/b" in hdrs)


    def test_OverwriteHeader(self):

        server = Session("www.example.com")
        request = Move(server, "/a", "http://www.example.com/b", overwrite=True)
        hdrs = request.generateRequestHeader()
        self.assertFalse("If-None-Match:" in hdrs)
        self.assertFalse("If-Match:" in hdrs)
        self.assertTrue("Overwrite: T" in hdrs)
        self.assertTrue("Destination: http://www.example.com/b" in hdrs)



class TestRequestBody(unittest.TestCase):
    pass



class TestResponse(unittest.TestCase):
    pass



class TestResponseHeaders(unittest.TestCase):
    pass



class TestResponseBody(unittest.TestCase):
    pass
