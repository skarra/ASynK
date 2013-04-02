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

from caldavclientlibrary.protocol.url import URL

import unittest

class TestURLParse(unittest.TestCase):

    def verifyParts(self, u, s, scheme, server, path, extended):
        self.assertEqual(u.toString(), s)
        self.assertEqual(u.scheme, scheme)
        self.assertEqual(u.server, server)
        self.assertEqual(u.path, path)
        self.assertEqual(u.extended, extended)


    def test_ParsePlain(self):

        s = "http://www.example.com"
        u = URL(url=s)
        self.verifyParts(u, s, "http", "www.example.com", "", "")


    def test_ParsePlainPath(self):

        s = "http://www.example.com/principals/users"
        u = URL(url=s)
        self.verifyParts(u, s, "http", "www.example.com", "/principals/users", "")


    def test_ParsePlainPathExtended(self):

        s = "http://www.example.com/principals/users?test=true"
        u = URL(url=s)
        self.verifyParts(u, s, "http", "www.example.com", "/principals/users", "?test=true")


    def test_ParseMailto(self):

        s = "mailto:user@example.com"
        u = URL(url=s)
        self.verifyParts(u, s, "mailto", "user@example.com", "", "")
