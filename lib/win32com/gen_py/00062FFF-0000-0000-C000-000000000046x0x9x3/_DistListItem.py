# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.00
# By python version 2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
# From type library '{00062FFF-0000-0000-C000-000000000046}'
# On Wed May 04 17:52:54 2011
"""Microsoft Outlook 12.0 Object Library"""
makepy_version = '0.5.00'
python_version = 0x20504f0

import win32com.client.CLSIDToClass, pythoncom, pywintypes
import win32com.client.util
from pywintypes import IID
from win32com.client import Dispatch

# The following 3 lines may need tweaking for the particular server
# Candidates are pythoncom.Missing, .Empty and .ArgNotFound
defaultNamedOptArg=pythoncom.Empty
defaultNamedNotOptArg=pythoncom.Empty
defaultUnnamedArg=pythoncom.Empty

CLSID = IID('{00062FFF-0000-0000-C000-000000000046}')
MajorVersion = 9
MinorVersion = 3
LibraryFlags = 8
LCID = 0x0

from win32com.client import DispatchBaseClass
class _DistListItem(DispatchBaseClass):
	CLSID = IID('{00063081-0000-0000-C000-000000000046}')
	coclass_clsid = IID('{0006103C-0000-0000-C000-000000000046}')

	def AddMember(self, Recipient=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64140, LCID, 1, (24, 0), ((9, 1),),Recipient
			)

	def AddMembers(self, Recipients=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(63744, LCID, 1, (24, 0), ((9, 1),),Recipients
			)

	def ClearTaskFlag(self):
		return self._oleobj_.InvokeTypes(64521, LCID, 1, (24, 0), (),)

	def Close(self, SaveMode=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(61475, LCID, 1, (24, 0), ((3, 1),),SaveMode
			)

	def Copy(self):
		ret = self._oleobj_.InvokeTypes(61490, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, u'Copy', None)
		return ret

	def Delete(self):
		return self._oleobj_.InvokeTypes(61514, LCID, 1, (24, 0), (),)

	def Display(self, Modal=defaultNamedOptArg):
		return self._oleobj_.InvokeTypes(61606, LCID, 1, (24, 0), ((12, 17),),Modal
			)

	# Result is of type Recipient
	def GetMember(self, Index=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(63749, LCID, 1, (9, 0), ((3, 1),),Index
			)
		if ret is not None:
			ret = Dispatch(ret, u'GetMember', '{00063045-0000-0000-C000-000000000046}')
		return ret

	def MarkAsTask(self, MarkInterval=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64510, LCID, 1, (24, 0), ((3, 1),),MarkInterval
			)

	def Move(self, DestFldr=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(61492, LCID, 1, (9, 0), ((9, 1),),DestFldr
			)
		if ret is not None:
			ret = Dispatch(ret, u'Move', None)
		return ret

	def PrintOut(self):
		return self._oleobj_.InvokeTypes(61491, LCID, 1, (24, 0), (),)

	def RemoveMember(self, Recipient=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64141, LCID, 1, (24, 0), ((9, 1),),Recipient
			)

	def RemoveMembers(self, Recipients=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(63745, LCID, 1, (24, 0), ((9, 1),),Recipients
			)

	def Save(self):
		return self._oleobj_.InvokeTypes(61512, LCID, 1, (24, 0), (),)

	def SaveAs(self, Path=defaultNamedNotOptArg, Type=defaultNamedOptArg):
		return self._oleobj_.InvokeTypes(61521, LCID, 1, (24, 0), ((8, 1), (12, 17)),Path
			, Type)

	def ShowCategoriesDialog(self):
		return self._oleobj_.InvokeTypes(64011, LCID, 1, (24, 0), (),)

	_prop_map_get_ = {
		# Method 'Actions' returns object of type 'Actions'
		"Actions": (63511, 2, (9, 0), (), "Actions", '{0006303E-0000-0000-C000-000000000046}'),
		# Method 'Application' returns object of type '_Application'
		"Application": (61440, 2, (9, 0), (), "Application", '{00063001-0000-0000-C000-000000000046}'),
		# Method 'Attachments' returns object of type 'Attachments'
		"Attachments": (63509, 2, (9, 0), (), "Attachments", '{0006303C-0000-0000-C000-000000000046}'),
		"AutoResolvedWinner": (64186, 2, (11, 0), (), "AutoResolvedWinner", None),
		"BillingInformation": (34101, 2, (8, 0), (), "BillingInformation", None),
		"Body": (37120, 2, (8, 0), (), "Body", None),
		"Categories": (36865, 2, (8, 0), (), "Categories", None),
		"CheckSum": (32844, 2, (3, 0), (), "CheckSum", None),
		"Class": (61450, 2, (3, 0), (), "Class", None),
		"Companies": (34107, 2, (8, 0), (), "Companies", None),
		# Method 'Conflicts' returns object of type 'Conflicts'
		"Conflicts": (64187, 2, (9, 0), (), "Conflicts", '{000630C2-0000-0000-C000-000000000046}'),
		"ConversationIndex": (64192, 2, (8, 0), (), "ConversationIndex", None),
		"ConversationTopic": (112, 2, (8, 0), (), "ConversationTopic", None),
		"CreationTime": (12295, 2, (7, 0), (), "CreationTime", None),
		"DLName": (32851, 2, (8, 0), (), "DLName", None),
		"DownloadState": (64077, 2, (3, 0), (), "DownloadState", None),
		"EntryID": (61470, 2, (8, 0), (), "EntryID", None),
		# Method 'FormDescription' returns object of type 'FormDescription'
		"FormDescription": (61589, 2, (9, 0), (), "FormDescription", '{00063046-0000-0000-C000-000000000046}'),
		# Method 'GetInspector' returns object of type '_Inspector'
		"GetInspector": (61502, 2, (9, 0), (), "GetInspector", '{00063005-0000-0000-C000-000000000046}'),
		"Importance": (23, 2, (3, 0), (), "Importance", None),
		"IsConflict": (64164, 2, (11, 0), (), "IsConflict", None),
		"IsMarkedAsTask": (64522, 2, (11, 0), (), "IsMarkedAsTask", None),
		# Method 'ItemProperties' returns object of type 'ItemProperties'
		"ItemProperties": (64009, 2, (9, 0), (), "ItemProperties", '{000630A8-0000-0000-C000-000000000046}'),
		"LastModificationTime": (12296, 2, (7, 0), (), "LastModificationTime", None),
		# Method 'Links' returns object of type 'Links'
		"Links": (62469, 2, (9, 0), (), "Links", '{0006308A-0000-0000-C000-000000000046}'),
		"MAPIOBJECT": (61696, 2, (13, 0), (), "MAPIOBJECT", None),
		"MarkForDownload": (34161, 2, (3, 0), (), "MarkForDownload", None),
		"MemberCount": (32843, 2, (3, 0), (), "MemberCount", None),
		"Members": (32853, 2, (12, 0), (), "Members", None),
		"MessageClass": (26, 2, (8, 0), (), "MessageClass", None),
		"Mileage": (34100, 2, (8, 0), (), "Mileage", None),
		"NoAging": (34062, 2, (11, 0), (), "NoAging", None),
		"OneOffMembers": (32852, 2, (12, 0), (), "OneOffMembers", None),
		"OutlookInternalVersion": (34130, 2, (3, 0), (), "OutlookInternalVersion", None),
		"OutlookVersion": (34132, 2, (8, 0), (), "OutlookVersion", None),
		"Parent": (61441, 2, (9, 0), (), "Parent", None),
		# Method 'PropertyAccessor' returns object of type 'PropertyAccessor'
		"PropertyAccessor": (64253, 2, (13, 0), (), "PropertyAccessor", '{0006102D-0000-0000-C000-000000000046}'),
		"ReminderOverrideDefault": (34076, 2, (11, 0), (), "ReminderOverrideDefault", None),
		"ReminderPlaySound": (34078, 2, (11, 0), (), "ReminderPlaySound", None),
		"ReminderSet": (34051, 2, (11, 0), (), "ReminderSet", None),
		"ReminderSoundFile": (34079, 2, (8, 0), (), "ReminderSoundFile", None),
		"ReminderTime": (34050, 2, (7, 0), (), "ReminderTime", None),
		"Saved": (61603, 2, (11, 0), (), "Saved", None),
		"Sensitivity": (54, 2, (3, 0), (), "Sensitivity", None),
		# Method 'Session' returns object of type '_NameSpace'
		"Session": (61451, 2, (9, 0), (), "Session", '{00063002-0000-0000-C000-000000000046}'),
		"Size": (3592, 2, (3, 0), (), "Size", None),
		"Subject": (55, 2, (8, 0), (), "Subject", None),
		"TaskCompletedDate": (33039, 2, (7, 0), (), "TaskCompletedDate", None),
		"TaskDueDate": (33029, 2, (7, 0), (), "TaskDueDate", None),
		"TaskStartDate": (33028, 2, (7, 0), (), "TaskStartDate", None),
		"TaskSubject": (64543, 2, (8, 0), (), "TaskSubject", None),
		"ToDoTaskOrdinal": (34208, 2, (7, 0), (), "ToDoTaskOrdinal", None),
		"UnRead": (61468, 2, (11, 0), (), "UnRead", None),
		# Method 'UserProperties' returns object of type 'UserProperties'
		"UserProperties": (63510, 2, (9, 0), (), "UserProperties", '{0006303D-0000-0000-C000-000000000046}'),
	}
	_prop_map_put_ = {
		"BillingInformation": ((34101, LCID, 4, 0),()),
		"Body": ((37120, LCID, 4, 0),()),
		"Categories": ((36865, LCID, 4, 0),()),
		"Companies": ((34107, LCID, 4, 0),()),
		"DLName": ((32851, LCID, 4, 0),()),
		"Importance": ((23, LCID, 4, 0),()),
		"MarkForDownload": ((34161, LCID, 4, 0),()),
		"Members": ((32853, LCID, 4, 0),()),
		"MessageClass": ((26, LCID, 4, 0),()),
		"Mileage": ((34100, LCID, 4, 0),()),
		"NoAging": ((34062, LCID, 4, 0),()),
		"OneOffMembers": ((32852, LCID, 4, 0),()),
		"ReminderOverrideDefault": ((34076, LCID, 4, 0),()),
		"ReminderPlaySound": ((34078, LCID, 4, 0),()),
		"ReminderSet": ((34051, LCID, 4, 0),()),
		"ReminderSoundFile": ((34079, LCID, 4, 0),()),
		"ReminderTime": ((34050, LCID, 4, 0),()),
		"Sensitivity": ((54, LCID, 4, 0),()),
		"Subject": ((55, LCID, 4, 0),()),
		"TaskCompletedDate": ((33039, LCID, 4, 0),()),
		"TaskDueDate": ((33029, LCID, 4, 0),()),
		"TaskStartDate": ((33028, LCID, 4, 0),()),
		"TaskSubject": ((64543, LCID, 4, 0),()),
		"ToDoTaskOrdinal": ((34208, LCID, 4, 0),()),
		"UnRead": ((61468, LCID, 4, 0),()),
	}

win32com.client.CLSIDToClass.RegisterCLSID( "{00063081-0000-0000-C000-000000000046}", _DistListItem )
# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.00
# By python version 2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
# From type library '{00062FFF-0000-0000-C000-000000000046}'
# On Wed May 04 17:52:54 2011
"""Microsoft Outlook 12.0 Object Library"""
makepy_version = '0.5.00'
python_version = 0x20504f0

import win32com.client.CLSIDToClass, pythoncom, pywintypes
import win32com.client.util
from pywintypes import IID
from win32com.client import Dispatch

# The following 3 lines may need tweaking for the particular server
# Candidates are pythoncom.Missing, .Empty and .ArgNotFound
defaultNamedOptArg=pythoncom.Empty
defaultNamedNotOptArg=pythoncom.Empty
defaultUnnamedArg=pythoncom.Empty

CLSID = IID('{00062FFF-0000-0000-C000-000000000046}')
MajorVersion = 9
MinorVersion = 3
LibraryFlags = 8
LCID = 0x0

_DistListItem_vtables_dispatch_ = 1
_DistListItem_vtables_ = [
	(( u'Application' , u'Application' , ), 61440, (61440, (), [ (16393, 10, None, "IID('{00063001-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 28 , (3, 0, None, None) , 0 , )),
	(( u'Class' , u'Class' , ), 61450, (61450, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 32 , (3, 0, None, None) , 0 , )),
	(( u'Session' , u'Session' , ), 61451, (61451, (), [ (16393, 10, None, "IID('{00063002-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 36 , (3, 0, None, None) , 0 , )),
	(( u'Parent' , u'Parent' , ), 61441, (61441, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 40 , (3, 0, None, None) , 0 , )),
	(( u'Actions' , u'Actions' , ), 63511, (63511, (), [ (16393, 10, None, "IID('{0006303E-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 44 , (3, 0, None, None) , 0 , )),
	(( u'Attachments' , u'Attachments' , ), 63509, (63509, (), [ (16393, 10, None, "IID('{0006303C-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 48 , (3, 0, None, None) , 0 , )),
	(( u'BillingInformation' , u'BillingInformation' , ), 34101, (34101, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 52 , (3, 0, None, None) , 0 , )),
	(( u'BillingInformation' , u'BillingInformation' , ), 34101, (34101, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 56 , (3, 0, None, None) , 0 , )),
	(( u'Body' , u'Body' , ), 37120, (37120, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 60 , (3, 0, None, None) , 0 , )),
	(( u'Body' , u'Body' , ), 37120, (37120, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 64 , (3, 0, None, None) , 0 , )),
	(( u'Categories' , u'Categories' , ), 36865, (36865, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 68 , (3, 0, None, None) , 0 , )),
	(( u'Categories' , u'Categories' , ), 36865, (36865, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 72 , (3, 0, None, None) , 0 , )),
	(( u'Companies' , u'Companies' , ), 34107, (34107, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 76 , (3, 0, None, None) , 0 , )),
	(( u'Companies' , u'Companies' , ), 34107, (34107, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 80 , (3, 0, None, None) , 0 , )),
	(( u'ConversationIndex' , u'ConversationIndex' , ), 64192, (64192, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 84 , (3, 0, None, None) , 0 , )),
	(( u'ConversationTopic' , u'ConversationTopic' , ), 112, (112, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 88 , (3, 0, None, None) , 0 , )),
	(( u'CreationTime' , u'CreationTime' , ), 12295, (12295, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 92 , (3, 0, None, None) , 0 , )),
	(( u'EntryID' , u'EntryID' , ), 61470, (61470, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 96 , (3, 0, None, None) , 0 , )),
	(( u'FormDescription' , u'FormDescription' , ), 61589, (61589, (), [ (16393, 10, None, "IID('{00063046-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 100 , (3, 0, None, None) , 0 , )),
	(( u'GetInspector' , u'GetInspector' , ), 61502, (61502, (), [ (16393, 10, None, "IID('{00063005-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 104 , (3, 0, None, None) , 0 , )),
	(( u'Importance' , u'Importance' , ), 23, (23, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 108 , (3, 0, None, None) , 0 , )),
	(( u'Importance' , u'Importance' , ), 23, (23, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 112 , (3, 0, None, None) , 0 , )),
	(( u'LastModificationTime' , u'LastModificationTime' , ), 12296, (12296, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 116 , (3, 0, None, None) , 0 , )),
	(( u'MAPIOBJECT' , u'MAPIOBJECT' , ), 61696, (61696, (), [ (16397, 10, None, None) , ], 1 , 2 , 4 , 0 , 120 , (3, 0, None, None) , 64 , )),
	(( u'MessageClass' , u'MessageClass' , ), 26, (26, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 124 , (3, 0, None, None) , 0 , )),
	(( u'MessageClass' , u'MessageClass' , ), 26, (26, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 128 , (3, 0, None, None) , 0 , )),
	(( u'Mileage' , u'Mileage' , ), 34100, (34100, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 132 , (3, 0, None, None) , 0 , )),
	(( u'Mileage' , u'Mileage' , ), 34100, (34100, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 136 , (3, 0, None, None) , 0 , )),
	(( u'NoAging' , u'NoAging' , ), 34062, (34062, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 140 , (3, 0, None, None) , 0 , )),
	(( u'NoAging' , u'NoAging' , ), 34062, (34062, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 144 , (3, 0, None, None) , 0 , )),
	(( u'OutlookInternalVersion' , u'OutlookInternalVersion' , ), 34130, (34130, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 148 , (3, 0, None, None) , 0 , )),
	(( u'OutlookVersion' , u'OutlookVersion' , ), 34132, (34132, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 152 , (3, 0, None, None) , 0 , )),
	(( u'Saved' , u'Saved' , ), 61603, (61603, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 156 , (3, 0, None, None) , 0 , )),
	(( u'Sensitivity' , u'Sensitivity' , ), 54, (54, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 160 , (3, 0, None, None) , 0 , )),
	(( u'Sensitivity' , u'Sensitivity' , ), 54, (54, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 164 , (3, 0, None, None) , 0 , )),
	(( u'Size' , u'Size' , ), 3592, (3592, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 168 , (3, 0, None, None) , 0 , )),
	(( u'Subject' , u'Subject' , ), 55, (55, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 172 , (3, 0, None, None) , 0 , )),
	(( u'Subject' , u'Subject' , ), 55, (55, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 176 , (3, 0, None, None) , 0 , )),
	(( u'UnRead' , u'UnRead' , ), 61468, (61468, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 180 , (3, 0, None, None) , 0 , )),
	(( u'UnRead' , u'UnRead' , ), 61468, (61468, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 184 , (3, 0, None, None) , 0 , )),
	(( u'UserProperties' , u'UserProperties' , ), 63510, (63510, (), [ (16393, 10, None, "IID('{0006303D-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 188 , (3, 0, None, None) , 0 , )),
	(( u'Close' , u'SaveMode' , ), 61475, (61475, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 192 , (3, 0, None, None) , 0 , )),
	(( u'Copy' , u'Item' , ), 61490, (61490, (), [ (16393, 10, None, None) , ], 1 , 1 , 4 , 0 , 196 , (3, 0, None, None) , 0 , )),
	(( u'Delete' , ), 61514, (61514, (), [ ], 1 , 1 , 4 , 0 , 200 , (3, 0, None, None) , 0 , )),
	(( u'Display' , u'Modal' , ), 61606, (61606, (), [ (12, 17, None, None) , ], 1 , 1 , 4 , 1 , 204 , (3, 0, None, None) , 0 , )),
	(( u'Move' , u'DestFldr' , u'Item' , ), 61492, (61492, (), [ (9, 1, None, "IID('{00063006-0000-0000-C000-000000000046}')") , 
			(16393, 10, None, None) , ], 1 , 1 , 4 , 0 , 208 , (3, 0, None, None) , 0 , )),
	(( u'PrintOut' , ), 61491, (61491, (), [ ], 1 , 1 , 4 , 0 , 212 , (3, 0, None, None) , 0 , )),
	(( u'Save' , ), 61512, (61512, (), [ ], 1 , 1 , 4 , 0 , 216 , (3, 0, None, None) , 0 , )),
	(( u'SaveAs' , u'Path' , u'Type' , ), 61521, (61521, (), [ (8, 1, None, None) , 
			(12, 17, None, None) , ], 1 , 1 , 4 , 1 , 220 , (3, 0, None, None) , 0 , )),
	(( u'DLName' , u'DLName' , ), 32851, (32851, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 224 , (3, 0, None, None) , 0 , )),
	(( u'DLName' , u'DLName' , ), 32851, (32851, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 228 , (3, 0, None, None) , 0 , )),
	(( u'MemberCount' , u'MemberCount' , ), 32843, (32843, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 232 , (3, 0, None, None) , 0 , )),
	(( u'CheckSum' , u'CheckSum' , ), 32844, (32844, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 236 , (3, 0, None, None) , 64 , )),
	(( u'Members' , u'Members' , ), 32853, (32853, (), [ (16396, 10, None, None) , ], 1 , 2 , 4 , 0 , 240 , (3, 0, None, None) , 64 , )),
	(( u'Members' , u'Members' , ), 32853, (32853, (), [ (12, 1, None, None) , ], 1 , 4 , 4 , 0 , 244 , (3, 0, None, None) , 64 , )),
	(( u'OneOffMembers' , u'OneOffMembers' , ), 32852, (32852, (), [ (16396, 10, None, None) , ], 1 , 2 , 4 , 0 , 248 , (3, 0, None, None) , 64 , )),
	(( u'OneOffMembers' , u'OneOffMembers' , ), 32852, (32852, (), [ (12, 1, None, None) , ], 1 , 4 , 4 , 0 , 252 , (3, 0, None, None) , 64 , )),
	(( u'Links' , u'Links' , ), 62469, (62469, (), [ (16393, 10, None, "IID('{0006308A-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 256 , (3, 0, None, None) , 0 , )),
	(( u'AddMembers' , u'Recipients' , ), 63744, (63744, (), [ (9, 1, None, "IID('{0006303B-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 260 , (3, 0, None, None) , 0 , )),
	(( u'RemoveMembers' , u'Recipients' , ), 63745, (63745, (), [ (9, 1, None, "IID('{0006303B-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 264 , (3, 0, None, None) , 0 , )),
	(( u'GetMember' , u'Index' , u'Recipient' , ), 63749, (63749, (), [ (3, 1, None, None) , 
			(16393, 10, None, "IID('{00063045-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 268 , (3, 0, None, None) , 0 , )),
	(( u'DownloadState' , u'DownloadState' , ), 64077, (64077, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 272 , (3, 0, None, None) , 0 , )),
	(( u'ShowCategoriesDialog' , ), 64011, (64011, (), [ ], 1 , 1 , 4 , 0 , 276 , (3, 0, None, None) , 0 , )),
	(( u'AddMember' , u'Recipient' , ), 64140, (64140, (), [ (9, 1, None, "IID('{00063045-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 280 , (3, 0, None, None) , 0 , )),
	(( u'RemoveMember' , u'Recipient' , ), 64141, (64141, (), [ (9, 1, None, "IID('{00063045-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 284 , (3, 0, None, None) , 0 , )),
	(( u'ItemProperties' , u'ItemProperties' , ), 64009, (64009, (), [ (16393, 10, None, "IID('{000630A8-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 288 , (3, 0, None, None) , 0 , )),
	(( u'MarkForDownload' , u'MarkForDownload' , ), 34161, (34161, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 292 , (3, 0, None, None) , 0 , )),
	(( u'MarkForDownload' , u'MarkForDownload' , ), 34161, (34161, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 296 , (3, 0, None, None) , 0 , )),
	(( u'IsConflict' , u'IsConflict' , ), 64164, (64164, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 300 , (3, 0, None, None) , 0 , )),
	(( u'AutoResolvedWinner' , u'AutoResolvedWinner' , ), 64186, (64186, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 304 , (3, 0, None, None) , 0 , )),
	(( u'Conflicts' , u'Conflicts' , ), 64187, (64187, (), [ (16393, 10, None, "IID('{000630C2-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 308 , (3, 0, None, None) , 0 , )),
	(( u'PropertyAccessor' , u'PropertyAccessor' , ), 64253, (64253, (), [ (16397, 10, None, "IID('{0006102D-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 312 , (3, 0, None, None) , 0 , )),
	(( u'TaskSubject' , u'TaskSubject' , ), 64543, (64543, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 316 , (3, 0, None, None) , 0 , )),
	(( u'TaskSubject' , u'TaskSubject' , ), 64543, (64543, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 320 , (3, 0, None, None) , 0 , )),
	(( u'TaskDueDate' , u'TaskDueDate' , ), 33029, (33029, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 324 , (3, 0, None, None) , 0 , )),
	(( u'TaskDueDate' , u'TaskDueDate' , ), 33029, (33029, (), [ (7, 1, None, None) , ], 1 , 4 , 4 , 0 , 328 , (3, 0, None, None) , 0 , )),
	(( u'TaskStartDate' , u'TaskStartDate' , ), 33028, (33028, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 332 , (3, 0, None, None) , 0 , )),
	(( u'TaskStartDate' , u'TaskStartDate' , ), 33028, (33028, (), [ (7, 1, None, None) , ], 1 , 4 , 4 , 0 , 336 , (3, 0, None, None) , 0 , )),
	(( u'TaskCompletedDate' , u'TaskCompletedDate' , ), 33039, (33039, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 340 , (3, 0, None, None) , 0 , )),
	(( u'TaskCompletedDate' , u'TaskCompletedDate' , ), 33039, (33039, (), [ (7, 1, None, None) , ], 1 , 4 , 4 , 0 , 344 , (3, 0, None, None) , 0 , )),
	(( u'ToDoTaskOrdinal' , u'ToDoTaskOrdinal' , ), 34208, (34208, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 348 , (3, 0, None, None) , 0 , )),
	(( u'ToDoTaskOrdinal' , u'ToDoTaskOrdinal' , ), 34208, (34208, (), [ (7, 1, None, None) , ], 1 , 4 , 4 , 0 , 352 , (3, 0, None, None) , 0 , )),
	(( u'ReminderOverrideDefault' , u'ReminderOverrideDefault' , ), 34076, (34076, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 356 , (3, 0, None, None) , 0 , )),
	(( u'ReminderOverrideDefault' , u'ReminderOverrideDefault' , ), 34076, (34076, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 360 , (3, 0, None, None) , 0 , )),
	(( u'ReminderPlaySound' , u'ReminderPlaySound' , ), 34078, (34078, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 364 , (3, 0, None, None) , 0 , )),
	(( u'ReminderPlaySound' , u'ReminderPlaySound' , ), 34078, (34078, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 368 , (3, 0, None, None) , 0 , )),
	(( u'ReminderSet' , u'ReminderSet' , ), 34051, (34051, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 372 , (3, 0, None, None) , 0 , )),
	(( u'ReminderSet' , u'ReminderSet' , ), 34051, (34051, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 376 , (3, 0, None, None) , 0 , )),
	(( u'ReminderSoundFile' , u'ReminderSoundFile' , ), 34079, (34079, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 380 , (3, 0, None, None) , 0 , )),
	(( u'ReminderSoundFile' , u'ReminderSoundFile' , ), 34079, (34079, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 384 , (3, 0, None, None) , 0 , )),
	(( u'ReminderTime' , u'ReminderTime' , ), 34050, (34050, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 388 , (3, 0, None, None) , 0 , )),
	(( u'ReminderTime' , u'ReminderTime' , ), 34050, (34050, (), [ (7, 1, None, None) , ], 1 , 4 , 4 , 0 , 392 , (3, 0, None, None) , 0 , )),
	(( u'MarkAsTask' , u'MarkInterval' , ), 64510, (64510, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 396 , (3, 0, None, None) , 0 , )),
	(( u'ClearTaskFlag' , ), 64521, (64521, (), [ ], 1 , 1 , 4 , 0 , 400 , (3, 0, None, None) , 0 , )),
	(( u'IsMarkedAsTask' , u'IsMarkedAsTask' , ), 64522, (64522, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 404 , (3, 0, None, None) , 0 , )),
]

win32com.client.CLSIDToClass.RegisterCLSID( "{00063081-0000-0000-C000-000000000046}", _DistListItem )
