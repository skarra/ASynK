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

from caldavclientlibrary.protocol.http.authentication.authenticator import Authenticator
from caldavclientlibrary.protocol.http.util import parsetoken
from caldavclientlibrary.protocol.http.definitions import headers
from StringIO import StringIO
import hashlib

class Digest(Authenticator):

    def __init__(self, user, pswd, www_authenticate):
        self.fields = {}
        self.fields['username'] = user
        self.fields['password'] = pswd
        self.parseAuthenticateHeader(www_authenticate)
        self.stale = False
        self.clientCount = 0


    def setDetails(self, user, pswd, www_authenticate):
        self.fields['username'] = user
        self.fields['password'] = pswd
        self.parseAuthenticateHeader(www_authenticate)


    def addHeaders(self, hdrs, request):
        # Generate response
        self.generateResponse(request)

        # Generate header
        os = StringIO()
        os.write("Digest username=\"%s\"," % (self.fields['username'],))
        os.write(" realm=\"%s\"," % (self.fields['realm'],))
        os.write(" nonce=\"%s\"," % (self.fields['nonce'],))
        os.write(" uri=\"%s\"," % (request.getURL(),))
        if "qop" in self.fields:
            os.write(" qop=auth,")
            os.write(" nc=\"%s\"" % (self.fields['nc'],))
            os.write(" cnonce=\"%s\"" % (self.fields['cnonce'],))
        os.write(" response=\"%s\"" % (self.response,))

        if "algorithm" in self.fields:
            os.write(", algorithm=\"%s\"" % (self.fields['algorithm'],))
        if "opaque" in self.fields:
            os.write(", opaque=\"%s\"" % (self.fields['opaque'],))

        hdrs.append((headers.Authorization, os.getvalue()))


    def parseAuthenticateHeader(self, hdrs):
        for hdr in hdrs:

            # Strip any space
            hdr = hdr.strip()

            # Must have Digest token
            if hdr[:7].lower() != "digest ":
                continue
            else:
                hdr = hdr[7:]

            # Get each name/value pair
            while True:
                name, hdr = parsetoken(hdr, " \t=")

                if not name or not hdr:
                    return
                name = name.lower()

                value, hdr = parsetoken(hdr, ", ")
                if not value:
                    return

                if name in ("realm", "domain", "nonce", "opaque", "algorithm", "qop"):
                    self.fields[name] = value

                elif name == "stale":
                    self.stale = (value.lower() != "false")

                else:
                    # Unknown token - ignore
                    pass

                # Punt over space
                hdr = hdr.strip()

            break

    algorithms = {
        'md5': hashlib.md5,
        'md5-sess': hashlib.md5,
        'sha': hashlib.sha1,
    }

    # DigestCalcHA1
    @staticmethod
    def calcHA1(
        pszAlg,
        pszUserName,
        pszRealm,
        pszPassword,
        pszNonce,
        pszCNonce,
        preHA1=None
    ):
        """
        @param pszAlg: The name of the algorithm to use to calculate the Digest.
            Currently supported are md5 md5-sess and sha.

        @param pszUserName: The username
        @param pszRealm: The realm
        @param pszPassword: The password
        @param pszNonce: The nonce
        @param pszCNonce: The cnonce

        @param preHA1: If available this is a str containing a previously
            calculated HA1 as a hex string. If this is given then the values for
            pszUserName, pszRealm, and pszPassword are ignored.
        """

        if (preHA1 and (pszUserName or pszRealm or pszPassword)):
            raise TypeError(("preHA1 is incompatible with the pszUserName, "
                             "pszRealm, and pszPassword arguments"))

        if preHA1 is None:
            # We need to calculate the HA1 from the username:realm:password
            m = Digest.algorithms[pszAlg]()
            m.update(pszUserName)
            m.update(":")
            m.update(pszRealm)
            m.update(":")
            m.update(pszPassword)
            HA1 = m.digest()
        else:
            # We were given a username:realm:password
            HA1 = preHA1.decode('hex')

        if pszAlg == "md5-sess":
            m = Digest.algorithms[pszAlg]()
            m.update(HA1)
            m.update(":")
            m.update(pszNonce)
            m.update(":")
            m.update(pszCNonce)
            HA1 = m.digest()

        return HA1.encode('hex')


    # DigestCalcResponse
    @staticmethod
    def calcResponse(
        HA1,
        algo,
        pszNonce,
        pszNonceCount,
        pszCNonce,
        pszQop,
        pszMethod,
        pszDigestUri,
        pszHEntity,
    ):
        m = Digest.algorithms[algo]()
        m.update(pszMethod)
        m.update(":")
        m.update(pszDigestUri)
        if pszQop == "auth-int":
            m.update(":")
            m.update(pszHEntity)
        HA2 = m.digest().encode('hex')

        m = Digest.algorithms[algo]()
        m.update(HA1)
        m.update(":")
        m.update(pszNonce)
        m.update(":")
        if pszNonceCount and pszCNonce: # pszQop:
            m.update(pszNonceCount)
            m.update(":")
            m.update(pszCNonce)
            m.update(":")
            m.update(pszQop)
            m.update(":")
        m.update(HA2)
        respHash = m.digest().encode('hex')
        return respHash


    def generateResponse(self, request):
        self.response = Digest.calcResponse(
            Digest.calcHA1(
                self.fields.get("algorithm", "md5"),
                self.fields.get("username", ""),
                self.fields.get("realm", ""),
                self.fields.get("password", ""),
                self.fields.get("nonce", ""),
                self.fields.get("cnonce", ""),
            ),
            self.fields.get("algorithm", "md5"),
            self.fields.get("nonce", ""),
            self.fields.get("nc", ""),
            self.fields.get("cnonce", ""),
            self.fields.get("qop", ""),
            request.method,
            request.url,
            None,
        )
