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

from caldavclientlibrary.protocol.webdav.ace import ACE
from xml.etree.ElementTree import XML
from caldavclientlibrary.protocol.webdav.definitions import davxml
from xml.etree.ElementTree import Element
from caldavclientlibrary.protocol.utils.xmlhelpers import BetterElementTree
from StringIO import StringIO

import unittest

class TestRequest(unittest.TestCase):

    def verifyXML(self, x, y=None):

        x = x.replace("\n", "\r\n")
        if y:
            y = y.replace("\n", "\r\n")

        # Parse the XML data
        a = ACE()
        a.parseACE(XML(x))

        # Generate the XML data
        aclnode = Element(davxml.acl)
        a.generateACE(aclnode)
        os = StringIO()
        xmldoc = BetterElementTree(aclnode.getchildren()[0])
        xmldoc.writeUTF8(os)

        # Verify data
        self.assertEqual(os.getvalue(), y if y else x)


    def test_XML1(self):

        self.verifyXML("""<?xml version='1.0' encoding='utf-8'?>
<ns0:ace xmlns:ns0="DAV:">
  <ns0:principal>
    <ns0:href>/principals/users/a</ns0:href>
  </ns0:principal>
  <ns0:grant>
    <ns0:privilege>
      <ns0:read />
    </ns0:privilege>
  </ns0:grant>
</ns0:ace>
""")


    def test_XML2(self):

        self.verifyXML("""<?xml version='1.0' encoding='utf-8'?>
<ns0:ace xmlns:ns0="DAV:">
  <ns0:principal>
    <ns0:unauthenticated />
  </ns0:principal>
  <ns0:deny>
    <ns0:privilege>
      <ns0:read />
    </ns0:privilege>
    <ns0:privilege>
      <ns0:write />
    </ns0:privilege>
  </ns0:deny>
</ns0:ace>
""")


    def test_XML3(self):

        self.verifyXML("""<?xml version='1.0' encoding='utf-8'?>
<ns0:ace xmlns:ns0="DAV:">
  <ns0:principal>
    <ns0:href>/principals/users/a</ns0:href>
  </ns0:principal>
  <ns0:grant>
    <ns0:privilege>
      <ns0:read />
    </ns0:privilege>
  </ns0:grant>
  <ns0:protected />
  <ns0:inherited />
</ns0:ace>
""")


    def test_XML4(self):

        self.verifyXML("""<?xml version='1.0' encoding='utf-8'?>
<ns0:ace xmlns:ns0="DAV:">
  <ns0:invert>
    <ns0:principal>
      <ns0:self />
    </ns0:principal>
  </ns0:invert>
  <ns0:grant>
    <ns0:privilege>
      <ns0:read />
    </ns0:privilege>
  </ns0:grant>
  <ns0:protected />
  <ns0:inherited />
</ns0:ace>
""")


    def test_XML5(self):

        self.verifyXML("""<?xml version='1.0' encoding='utf-8'?>
<ns0:ace xmlns:ns0="DAV:">
  <ns0:principal>
    <ns0:property>
      <ns0:owner />
    </ns0:property>
  </ns0:principal>
  <ns0:grant>
    <ns0:privilege>
      <ns0:read />
    </ns0:privilege>
  </ns0:grant>
</ns0:ace>
""")
