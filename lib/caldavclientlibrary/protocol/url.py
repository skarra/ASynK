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

import os
import urllib

class URL(object):

    eAbsolute = 0
    eRelative = 1
    eLastPath = 2

    URLEscape = '%'
    URLReserved = "/?:@&="
    URLUnreserved = (# Allowable URL chars
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 0 - 15
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 16 - 31
        0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, # 32 - 47
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, # 48 - 63
        0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, # 64 - 79
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, # 80 - 95
        0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, # 96 - 111
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, # 112 - 127
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 128 - 143
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 144 - 159
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 160 - 175
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 176 - 191
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 192 - 207
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 208 - 223
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 224 - 239
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 240 - 255
    )

    URLCharacter = (# Allowable URL chars -- all
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 0 - 15
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 16 - 31
        0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, # 32 - 47
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, # 48 - 63
        0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, # 64 - 79
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, # 80 - 95
        0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, # 96 - 111
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, # 112 - 127
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 128 - 143
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 144 - 159
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 160 - 175
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 176 - 191
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 192 - 207
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 208 - 223
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 224 - 239
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 240 - 255
    )

    URLXCharacter = (# Allowable URL chars (all)
          # RFC2732 uses '[...]' for IPv6 addressing - [] are now allowed
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 0 - 15
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 16 - 31
        0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, # 32 - 47
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, # 48 - 63
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, # 64 - 79
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, # 80 - 95
        0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, # 96 - 111
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, # 112 - 127
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 128 - 143
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 144 - 159
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 160 - 175
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 176 - 191
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 192 - 207
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 208 - 223
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 224 - 239
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, # 240 - 255
    )

    URLSchemeDoubleSlash = ("http", "https", "webcal",)

    def __init__(self, url=None, scheme=None, server=None, path=None, extended=None, decode=False):

        self.scheme = ""
        self.server = ""
        self.path = ""
        self.extended = ""

        if not url:
            self.scheme = scheme
            self.server = server
            self.path = path
            if self.path and decode:
                self.path = urllib.unquote(self.path)
            self.extended = extended
            if self.extended and decode:
                self.extended = urllib.unquote_plus(self.extended)
        else:
            self._parse(url, decode)


    def __str__(self):
        return "URL: %s" % (self.toString(),)


    def __repr__(self):
        return "URL: %s" % (self.toString(),)


    def __cmp__(self, other):
        return cmp(self.toString(), other.toString())


    def absoluteURL(self):
        return self.toString()


    def relativeURL(self):
        return self.toString(conversion=URL.eRelative)


    def toString(self, conversion=eAbsolute, encode=True):

        result = ""

        # Add scheme & host if not relative
        if conversion == URL.eAbsolute and self.scheme and self.server:
            result += self.scheme + ":"
            if self.scheme in URL.URLSchemeDoubleSlash:
                result += "//"
            result += self.server

        # Get path (or last part of it if required)
        if self.path and conversion == URL.eLastPath:
            path = self.path[self.path.rfind("/"):]
        else:
            path = self.path

        # Now encode if required
        if path:
            result += (urllib.quote(path) if encode else path)

        if self.extended:
            result += (urllib.quote_plus(self.extended, "?&=") if encode else self.extended)

        return result


    def equal(self, comp):
        # Compare each component

        if self.scheme != comp.scheme:
            return False

        if self.server != comp.server:
            return False

        # Ignore trailing slash
        if self.path.rstrip("/") != comp.path.rstrip("/"):
            return False

        return True


    def equalRelative(self, comp):
        # Must be relative
        if comp.server:
            return False

        # Just compare paths, ignore trailing slash
        return self.path.rstrip("/") == comp.path.rstrip("/")


    def dirname(self):
        if self.path:
            newpath = os.path.dirname(self.path.rstrip("/")) + "/"
        return URL(scheme=self.scheme, server=self.server, path=newpath)


    def _parse(self, url, decode=False):

        # Strip off main scheme
        if url.lower().startswith("url:"):
            url = url[4:]

        # Special - if it starts with "/" its a relative HTTP url
        if url[0] == '/':
            self.scheme = "http"
            self.server = None
            self._parsePath(url, decode)
        else:
            # Get protocol scheme
            self.scheme = url[:url.find(":")].lower()
            url = url[len(self.scheme):]

            if self.scheme in URL.URLSchemeDoubleSlash:

                assert(url.startswith("://"))

                # Look for server
                splits = url[3:].split("/", 1)
                self.server = splits[0]
                if len(splits) == 2:
                    self._parsePath("/" + splits[1], decode)

            elif self.scheme in ("mailto", "urn",):

                assert(url.startswith(":"))

                # Look for server
                self.server = url[1:]


    def _parsePath(self, path, decode=False):

        # Look for extended bits
        splits = path.split("?", 1)
        self.path = splits[0]
        if decode:
            self.path = urllib.unquote(self.path)
        if len(splits) == 2:
            self.extended = "?" + splits[1]
            if decode:
                self.extended = urllib.unquote_plus(self.extended)
