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
from caldavclientlibrary.protocol.http.definitions import headers

class Basic(Authenticator):

    def __init__(self, user, pswd):
        self.user = user
        self.pswd = pswd


    def setDetails(self, user, pswd):
        self.user = user
        self.pswd = pswd


    def addHeaders(self, hdrs, request):
        # Generate the base64 encoded string
        encode = self.user + ":" + self.pswd
        base64 = encode.encode("base64").strip()

        # Generate header
        hdrs.append((headers.Authorization, "Basic %s" % (base64,)))
