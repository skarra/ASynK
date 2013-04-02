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

from xml.etree.ElementTree import QName
from caldavclientlibrary.protocol.webdav.definitions import davxml
from xml.etree.ElementTree import SubElement

class ACE(object):

    def __init__(self):

        self.principal = None
        self.data = None
        self.invert = False
        self.grant = True
        self.privs = ()
        self.protected = False
        self.inherited = False


    def getPrincipal(self):
        return self.principal


    def setPrincipal(self, principal, data=None):
        self.principal = principal
        self.data = data


    def canChange(self):
        return not self.protected and not self.inherited


    @staticmethod
    def parseFromACL(aclnode):

        aces = []
        acenodes = aclnode.findall(str(davxml.ace))
        for node in acenodes:
            newace = ACE()
            newace.parseACE(node)
            aces.append(newace)
        return aces


    def parseACE(self, acenode):

        assert(acenode and acenode.tag == davxml.ace)

        # Get invert
        self.invert = False
        principal_parent = acenode
        invert = acenode.find(str(davxml.invert))
        if invert:
            self.invert = True
            principal_parent = invert

        # Get the principal
        principal = principal_parent.find(str(davxml.principal))
        if not principal or len(principal.getchildren()) != 1:
            return False

        # Determine principal info
        child = principal.getchildren()[0]
        if child.tag == davxml.href:
            self.setPrincipal(child.tag, child.text)

        elif child.tag in (davxml.all, davxml.authenticated, davxml.unauthenticated, davxml.self,):
            self.setPrincipal(child.tag)

        elif child.tag == davxml.property:
            if len(child.getchildren()) == 1:
                self.setPrincipal(child.tag, QName(child.getchildren()[0].tag))
            else:
                self.setPrincipal(child.tag)

        # Determine rights
        self.grant = True
        child = acenode.find(str(davxml.grant))
        if not child:
            child = acenode.find(str(davxml.deny))
            if child:
                self.grant = False
        if child:
            self.parsePrivileges(child)

        # Determine protected/inherited state
        self.protected = acenode.find(str(davxml.protected)) is not None
        self.inherited = acenode.find(str(davxml.inherited)) is not None

        return True


    def parsePrivileges(self, parent):

        assert(parent.tag in (davxml.grant, davxml.deny,))

        # Parent node contains one of more privilege nodes which we parse
        self.privs = ()
        for privilege in parent.getchildren():
            # Look for privilege
            if privilege.tag != davxml.privilege or len(privilege.getchildren()) != 1:
                continue

            # Now get rights within the privilege
            self.privs += (privilege.getchildren()[0].tag,)


    def generateACE(self, aclnode):
        # Structure of ace is:
        #
        #   <DAV:ace>
        #     <DAV:principal>...</DAV:principal>
        #       <DAV:grant>...</DAV:grant>
        #   </DAV:ace>

        # <DAV:ace> element
        ace = SubElement(aclnode, davxml.ace)

        if self.invert:
            invert = SubElement(ace, davxml.invert)

        # <DAV:principal> element
        principal = SubElement(invert if self.invert else ace, davxml.principal)

        # Principal type
        if self.principal == davxml.href:

            # <DAV:href> element
            href = SubElement(principal, davxml.href)
            href.text = self.data

        elif self.principal in (davxml.all, davxml.authenticated, davxml.unauthenticated, davxml.self,):

            # <DAV:all>/<DAV:authenticated>/<DAV:unauthenticated>/<DAV:self> elements
            SubElement(principal, self.principal)

        elif self.principal == davxml.property:

            # <DAV:property> element - the UID is the property element name
            property = SubElement(principal, davxml.property)
            SubElement(property, self.data)

        # Do grant rights for each one set
        if self.grant:
            # <DAV:grant> element
            privs = SubElement(ace, davxml.grant)

        # Do deny rights for each one set
        else:
            # <DAV:deny> element
            privs = SubElement(ace, davxml.deny)

        for item in self.privs:
            priv = SubElement(privs, davxml.privilege)
            SubElement(priv, item)

        # <DAV:protected> and <DAV:inherited>
        if self.protected:
            SubElement(ace, davxml.protected)
        if self.inherited:
            SubElement(ace, davxml.inherited)
