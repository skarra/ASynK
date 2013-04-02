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

DAVNamespace = "DAV:"

propfind = QName(DAVNamespace, "propfind")
propname = QName(DAVNamespace, "propname")
allprop = QName(DAVNamespace, "allprop")
prop = QName(DAVNamespace, "prop")
propstat = QName(DAVNamespace, "propstat")
propertyupdate = QName(DAVNamespace, "propertyupdate")
remove = QName(DAVNamespace, "remove")
set = QName(DAVNamespace, "set")

getetag = QName(DAVNamespace, "getetag")
creationdate = QName(DAVNamespace, "creationdate")
displayname = QName(DAVNamespace, "displayname")
getcontentlanguage = QName(DAVNamespace, "getcontentlanguage")
getcontentlength = QName(DAVNamespace, "getcontentlength")
getcontenttype = QName(DAVNamespace, "getcontenttype")
getlastmodified = QName(DAVNamespace, "getlastmodified")
resourcetype = QName(DAVNamespace, "resourcetype")
collection = QName(DAVNamespace, "collection")
synctoken = QName(DAVNamespace, "sync-token")

lockinfo = QName(DAVNamespace, "lockinfo")
lockscope = QName(DAVNamespace, "lockscope")
locktype = QName(DAVNamespace, "locktype")
owner = QName(DAVNamespace, "owner")
exclusive = QName(DAVNamespace, "exclusive")
shared = QName(DAVNamespace, "shared")
write = QName(DAVNamespace, "write")

acl = QName(DAVNamespace, "acl")
ace = QName(DAVNamespace, "ace")
invert = QName(DAVNamespace, "invert")
principal = QName(DAVNamespace, "principal")
privilege = QName(DAVNamespace, "privilege")
grant = QName(DAVNamespace, "grant")
deny = QName(DAVNamespace, "deny")
protected = QName(DAVNamespace, "protected")
inherited = QName(DAVNamespace, "inherited")

href = QName(DAVNamespace, "href")
all = QName(DAVNamespace, "all")
authenticated = QName(DAVNamespace, "authenticated")
unauthenticated = QName(DAVNamespace, "unauthenticated")
property = QName(DAVNamespace, "property")
self = QName(DAVNamespace, "self")
read = QName(DAVNamespace, "read")
write = QName(DAVNamespace, "write")
write_properties = QName(DAVNamespace, "write-properties")
write_content = QName(DAVNamespace, "write-content")
read_acl = QName(DAVNamespace, "read-acl")
read_current_user_privilege_set = QName(DAVNamespace, "read-current-user-privilege-set")
write_acl = QName(DAVNamespace, "write-acl")
bind = QName(DAVNamespace, "bind")
unbind = QName(DAVNamespace, "unbind")
all = QName(DAVNamespace, "all")

multistatus = QName(DAVNamespace, "multistatus")
response = QName(DAVNamespace, "response")
responsedescription = QName(DAVNamespace, "responsedescription")
status = QName(DAVNamespace, "status")

principal_match = QName(DAVNamespace, "principal-match")

principal_collection_set = QName(DAVNamespace, "principal-collection-set")

alternate_URI_set = QName(DAVNamespace, "alternate-URI-set")
principal_URL = QName(DAVNamespace, "principal-URL")
group_member_set = QName(DAVNamespace, "group-member-set")
group_membership = QName(DAVNamespace, "group-membership")

supported_report_set = QName(DAVNamespace, "supported-report-set")
supported_report = QName(DAVNamespace, "supported-report")
report = QName(DAVNamespace, "report")

quota_available_bytes = QName(DAVNamespace, "quota-available-bytes")
quota_used_bytes = QName(DAVNamespace, "quota-used-bytes")

current_user_principal = QName(DAVNamespace, "current-user-principal")

mkcol = QName(DAVNamespace, "mkcol")
mkcol_response = QName(DAVNamespace, "mkcol-response")

sync_collection = QName(DAVNamespace, "sync-collection")
sync_token = QName(DAVNamespace, "sync-token")
sync_level = QName(DAVNamespace, "sync-level")
sync_level_1 = "1"
sync_level_infinite = "infinite"
