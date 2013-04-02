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

CalDAVNamespace = "urn:ietf:params:xml:ns:caldav"

# RFC4791

mkcalendar = QName(CalDAVNamespace, "mkcalendar")
mkcalendar_response = QName(CalDAVNamespace, "mkcalendar-response")

calendar = QName(CalDAVNamespace, "calendar")

calendar_description = QName(CalDAVNamespace, "calendar-description")
calendar_timezone = QName(CalDAVNamespace, "calendar-timezone")
supported_calendar_component_set = QName(CalDAVNamespace, "supported-calendar-component-set")
supported_calendar_data = QName(CalDAVNamespace, "supported-calendar-data")
max_resource_size = QName(CalDAVNamespace, "max-resource-size")
min_date_time = QName(CalDAVNamespace, "min-date-time")
max_date_time = QName(CalDAVNamespace, "max-date-time")
max_instances = QName(CalDAVNamespace, "max-instances")
max_attendees_per_instance = QName(CalDAVNamespace, "max-attendees-per-instance")

read_free_busy = QName(CalDAVNamespace, "read-free-busy")
calendar_home_set = QName(CalDAVNamespace, "calendar-home-set")

supported_collation = QName(CalDAVNamespace, "supported-collation")

calendar_query = QName(CalDAVNamespace, "calendar-query")
calendar_data = QName(CalDAVNamespace, "calendar-data")
comp = QName(CalDAVNamespace, "comp")
allcomp = QName(CalDAVNamespace, "allcomp")
prop = QName(CalDAVNamespace, "prop")
expand = QName(CalDAVNamespace, "expand")
limit_recurrence_set = QName(CalDAVNamespace, "limit-recurrence-set")
limit_freebusy_set = QName(CalDAVNamespace, "limit-freebusy-set")
filter = QName(CalDAVNamespace, "filter")
comp_filter = QName(CalDAVNamespace, "comp-filter")
prop_filter = QName(CalDAVNamespace, "prop-filter")
param_filter = QName(CalDAVNamespace, "param-filter")
is_not_defined = QName(CalDAVNamespace, "is-not-defined")
text_match = QName(CalDAVNamespace, "text-match")
timezone = QName(CalDAVNamespace, "timezone")
time_range = QName(CalDAVNamespace, "time-range")

calendar_multiget = QName(CalDAVNamespace, "calendar-multiget")

free_busy_query = QName(CalDAVNamespace, "free-busy-query")

# draft caldav-schedule
calendar_free_busy_set = QName(CalDAVNamespace, "calendar-free-busy-set")
originator = QName(CalDAVNamespace, "originator")
recipient = QName(CalDAVNamespace, "recipient")
schedule = QName(CalDAVNamespace, "schedule")

schedule_tag = QName(CalDAVNamespace, "schedule-tag")
schedule_inbox = QName(CalDAVNamespace, "schedule-inbox")
schedule_inbox_URL = QName(CalDAVNamespace, "schedule-inbox-URL")
schedule_outbox = QName(CalDAVNamespace, "schedule-outbox")
schedule_outbox_URL = QName(CalDAVNamespace, "schedule-outbox-URL")
calendar_user_address_set = QName(CalDAVNamespace, "calendar-user-address-set")

schedule_response = QName(CalDAVNamespace, "schedule-response")
response = QName(CalDAVNamespace, "timezone")
request_status = QName(CalDAVNamespace, "request-status")

# Extensions

CalendarServerNamespace = "http://calendarserver.org/ns/"

calendar_proxy_read = QName(CalendarServerNamespace, "calendar-proxy-read")
calendar_proxy_write = QName(CalendarServerNamespace, "calendar-proxy-write")
