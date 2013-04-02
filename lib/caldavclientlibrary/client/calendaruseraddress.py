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


class CalendarUserAddress(object):

    def __init__(self, cuaddr=None, name=None, attendee=None):
        self.cuaddr = cuaddr
        self.name = name
        if attendee:
            self.setAttendee(attendee)


    def getCUAddr(self):
        return self.cuaddr


    def setCUAddr(self, value):
        self.cuaddr = value


    def getName(self):
        return self.name


    def setCn(self, value):
        self.name = value


    def getFullText(self):
        return ("%s <%s>" % (self.name, self.cuaddr,)) if self.name else ("<%s>" % (self.cuaddr,))


    def getAttendeeProperty(self):
        pass


    def setAttendee(self, attendee):
        pass
