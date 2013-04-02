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

# RFC2518 9 - Request Header fields (only the ones we need)

from caldavclientlibrary.protocol.http.definitions.headers import * #@UnusedWildImport

DAV = "DAV"
DAV1 = "1"
DAV2 = "2"
DAVbis = "bis"
DAVACL = "access-control"        # ACL extension RFC3744
Depth = "Depth"
Depth0 = "0"
Depth1 = "1"
DepthInfinity = "infinity"
Destination = "Destination"
If = "If"
ForceAuthentication = "Force-Authentication"
LockToken = "Lock-Token"
Overwrite = "Overwrite"
OverwriteTrue = "T"
OverwriteFalse = "F"
Timeout = "Timeout"
TimeoutSeconds = "Second-"
TimeoutInfinite = "Infinite"
Brief = "Brief"                 # MS extension
