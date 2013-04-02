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

from caldavclientlibrary.client.account import CalDAVAccount

if __name__ == '__main__':
    account = CalDAVAccount("", ssl=True, user="", pswd="", root="", principal="")

    print account.getPrincipal()

#    memberships = [CalDAVPrincipal(account.session, path) for path in account.getPrincipal().memberships]
#    for member in memberships:
#        member.loadDetails()
#    memberships = [member.displayname for member in memberships]
#    print "Memberships: %s" % (memberships,)

#    calendars = account.getPrincipal().listCalendars()
#    for calendar in calendars:
#        print "%s:" % (calendar,)
#        txt = calendar.getDisplayName()
#        if txt:
#            print "  Display Name: %s" % (txt,)
#        txt = calendar.getDescription()
#        if txt:
#            print "  Description: %s" % (txt,)

#    fbset = account.getPrincipal().listFreeBusySet()
#    print fbset
#    account.getPrincipal().cleanFreeBusySet()

    proxies = account.getPrincipal().getReadProxies()
    for proxy in proxies:
        print proxy
