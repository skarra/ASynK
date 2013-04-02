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

from caldavclientlibrary.protocol.http.util import parsequoted
from caldavclientlibrary.protocol.http.util import parsetoken
from caldavclientlibrary.protocol.http.util import parseStatusLine

import unittest

class TestParseQuoted(unittest.TestCase):

    def testParseQuotedOK(self):

        data = {
            "\"\""                                  : ("", ""),
            "\"quoted\""                            : ("quoted", ""),
            "\"quoted words\""                      : ("quoted words", ""),
            "\"quoting a \\\"word\\\"\""            : ("quoting a \"word\"", ""),
            "\"\" after"                            : ("", "after"),
            "\"quoted\" after"                      : ("quoted", "after"),
            "\"quoted words\" after"                : ("quoted words", "after"),
            "\"quoting a \\\"word\\\"\" after"      : ("quoting a \"word\"", "after"),
            "\"quoting a \\\"word\\\" after\" after": ("quoting a \"word\" after", "after"),
            "\"quoted\"after"                       : ("quoted", "after"),
            "\""                                    : ("", ""),
            "\"unterminated"                        : ("unterminated", ""),
            "\"unterminated words"                  : ("unterminated words", ""),
            "\"unterminated a \\\"word\\\""         : ("unterminated a \"word\"", ""),
         }

        for input, result in data.iteritems():
            self.assertEqual(parsequoted(input), result)


    def testParseQuotedBAD(self):

        data = (
            "",
            "unquoted",
            "unquoted \"quoted\"",
        )

        for input in data:
            self.assertRaises(AssertionError, parsequoted, input)



class TestParseToken(unittest.TestCase):

    def testParseTokenOK(self):

        data = {
            ""                                      : ("", ""),
            "unquoted"                              : ("unquoted", ""),
            "unquoted words"                        : ("unquoted", "words"),
            "unquoted  words"                       : ("unquoted", "words"),
            "unquoting a \"word\""                  : ("unquoting", "a \"word\""),
            "unquoted\twords"                       : ("unquoted", "words"),
            "unquoting\ta \"word\""                 : ("unquoting", "a \"word\""),
            "unquoted: words"                       : ("unquoted", "words"),
            "unquoting: a \"word\""                 : ("unquoting", "a \"word\""),

            "\"\""                                  : ("", ""),
            "\"quoted\""                            : ("quoted", ""),
            "\"quoted words\""                      : ("quoted words", ""),
            "\"quoting a \\\"word\\\"\""            : ("quoting a \"word\"", ""),
            "\"\" after"                            : ("", "after"),
            "\"quoted\" after"                      : ("quoted", "after"),
            "\"quoted words\" after"                : ("quoted words", "after"),
            "\"quoting a \\\"word\\\"\" after"      : ("quoting a \"word\"", "after"),
            "\"quoting a \\\"word\\\" after\" after": ("quoting a \"word\" after", "after"),
            "\"quoted\"after"                       : ("quoted", "after"),
            "\""                                    : ("", ""),
            "\"unterminated"                        : ("unterminated", ""),
            "\"unterminated words"                  : ("unterminated words", ""),
            "\"unterminated a \\\"word\\\""         : ("unterminated a \"word\"", ""),
        }

        for input, result in data.iteritems():
            self.assertEqual(parsetoken(input, " \t:"), result)



class TestParseStatusLine(unittest.TestCase):

    def testParseTokenOK(self):
        self.assertEqual(parseStatusLine("HTTP/1.1 200 OK"), 200)


    def testParseTokenBadStatus(self):
        self.assertEqual(parseStatusLine("HTTP/1.2 2001 OK"), 0)


    def testParseTokenBadVersion(self):
        self.assertEqual(parseStatusLine("HTTP/1.2 200 OK"), 0)


    def testParseTokenBadNumber(self):
        self.assertEqual(parseStatusLine("HTTP/1.1 OK"), 0)


    def testParseTokenBad(self):
        self.assertEqual(parseStatusLine("HTTP/1.1"), 0)
