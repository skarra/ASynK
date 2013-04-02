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

# HTTP protocol headers

# RFC2616 4.5 - General Header fields (only the ones we need)

Connection = "Connection"
ConnectionClose = "close"
Date = "Date"
TransferEncoding = "Transfer-Encoding"
TransferEncodingChunked = "chunked"

# RFC2616 5.3 - Request Header fields (only the ones we need)

Authorization = "Authorization"
Host = "Host"
IfMatch = "If-Match"
IfNoneMatch = "If-None-Match"

# RFC2616 6.2 - Response Header fields (only the ones we need)

ETag = "ETag"
Location = "Location"
Server = "Server"
WWWAuthenticate = "WWW-Authenticate"

# RFC2616 7.1 - Entity Header fields (only the ones we need)

Allow = "Allow"
ContentLength = "Content-Length"
ContentType = "Content-Type"
