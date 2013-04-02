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
from caldavclientlibrary.protocol.webdav.unlock import Unlock

import unittest

class TestRequest(unittest.TestCase):

    def test_Method(self):

        server = Session("www.example.com")
        request = Unlock(server, "/", "locked-up-in-chains")
        self.assertEqual(request.getMethod(), "UNLOCK")



class TestRequestHeaders(unittest.TestCase):

    def test_LockTokenHeaders(self):

        server = Session("www.example.com")
        request = Unlock(server, "/", "locked-up-in-chains")
        hdrs = request.generateRequestHeader()
        self.assertTrue("Lock-Token: <locked-up-in-chains>" in hdrs)



class TestRequestBody(unittest.TestCase):
    pass



class TestResponse(unittest.TestCase):
    pass



class TestResponseHeaders(unittest.TestCase):
    pass



class TestResponseBody(unittest.TestCase):
    pass
