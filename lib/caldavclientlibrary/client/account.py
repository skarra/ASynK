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

from caldavclientlibrary.client.clientsession import CalDAVSession
from caldavclientlibrary.client.principal import principalCache

class CalDAVAccount(object):

    def __init__(self, server, port=None, ssl=False, user="", pswd="", principal=None, root=None, logging=False):
        self.session = CalDAVSession(server, port, ssl, user, pswd, principal, root, logging)
        self.principal = principalCache.getPrincipal(self.session, self.session.principalPath)


    def setUserPswd(self, user, pswd):

        self.session.setUserPswd(user, pswd)
        self.principal = principalCache.getPrincipal(self.session, self.session.principalPath)


    def getPrincipal(self, path=None, refresh=False):
        if path:
            return principalCache.getPrincipal(self.session, path, refresh=refresh)
        elif refresh:
            self.principal = principalCache.getPrincipal(self.session, self.session.principalPath, refresh=refresh)

        return self.principal
