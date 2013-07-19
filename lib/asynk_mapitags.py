## Created : Fri Jul 19 20:00:06 IST 2013
##
## Copyright (C) 2013 Sriram Karra <karra.etc@gmail.com>
##
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero General Public License as published by the
## Free Software Foundation, version 3 of the License
##
## ASynK is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
## FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
## License for more details.
##
## You should have a copy of the license in the doc/ directory of ASynK.  If
## not, see <http://www.gnu.org/licenses/>.

## This file contains some definitions for Outlook Named Properties. ASynK
## currently does not use all of these constants.

dispidMeetingType               = 0x0026
dispidFileUnder                 = 0x8005
dispidYomiFirstName             = 0x802C
dispidYomiLastName              = 0x802D
dispidYomiCompanyName           = 0x802E
dispidWorkAddressStreet         = 0x8045
dispidWorkAddressCity           = 0x8046
dispidWorkAddressState          = 0x8047
dispidWorkAddressPostalCode     = 0x8048
dispidWorkAddressCountry        = 0x8049
dispidWorkAddressPostOfficeBox  = 0x804A
dispidInstMsg                   = 0x8062
dispidEmailDisplayName          = 0x8080
dispidEmailAddrType             = 0x8082
dispidEmailEmailAddress         = 0x8083
dispidEmailOriginalDisplayName  = 0x8084
dispidEmail1OriginalEntryID     = 0x8085
dispidEmail2DisplayName         = 0x8090
dispidEmail2AddrType            = 0x8092
dispidEmail2EmailAddress        = 0x8093
dispidEmail2OriginalDisplayName = 0x8094
dispidEmail2OriginalEntryID     = 0x8095
dispidEmail3DisplayName         = 0x80A0
dispidEmail3AddrType            = 0x80A2
dispidEmail3EmailAddress        = 0x80A3
dispidEmail3OriginalDisplayName = 0x80A4
dispidEmail3OriginalEntryID     = 0x80A5
dispidTaskStatus                = 0x8101
dispidTaskStartDate             = 0x8104
dispidTaskDueDate               = 0x8105
dispidTaskActualEffort          = 0x8110
dispidTaskEstimatedEffort       = 0x8111
dispidTaskFRecur                = 0x8126
dispidBusyStatus                = 0x8205
dispidLocation                  = 0x8208
dispidApptStartWhole            = 0x820D
dispidApptEndWhole              = 0x820E
dispidApptDuration              = 0x8213
dispidRecurring                 = 0x8223
dispidTimeZoneStruct            = 0x8233
dispidAllAttendeesString        = 0x8238
dispidToAttendeesString         = 0x823B
dispidCCAttendeesString         = 0x823C
dispidConfCheck                 = 0x8240
dispidApptCounterProposal       = 0x8257
dispidApptTZDefStartDisplay     = 0x825E
dispidApptTZDefEndDisplay       = 0x825F
dispidApptTZDefRecur            = 0x8260
dispidReminderTime              = 0x8502
dispidReminderSet               = 0x8503
dispidFormStorage               = 0x850F
dispidPageDirStream             = 0x8513
dispidSmartNoAttach             = 0x8514
dispidCommonStart               = 0x8516
dispidCommonEnd                 = 0x8517
dispidFormPropStream            = 0x851B
dispidRequest                   = 0x8530
dispidCompanies                 = 0x8539
dispidContacts                  = 0x853A
dispidPropDefStream             = 0x8540
dispidScriptStream              = 0x8541
dispidCustomFlag                = 0x8542
dispidReminderNextTime          = 0x8560
dispidHeaderItem                = 0x8578
dispidUseTNEF                   = 0x8582
dispidToDoTitle                 = 0x85A4
dispidLogType                   = 0x8700
dispidLogStart                  = 0x8706
dispidLogDuration               = 0x8707
dispidLogEnd                    = 0x8708

## FIXME: Fri Jul 19 17:27:43 IST 2013 - Some more GUIDs below. We have alrady
## defined a few in class PropTags. If we need any more of the following we
## will bring them to life and refactor the stuff out of class PropTags.

# const GUID PS_INTERNET_HEADERS  = {0x00020386, 0x0000, 0x0000, {0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46}};
# const GUID PS_PUBLIC_STRINGS    = {0x00020329, 0x0000, 0x0000, {0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46}};
# const GUID PSETID_Appointment = {0x00062002, 0x0000, 0x0000, {0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46}};
# const GUID PSETID_Address       = {0x00062004, 0x0000, 0x0000, {0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46}};
# const GUID PSETID_Common        = {0x00062008, 0x0000, 0x0000, {0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46}};
# const GUID PSETID_Log           = {0x0006200A, 0x0000, 0x0000, {0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46}};
# const GUID PSETID_Meeting  = {0x6ED8DA90, 0x450B, 0x101B, {0x98, 0xDA, 0x00, 0xAA, 0x00, 0x3F, 0x13, 0x05}};
# const GUID PSETID_Task          = {0x00062003, 0x0000, 0x0000, {0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46}};
