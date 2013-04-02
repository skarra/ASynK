# #
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
# #

from caldavclientlibrary.client.httpshandler import SmartHTTPConnection
from caldavclientlibrary.protocol.caldav.definitions import headers
from caldavclientlibrary.protocol.caldav.makecalendar import MakeCalendar
from caldavclientlibrary.protocol.carddav.makeaddressbook import MakeAddressBook
from caldavclientlibrary.protocol.http.authentication.basic import Basic
from caldavclientlibrary.protocol.http.authentication.digest import Digest
from caldavclientlibrary.protocol.webdav.synccollection import SyncCollection
from caldavclientlibrary.protocol.caldav.query import QueryVEVENTTimeRange
try:
    from caldavclientlibrary.protocol.http.authentication.gssapi import Kerberos
except ImportError:
    Kerberos = None
from caldavclientlibrary.protocol.http.data.string import ResponseDataString, RequestDataString
from caldavclientlibrary.protocol.url import URL
from caldavclientlibrary.protocol.webdav.acl import ACL
from caldavclientlibrary.protocol.webdav.definitions import davxml
from caldavclientlibrary.protocol.webdav.definitions import statuscodes
from caldavclientlibrary.protocol.webdav.delete import Delete
from caldavclientlibrary.protocol.webdav.get import Get
from caldavclientlibrary.protocol.webdav.makecollection import MakeCollection
from caldavclientlibrary.protocol.webdav.move import Move
from caldavclientlibrary.protocol.webdav.post import Post
from caldavclientlibrary.protocol.webdav.principalmatch import PrincipalMatch
from caldavclientlibrary.protocol.webdav.propall import PropAll
from caldavclientlibrary.protocol.webdav.propfind import PropFind
from caldavclientlibrary.protocol.webdav.propfindparser import PropFindParser
from caldavclientlibrary.protocol.webdav.propnames import PropNames
from caldavclientlibrary.protocol.webdav.proppatch import PropPatch
from caldavclientlibrary.protocol.webdav.put import Put
from caldavclientlibrary.protocol.webdav.session import Session
from xml.etree.ElementTree import Element, tostring
import types

class CalDAVSession(Session):

    class logger(object):

        def write(self, data):
            print data.replace("\r\n", "\n"),


    def __init__(self, server, port=None, ssl=False, user="", pswd="", principal=None, root=None, logging=False):
        super(CalDAVSession, self).__init__(server, port, ssl, log=CalDAVSession.logger())

        self.loghttp = logging

        self.user = user
        self.pswd = pswd

        # Initialize state
        self.connect = None

        # Paths
        self.rootPath = URL(url=root)
        self.principalPath = URL(url=principal) if principal else None

        self._initCalDAVState()


    def _initCalDAVState(self):

        # We need to cache the server capabilities and properties
        if not self.principalPath:
            self._discoverPrincipal()


    def _discoverPrincipal(self):

        current = self.getCurrentPrincipalResource(self.rootPath)
        if current:
            self.principalPath = current
            if self.log:
                self.log.write("Found current principal path: %s\n" % (self.principalPath.absoluteURL(),))
            return

        hrefs = self.getHrefListProperty(self.rootPath, davxml.principal_collection_set)
        if not hrefs:
            return

        # For each principal collection find current principal
        for href in hrefs:
            current = self.getCurrentPrincipalResource(href)
            if current:
                self.principalPath = current
                if self.log:
                    self.log.write("Found current principal path: %s\n" % (self.principalPath.absoluteURL(),))
                return


    def setUserPswd(self, user, pswd):

        self.user = user
        self.pswd = pswd
        self.authorization = None
        self._discoverPrincipal()


    def testResource(self, rurl):

        assert(isinstance(rurl, URL))

        request = PropFind(self, rurl.relativeURL(), headers.Depth0, (davxml.resourcetype,))

        # Process it
        self.runSession(request)

        return request.getStatusCode() == statuscodes.MultiStatus


    def getPropertyNames(self, rurl):

        assert(isinstance(rurl, URL))

        results = ()

        # Create WebDAV propfind
        request = PropNames(self, rurl.relativeURL(), headers.Depth0)
        result = ResponseDataString()
        request.setOutput(result)

        # Process it
        self.runSession(request)

        # If its a 207 we want to parse the XML
        if request.getStatusCode() == statuscodes.MultiStatus:

            parser = PropFindParser()
            parser.parseData(result.getData())

            # Look at each propfind result
            for item in parser.getResults().itervalues():

                # Get child element name (decode URL)
                name = URL(url=item.getResource(), decode=True)

                # Must match rurl
                if name.equalRelative(rurl):

                    results = tuple([name for name in item.getNodeProperties().iterkeys()])

        else:
            self.handleHTTPError(request)

        return results


    def getProperties(self, rurl, props, xmldata=False):

        assert(isinstance(rurl, URL))

        results = {}
        bad = None

        # Create WebDAV propfind
        if props:
            request = PropFind(self, rurl.relativeURL(), headers.Depth0, props)
        else:
            request = PropAll(self, rurl.relativeURL(), headers.Depth0)
        result = ResponseDataString()
        request.setOutput(result)

        # Process it
        self.runSession(request)

        # If its a 207 we want to parse the XML
        if request.getStatusCode() == statuscodes.MultiStatus:

            parser = PropFindParser()
            parser.parseData(result.getData())

            # Look at each propfind result
            for item in parser.getResults().itervalues():

                # Get child element name (decode URL)
                name = URL(url=item.getResource(), decode=True)

                # Must match rurl
                if name.equalRelative(rurl):
                    for name, value in item.getTextProperties().iteritems():
                        results[name] = value
                    for name, value in item.getHrefProperties().iteritems():
                        if name not in results:
                            results[name] = value
                    for name, value in item.getNodeProperties().iteritems():
                        if name not in results:
                            results[name] = tostring(value) if xmldata else value
                    bad = item.getBadProperties()
        else:
            self.handleHTTPError(request)

        return results, bad


    def getPropertiesOnHierarchy(self, rurl, props):

        assert(isinstance(rurl, URL))

        results = {}

        # Create WebDAV propfind
        request = PropFind(self, rurl.relativeURL(), headers.Depth1, props)
        result = ResponseDataString()
        request.setOutput(result)

        # Process it
        self.runSession(request)

        # If its a 207 we want to parse the XML
        if request.getStatusCode() == statuscodes.MultiStatus:

            parser = PropFindParser()
            parser.parseData(result.getData())

            # Look at each propfind result
            for item in parser.getResults().itervalues():

                # Get child element name (decode URL)
                name = URL(url=item.getResource(), decode=True)
                propresults = {}
                results[name.relativeURL()] = propresults

                for prop in props:

                    if str(prop) in item.getTextProperties():
                        propresults[prop] = item.getTextProperties().get(str(prop))

                    elif str(prop) in item.getNodeProperties():
                        propresults[prop] = item.getNodeProperties()[str(prop)]
        else:
            self.handleHTTPError(request)

        return results


    def getHrefListProperty(self, rurl, propname):

        assert(isinstance(rurl, URL))

        results = ()

        # Create WebDAV propfind
        request = PropFind(self, rurl.relativeURL(), headers.Depth0, (propname,))
        result = ResponseDataString()
        request.setOutput(result)

        # Process it
        self.runSession(request)

        # If its a 207 we want to parse the XML
        if request.getStatusCode() == statuscodes.MultiStatus:

            parser = PropFindParser()
            parser.parseData(result.getData())

            # Look at each propfind result and extract any Hrefs
            for item in parser.getResults().itervalues():

                # Get child element name (decode URL)
                name = URL(url=item.getResource(), decode=True)

                # Must match rurl
                if name.equalRelative(rurl):

                    if str(propname) in item.getNodeProperties():

                        propnode = item.getNodeProperties()[str(propname)]
                        results += tuple([URL(url=href.text, decode=True) for href in propnode.findall(str(davxml.href)) if href.text])
        else:
            self.handleHTTPError(request)

        return results


    # Do principal-match report with self on the passed in url
    def getSelfProperties(self, rurl, props):

        assert(isinstance(rurl, URL))

        results = {}

        # Create WebDAV principal-match
        request = PrincipalMatch(self, rurl.relativeURL(), props)
        result = ResponseDataString()
        request.setOutput(result)

        # Process it
        self.runSession(request)

        # If its a 207 we want to parse the XML
        if request.getStatusCode() == statuscodes.MultiStatus:

            parser = PropFindParser()
            parser.parseData(result.getData())

            # Look at each principal-match result and return first one that is appropriate
            for item in parser.getResults().itervalues():

                for prop in props:

                    if str(prop) in item.getNodeProperties():

                        href = item.getNodeProperties()[str(prop)].find(str(davxml.href))

                        if href is not None:
                            results[prop] = URL(url=href.text, decode=True)

                # We'll take the first one, whatever that is
                break

        else:
            self.handleHTTPError(request)
            return None

        return results


    # Do principal-match report with self on the passed in url
    def getSelfHrefs(self, rurl):

        assert(isinstance(rurl, URL))

        results = ()

        # Create WebDAV principal-match
        request = PrincipalMatch(self, rurl.relativeURL(), (davxml.principal_URL,))
        result = ResponseDataString()
        request.setOutput(result)

        # Process it
        self.runSession(request)

        # If its a 207 we want to parse the XML
        if request.getStatusCode() == statuscodes.MultiStatus:

            parser = PropFindParser()
            parser.parseData(result.getData())

            # Look at each propfind result and extract any Hrefs
            for item in parser.getResults().itervalues():

                # Get child element name (decode URL)
                name = URL(url=item.getResource(), decode=True)
                results += (name,)

        else:
            self.handleHTTPError(request)
            return None

        return results


    # Do principal-match report with self on the passed in url
    def getSelfPrincipalResource(self, rurl):

        assert(isinstance(rurl, URL))

        hrefs = self.getHrefListProperty(rurl, davxml.principal_collection_set)
        if not hrefs:
            return None

        # For each principal collection find one that matches self
        for href in hrefs:

            results = self.getSelfHrefs(href)
            if results:
                return results[0]

        return None


    # Do current-user-principal property on the passed in url
    def getCurrentPrincipalResource(self, rurl):

        assert(isinstance(rurl, URL))

        hrefs = self.getHrefListProperty(rurl, davxml.current_user_principal)
        return hrefs[0] if hrefs else None


    def setProperties(self, rurl, props):

        assert(isinstance(rurl, URL))

        results = ()

        # Convert property data into something sensible
        converted = []
        for name, value in props:
            node = None
            if isinstance(value, types.StringType):
                node = Element(name)
                node.text = value
            elif isinstance(value, URL):
                node = Element(davxml.href)
                node.text = value.absoluteURL()
            elif isinstance(value, types.ListType) or isinstance(value, types.TupleType):
                hrefs = []
                for item in value:
                    if isinstance(item, URL):
                        href = Element(davxml.href)
                        href.text = item.relativeURL()
                        hrefs.append(href)
                    else:
                        break
                else:
                    node = Element(name)
                    map(node.append, hrefs)

            if node is not None:
                converted.append(node)

        # Create WebDAV propfind
        request = PropPatch(self, rurl.relativeURL(), converted)
        result = ResponseDataString()
        request.setOutput(result)

        # Process it
        self.runSession(request)

        # If its a 207 we want to parse the XML
        if request.getStatusCode() == statuscodes.MultiStatus:

            parser = PropFindParser()
            parser.parseData(result.getData())

            # Look at each propfind result
            for item in parser.getResults().itervalues():

                # Get child element name (decode URL)
                name = URL(url=item.getResource(), decode=True)

                # Must match rurl
                if name.equalRelative(rurl):

                    for prop in item.getNodeProperties():
                        results += (prop,)

        else:
            self.handleHTTPError(request)

        return results


    def setACL(self, rurl, aces):

        assert(isinstance(rurl, URL))

        # Create WebDAV ACL
        request = ACL(self, rurl.relativeURL(), aces)

        # Process it
        self.runSession(request)

        if request.getStatusCode() not in (statuscodes.OK, statuscodes.Created, statuscodes.NoContent):
            self.handleHTTPError(request)


    def makeCollection(self, rurl):

        assert(isinstance(rurl, URL))

        # Create WebDAV MKCOL
        request = MakeCollection(self, rurl.relativeURL())

        # Process it
        self.runSession(request)

        if request.getStatusCode() not in (statuscodes.OK, statuscodes.Created, statuscodes.NoContent):
            self.handleHTTPError(request)


    def makeCalendar(self, rurl, displayname=None, description=None):

        assert(isinstance(rurl, URL))

        # Create WebDAV MKCALENDAR
        request = MakeCalendar(self, rurl.relativeURL(), displayname, description)

        # Process it
        self.runSession(request)

        if request.getStatusCode() not in (statuscodes.OK, statuscodes.Created, statuscodes.NoContent):
            self.handleHTTPError(request)


    def makeAddressBook(self, rurl, displayname=None, description=None):

        assert(isinstance(rurl, URL))

        # Create WebDAV extended MKCOL
        request = MakeAddressBook(self, rurl.relativeURL(), displayname, description)

        # Process it
        self.runSession(request)

        if request.getStatusCode() not in (statuscodes.OK, statuscodes.Created, statuscodes.NoContent):
            self.handleHTTPError(request)


    def syncCollection(self, rurl, synctoken, props=()):

        assert(isinstance(rurl, URL))

        newsynctoken = ""
        changed = set()
        removed = set()
        other = set()

        # Create WebDAV sync REPORT
        request = SyncCollection(self, rurl.relativeURL(), davxml.sync_level_1, synctoken, props)
        result = ResponseDataString()
        request.setOutput(result)

        # Process it
        self.runSession(request)

        # If its a 207 we want to parse the XML
        if request.getStatusCode() == statuscodes.MultiStatus:

            parser = PropFindParser()
            parser.parseData(result.getData())

            # Look at each propfind result
            for item in parser.getResults().itervalues():

                # Get child element name (decode URL)
                name = URL(url=item.getResource(), decode=True)
                if item.status == 404:
                    removed.add(name)
                elif item.status / 100 != 2:
                    other.add(name)
                else:
                    changed.add(name)

            # Get the new token
            for node in parser.getOthers():
                if node.tag == davxml.sync_token:
                    newsynctoken = node.text
                    break

        else:
            self.handleHTTPError(request)

        return (newsynctoken, changed, removed, other,)


    def queryCollection(self, rurl, timerange, start, end, expand, props=()):

        assert(isinstance(rurl, URL))

        hrefs = set()

        # Create CalDAV query REPORT
        if timerange:
            request = QueryVEVENTTimeRange(self, rurl.relativeURL(), start, end, expand, props=props)
        else:
            raise NotImplementedError
        result = ResponseDataString()
        request.setOutput(result)

        # Process it
        self.runSession(request)

        # If its a 207 we want to parse the XML
        if request.getStatusCode() == statuscodes.MultiStatus:

            parser = PropFindParser()
            parser.parseData(result.getData())

            # Look at each propfind result
            for item in parser.getResults().itervalues():

                # Get child element name (decode URL)
                name = URL(url=item.getResource(), decode=True)
                hrefs.add(name)

        else:
            self.handleHTTPError(request)

        return hrefs


    def deleteResource(self, rurl):

        assert(isinstance(rurl, URL))

        # Create WebDAV DELETE
        request = Delete(self, rurl.relativeURL())

        # Process it
        self.runSession(request)

        if request.getStatusCode() not in (statuscodes.OK, statuscodes.NoContent):
            self.handleHTTPError(request)


    def moveResource(self, rurlFrom, rurlTo):

        assert(isinstance(rurlFrom, URL))
        assert(isinstance(rurlTo, URL))

        # Create WebDAV MOVE
        request = Move(self, rurlFrom.relativeURL(), rurlTo.absoluteURL())

        # Process it
        self.runSession(request)

        if request.getStatusCode() not in (statuscodes.OK, statuscodes.Created, statuscodes.NoContent):
            self.handleHTTPError(request)


    def readData(self, rurl):

        assert(isinstance(rurl, URL))

        # Create WebDAV GET
        request = Get(self, rurl.relativeURL())
        dout = ResponseDataString()
        request.setData(dout)

        # Process it
        self.runSession(request)

        # Check response status
        if request.getStatusCode() != statuscodes.OK:
            self.handleHTTPError(request)
            return None

        # Look for ETag
        if request.getNewETag() is not None:

            etag = request.getNewETag()

            # Handle server bug: ETag value MUST be quoted per HTTP/1.1 S3.11
            if not etag.startswith('"'):
                etag = "\"%s\"" % (etag,)
        else:
            etag = None

        # Return data as a string and etag
        return dout.getData(), etag


    def writeData(self, rurl, data, contentType):

        assert(isinstance(rurl, URL))

        # Create WebDAV PUT
        request = Put(self, rurl.relativeURL())
        dout = RequestDataString(data, contentType)
        request.setData(dout, None)

        # Process it
        self.runSession(request)

        # Check response status
        if request.getStatusCode() not in (statuscodes.OK, statuscodes.Created, statuscodes.NoContent,):
            self.handleHTTPError(request)


    def importData(self, rurl, data, contentType):

        assert(isinstance(rurl, URL))

        # Create WebDAV POST
        request = Post(self, rurl.relativeURL())
        dout = RequestDataString(data, contentType)
        request.setData(dout, None)

        # Process it
        self.runSession(request)

        # Check response status
        if request.getStatusCode() not in (statuscodes.OK, statuscodes.MultiStatus, statuscodes.NoContent,):
            self.handleHTTPError(request)


    def addAttachment(self, rurl, filename, data, contentType, return_representation):

        assert(isinstance(rurl, URL))

        # Create WebDAV POST
        rurl.extended = "?action=attachment-add"
        request = Post(self, rurl.relativeURL())
        dout = RequestDataString(data, contentType)
        request.setRequestHeader("Content-Disposition", "attachment;filename=%s" % (filename,))
        if return_representation:
            request.setRequestHeader("Prefer", "return-representation")
        request.setData(dout, None)

        # Process it
        self.runSession(request)

        # Check response status
        if request.getStatusCode() not in (statuscodes.OK, statuscodes.Created, statuscodes.NoContent,):
            self.handleHTTPError(request)


    def updateAttachment(self, rurl, managed_id, filename, data, contentType, return_representation):

        assert(isinstance(rurl, URL))

        # Create WebDAV POST
        rurl.extended = "?action=attachment-update&managed-id=%s" % (managed_id,)
        request = Post(self, rurl.relativeURL())
        request.setRequestHeader("Content-Disposition", "attachment;filename=%s" % (filename,))
        if return_representation:
            request.setRequestHeader("Prefer", "return-representation")
        dout = RequestDataString(data, contentType)
        request.setData(dout, None)

        # Process it
        self.runSession(request)

        # Check response status
        if request.getStatusCode() not in (statuscodes.OK, statuscodes.Created, statuscodes.NoContent,):
            self.handleHTTPError(request)


    def removeAttachment(self, rurl, managed_id):

        assert(isinstance(rurl, URL))

        # Create WebDAV POST
        rurl.extended = "?action=attachment-remove&managed-id=%s" % (managed_id,)
        request = Post(self, rurl.relativeURL())

        # Process it
        self.runSession(request)

        # Check response status
        if request.getStatusCode() not in (statuscodes.OK, statuscodes.NoContent,):
            self.handleHTTPError(request)


    def displayHTTPError(self, request):
        print request.status_code


    def openSession(self):
        # Create connection
        self.connect = SmartHTTPConnection(self.server, self.port, self.ssl)

        # Write to log file
        if self.loghttp and self.log:
            self.log.write("\n        <-------- BEGIN HTTP CONNECTION -------->\n")
            self.log.write("Server: %s\n" % (self.server,))


    def closeSession(self):
        if self.connect:
            self.connect.close()
            self.connect = None

            # Write to log file
            if self.loghttp and self.log:
                self.log.write("\n        <-------- END HTTP CONNECTION -------->\n")


    def runSession(self, request):

        ctr = 5
        while ctr:
            ctr -= 1

            self.doSession(request)

            if request and request.isRedirect():
                location = request.getResponseHeader(headers.Location)
                if location:
                    u = URL(location)
                    if not u.scheme or u.scheme in ("http", "https",):
                        # Get new server and base RURL
                        different_server = (self.server != u.server) if u.server else False

                        # Use new host in this session
                        if different_server:
                            self.setServer(u.server)

                        # Reset the request with new info
                        request.setURL(u.relativeURL())
                        request.clearResponse()

                        # Write to log file
                        if self.loghttp and self.log:
                            self.log.write("\n        <-------- HTTP REDIRECT -------->\n")
                            self.log.write("Location: %s\n" % (location,))

                        # Recyle through loop
                        continue

            # Exit when redirect does not occur
            break


    def doSession(self, request):
        # Do initialisation if not already done
        if not self.initialised:

            if not self.initialise(self.server, self.rootPath.relativeURL()):

                # Break connection with server
                self.closeConnection()
                return

        # Do the request if present
        if request:

            # Handle delayed authorization
            first_time = True
            while True:

                # Run the request actions - this will make any connection that is needed
                self.sendRequest(request)

                # Check for auth failure if none before
                if request.getStatusCode() == statuscodes.Unauthorized:

                    # If we had authorization before, then chances are auth details are wrong - so delete and try again with new auth
                    if self.hasAuthorization():

                        self.authorization = None

                        # Display error so user knows why the prompt occurs again - but not the first time
                        # as we might have a digest re-auth.
                        if not first_time:
                            self.displayHTTPError(request)

                    # Get authorization object (prompt the user) and redo the request
                    self.authorization, cancelled = self.getAuthorizor(first_time, request.getResponseHeaders(headers.WWWAuthenticate))

                    # Check for auth cancellation
                    if cancelled:
                        self.authorization = None

                    else:
                        first_time = False

                        request.clearResponse()

                        # Repeat the request loop with new authorization
                        continue

                # If we get here we are complete with auth loop
                break

        # Now close it - eventually we will do keep-alive support

        # Break connection with server
        self.closeConnection()


    def doRequest(self, request):

        # Write request headers
        self.connect.putrequest(request.method, request.url, skip_host=True, skip_accept_encoding=True)
        hdrs = request.getRequestHeaders()
        for header, value in hdrs:
            self.connect.putheader(header, value)
        self.connect.endheaders()

        # Write to log file
        if self.loghttp and self.log:
            self.log.write("\n        <-------- BEGIN HTTP REQUEST -------->\n")
            self.log.write("%s\n" % (request.getRequestStartLine(),))
            for header, value in hdrs:
                self.log.write("%s: %s\n" % (header, value))
            self.log.write("\n")

        # Write the data
        self.writeRequestData(request)

        # Blank line in log between
        if self.loghttp and self.log:
            self.log.write("\n        <-------- BEGIN HTTP RESPONSE -------->\n")

        # Get response
        response = self.connect.getresponse()

        # Get response headers
        request.setResponseStatus(response.version, response.status, response.reason)
        request.setResponseHeaders(response.msg.headers)
        if self.loghttp and self.log:
            self.log.write("HTTP/%s %s %s\r\n" % (
                {11: "1.1", 10: "1.0", 9: "0.9"}.get(response.version, "?"),
                response.status,
                response.reason
            ))
            for hdr in response.msg.headers:
                self.log.write(hdr)
            self.log.write("\n")

        # Now get the data
        self.readResponseData(request, response)

        # Trailer in log
        if self.loghttp and self.log:
            self.log.write("\n        <-------- END HTTP RESPONSE -------->\n")


    def handleHTTPError(self, request):
        print "Ignoring error: %d" % (request.getStatusCode(),)


    def getAuthorizor(self, first_time, wwwhdrs):

        for witem in wwwhdrs:
            for item in witem.split(","):
                item = item.strip()
                if item.lower().startswith("basic"):
                    return Basic(self.user, self.pswd), False
                elif item.lower().startswith("digest"):
                    return Digest(self.user, self.pswd, wwwhdrs), False
                elif item.lower().startswith("negotiate") and Kerberos is not None:
                    return Kerberos(self.user), False
        else:
            return None, True


    def writeRequestData(self, request):

        # Write the data if any present
        if request.hasRequestData():

            stream = request.getRequestData()
            if stream:
                # Tell data we are using it
                stream.start()

                # Buffered write from stream
                more = True
                while more:
                    data, more = stream.read()
                    if data:
                        self.connect.send(data)

                        if self.loghttp and self.log:
                            self.log.write(data)

                # Tell data we are done using it
                stream.stop()


    def readResponseData(self, request, response):

        # Check for data and write it
        data = response.read()

        if request.hasResponseData():
            stream = request.getResponseData()
            stream.start()
            stream.write(data)
            stream.stop()
        else:
            response.read()

        if self.loghttp and self.log:
            self.log.write(data)


    def setServerType(self, type):
        self.type = type


    def setServerDescriptor(self, txt):
        self.descriptor = txt


    def setServerCapability(self, txt):
        self.capability = txt
