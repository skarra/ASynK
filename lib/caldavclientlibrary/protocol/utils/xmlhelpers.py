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

from xml.etree.ElementTree import ElementTree, _namespace_map
from xml.etree.ElementTree import Comment
from xml.etree.ElementTree import _escape_cdata
from xml.etree.ElementTree import ProcessingInstruction
from xml.etree.ElementTree import QName
from xml.etree.ElementTree import _raise_serialization_error
from xml.etree.ElementTree import _encode
from xml.etree.ElementTree import _escape_attrib
from StringIO import StringIO
from xml.etree.ElementTree import SubElement
import string

def SubElementWithData(parent, tag, data=None, attrs={}):
    element = SubElement(parent, tag, attrs)
    if data:
        element.text = data
    return element



def myfixtag(tag, namespaces):
    # given a decorated tag (of the form {uri}tag), return prefixed
    # tag and namespace declaration, if any
    if isinstance(tag, QName):
        tag = tag.text
    namespace_uri, tag = string.split(tag[1:], "}", 1)
    prefix = namespaces.get(namespace_uri)
    if prefix is None:
        prefix = _namespace_map.get(namespace_uri)
        if prefix is None:
            prefix = "ns%d" % len(namespaces)
        namespaces[namespace_uri] = prefix
        if prefix == "xml":
            xmlns = None
        else:
            xmlns = ("xmlns:%s" % prefix, namespace_uri)
    else:
        xmlns = None
    return "%s:%s" % (prefix, tag), xmlns



class BetterElementTree(ElementTree):

    def writeUTF8(self, file):
        assert self._root is not None
        if not hasattr(file, "write"):
            file = open(file, "wb")
        encoding = "utf-8"
        file.write("<?xml version='1.0' encoding='%s'?>" % encoding)
        self._prettywrite(file, self._root, encoding, {})
        file.write("\r\n")


    def _prettywrite(self, file, node, encoding, namespaces, depth=0):
        # write XML to file
        tag = node.tag
        if tag is Comment:
            file.write("\r\n" + "  " * depth)
            file.write("<!-- %s -->" % _escape_cdata(node.text, encoding))
        elif tag is ProcessingInstruction:
            file.write("\r\n" + "  " * depth)
            file.write("<?%s?>" % _escape_cdata(node.text, encoding))
        else:
            items = node.items()
            xmlns_items = [] # new namespaces in this scope
            try:
                if isinstance(tag, QName) or tag[:1] == "{":
                    tag, xmlns = myfixtag(tag, namespaces)
                    if xmlns:
                        xmlns_items.append(xmlns)
            except TypeError:
                _raise_serialization_error(tag)
            file.write("\r\n" + "  " * depth)
            file.write("<" + _encode(tag, encoding))
            if items or xmlns_items:
                items.sort() # lexical order
                for k, v in items:
                    try:
                        if isinstance(k, QName) or k[:1] == "{":
                            k, xmlns = myfixtag(k, namespaces)
                            if xmlns:
                                xmlns_items.append(xmlns)
                    except TypeError:
                        _raise_serialization_error(k)
                    try:
                        if isinstance(v, QName):
                            v, xmlns = myfixtag(v, namespaces)
                            if xmlns:
                                xmlns_items.append(xmlns)
                    except TypeError:
                        _raise_serialization_error(v)
                    file.write(" %s=\"%s\"" % (_encode(k, encoding),
                                               _escape_attrib(v, encoding)))
                for k, v in xmlns_items:
                    file.write(" %s=\"%s\"" % (_encode(k, encoding),
                                               _escape_attrib(v, encoding)))
            if node.text or len(node):
                file.write(">")
                if node.text:
                    file.write(_escape_cdata(node.text, encoding))
                for n in node:
                    self._prettywrite(file, n, encoding, namespaces, depth=depth + 1)
                if not node.text or len(node):
                    file.write("\r\n" + "  " * depth)
                file.write("</" + _encode(tag, encoding) + ">")
            else:
                file.write(" />")
            for k, v in xmlns_items:
                del namespaces[v]
        if node.tail:
            file.write(_escape_cdata(node.tail, encoding))



def elementToString(element):
    os = StringIO()
    xmldoc = BetterElementTree(element)
    xmldoc.writeUTF8(os)
    return os.getvalue()
