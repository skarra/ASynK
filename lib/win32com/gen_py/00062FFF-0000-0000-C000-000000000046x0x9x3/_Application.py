# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.00
# By python version 2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
# From type library '{00062FFF-0000-0000-C000-000000000046}'
# On Wed May 04 17:52:40 2011
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
class _Application(DispatchBaseClass):
	CLSID = IID('{00063001-0000-0000-C000-000000000046}')
	coclass_clsid = IID('{0006F03A-0000-0000-C000-000000000046}')

	# Result is of type _Explorer
	def ActiveExplorer(self):
		ret = self._oleobj_.InvokeTypes(273, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, u'ActiveExplorer', '{00063003-0000-0000-C000-000000000046}')
		return ret

	# Result is of type _Inspector
	def ActiveInspector(self):
		ret = self._oleobj_.InvokeTypes(274, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, u'ActiveInspector', '{00063005-0000-0000-C000-000000000046}')
		return ret

	def ActiveWindow(self):
		ret = self._oleobj_.InvokeTypes(287, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, u'ActiveWindow', None)
		return ret

	# Result is of type Search
	def AdvancedSearch(self, Scope=defaultNamedNotOptArg, Filter=defaultNamedOptArg, SearchSubFolders=defaultNamedOptArg, Tag=defaultNamedOptArg):
		ret = self._oleobj_.InvokeTypes(64101, LCID, 1, (9, 0), ((8, 1), (12, 17), (12, 17), (12, 17)),Scope
			, Filter, SearchSubFolders, Tag)
		if ret is not None:
			ret = Dispatch(ret, u'AdvancedSearch', '{0006300B-0000-0000-C000-000000000046}')
		return ret

	def CopyFile(self, FilePath=defaultNamedNotOptArg, DestFolderPath=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(64098, LCID, 1, (9, 0), ((8, 1), (8, 1)),FilePath
			, DestFolderPath)
		if ret is not None:
			ret = Dispatch(ret, u'CopyFile', None)
		return ret

	def CreateItem(self, ItemType=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(266, LCID, 1, (9, 0), ((3, 1),),ItemType
			)
		if ret is not None:
			ret = Dispatch(ret, u'CreateItem', None)
		return ret

	def CreateItemFromTemplate(self, TemplatePath=defaultNamedNotOptArg, InFolder=defaultNamedOptArg):
		ret = self._oleobj_.InvokeTypes(267, LCID, 1, (9, 0), ((8, 1), (12, 17)),TemplatePath
			, InFolder)
		if ret is not None:
			ret = Dispatch(ret, u'CreateItemFromTemplate', None)
		return ret

	def CreateObject(self, ObjectName=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(277, LCID, 1, (9, 0), ((8, 1),),ObjectName
			)
		if ret is not None:
			ret = Dispatch(ret, u'CreateObject', None)
		return ret

	# Result is of type _NameSpace
	def GetNamespace(self, Type=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(272, LCID, 1, (9, 0), ((8, 1),),Type
			)
		if ret is not None:
			ret = Dispatch(ret, u'GetNamespace', '{00063002-0000-0000-C000-000000000046}')
		return ret

	def GetNewNickNames(self, pvar=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64072, LCID, 1, (24, 0), ((16396, 1),),pvar
			)

	def GetObjectReference(self, Item=defaultNamedNotOptArg, ReferenceType=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(64470, LCID, 1, (9, 0), ((9, 1), (3, 1)),Item
			, ReferenceType)
		if ret is not None:
			ret = Dispatch(ret, u'GetObjectReference', None)
		return ret

	def IsSearchSynchronous(self, LookInFolders=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64108, LCID, 1, (11, 0), ((8, 1),),LookInFolders
			)

	def Quit(self):
		return self._oleobj_.InvokeTypes(275, LCID, 1, (24, 0), (),)

	_prop_map_get_ = {
		# Method 'AnswerWizard' returns object of type 'AnswerWizard'
		"AnswerWizard": (285, 2, (9, 0), (), "AnswerWizard", '{000C0360-0000-0000-C000-000000000046}'),
		# Method 'Application' returns object of type '_Application'
		"Application": (61440, 2, (9, 0), (), "Application", '{00063001-0000-0000-C000-000000000046}'),
		# Method 'Assistance' returns object of type 'IAssistance'
		"Assistance": (64520, 2, (9, 0), (), "Assistance", '{4291224C-DEFE-485B-8E69-6CF8AA85CB76}'),
		# Method 'Assistant' returns object of type 'Assistant'
		"Assistant": (276, 2, (9, 0), (), "Assistant", '{000C0322-0000-0000-C000-000000000046}'),
		# Method 'COMAddIns' returns object of type 'COMAddIns'
		"COMAddIns": (280, 2, (9, 0), (), "COMAddIns", '{000C0339-0000-0000-C000-000000000046}'),
		"Class": (61450, 2, (3, 0), (), "Class", None),
		"DefaultProfileName": (64214, 2, (8, 0), (), "DefaultProfileName", None),
		# Method 'Explorers' returns object of type '_Explorers'
		"Explorers": (281, 2, (9, 0), (), "Explorers", '{0006300A-0000-0000-C000-000000000046}'),
		"FeatureInstall": (286, 2, (3, 0), (), "FeatureInstall", None),
		# Method 'Inspectors' returns object of type '_Inspectors'
		"Inspectors": (282, 2, (9, 0), (), "Inspectors", '{00063008-0000-0000-C000-000000000046}'),
		"IsTrusted": (64499, 2, (11, 0), (), "IsTrusted", None),
		# Method 'LanguageSettings' returns object of type 'LanguageSettings'
		"LanguageSettings": (283, 2, (9, 0), (), "LanguageSettings", '{000C0353-0000-0000-C000-000000000046}'),
		"Name": (12289, 2, (8, 0), (), "Name", None),
		"Parent": (61441, 2, (9, 0), (), "Parent", None),
		"ProductCode": (284, 2, (8, 0), (), "ProductCode", None),
		# Method 'Reminders' returns object of type '_Reminders'
		"Reminders": (64153, 2, (9, 0), (), "Reminders", '{000630B1-0000-0000-C000-000000000046}'),
		# Method 'Session' returns object of type '_NameSpace'
		"Session": (61451, 2, (9, 0), (), "Session", '{00063002-0000-0000-C000-000000000046}'),
		# Method 'TimeZones' returns object of type 'TimeZones'
		"TimeZones": (64553, 2, (13, 0), (), "TimeZones", '{000610FC-0000-0000-C000-000000000046}'),
		"Version": (278, 2, (8, 0), (), "Version", None),
	}
	_prop_map_put_ = {
		"FeatureInstall": ((286, LCID, 4, 0),()),
	}

win32com.client.CLSIDToClass.RegisterCLSID( "{00063001-0000-0000-C000-000000000046}", _Application )
# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.00
# By python version 2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
# From type library '{00062FFF-0000-0000-C000-000000000046}'
# On Wed May 04 17:52:40 2011
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

_Application_vtables_dispatch_ = 1
_Application_vtables_ = [
	(( u'Application' , u'Application' , ), 61440, (61440, (), [ (16393, 10, None, "IID('{00063001-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 28 , (3, 0, None, None) , 0 , )),
	(( u'Class' , u'Class' , ), 61450, (61450, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 32 , (3, 0, None, None) , 0 , )),
	(( u'Session' , u'Session' , ), 61451, (61451, (), [ (16393, 10, None, "IID('{00063002-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 36 , (3, 0, None, None) , 0 , )),
	(( u'Parent' , u'Parent' , ), 61441, (61441, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 40 , (3, 0, None, None) , 0 , )),
	(( u'Assistant' , u'Assistant' , ), 276, (276, (), [ (16393, 10, None, "IID('{000C0322-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 44 , (3, 0, None, None) , 64 , )),
	(( u'Name' , u'Name' , ), 12289, (12289, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 48 , (3, 0, None, None) , 0 , )),
	(( u'Version' , u'Version' , ), 278, (278, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 52 , (3, 0, None, None) , 0 , )),
	(( u'ActiveExplorer' , u'ActiveExplorer' , ), 273, (273, (), [ (16393, 10, None, "IID('{00063003-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 56 , (3, 0, None, None) , 0 , )),
	(( u'ActiveInspector' , u'ActiveInspector' , ), 274, (274, (), [ (16393, 10, None, "IID('{00063005-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 60 , (3, 0, None, None) , 0 , )),
	(( u'CreateItem' , u'ItemType' , u'Item' , ), 266, (266, (), [ (3, 1, None, None) , 
			(16393, 10, None, None) , ], 1 , 1 , 4 , 0 , 64 , (3, 0, None, None) , 0 , )),
	(( u'CreateItemFromTemplate' , u'TemplatePath' , u'InFolder' , u'Item' , ), 267, (267, (), [ 
			(8, 1, None, None) , (12, 17, None, None) , (16393, 10, None, None) , ], 1 , 1 , 4 , 1 , 68 , (3, 0, None, None) , 0 , )),
	(( u'CreateObject' , u'ObjectName' , u'Object' , ), 277, (277, (), [ (8, 1, None, None) , 
			(16393, 10, None, None) , ], 1 , 1 , 4 , 0 , 72 , (3, 0, None, None) , 0 , )),
	(( u'GetNamespace' , u'Type' , u'NameSpace' , ), 272, (272, (), [ (8, 1, None, None) , 
			(16393, 10, None, "IID('{00063002-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 76 , (3, 0, None, None) , 0 , )),
	(( u'Quit' , ), 275, (275, (), [ ], 1 , 1 , 4 , 0 , 80 , (3, 0, None, None) , 0 , )),
	(( u'COMAddIns' , u'COMAddIns' , ), 280, (280, (), [ (16393, 10, None, "IID('{000C0339-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 84 , (3, 0, None, None) , 0 , )),
	(( u'Explorers' , u'Explorers' , ), 281, (281, (), [ (16393, 10, None, "IID('{0006300A-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 88 , (3, 0, None, None) , 0 , )),
	(( u'Inspectors' , u'Inspectors' , ), 282, (282, (), [ (16393, 10, None, "IID('{00063008-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 92 , (3, 0, None, None) , 0 , )),
	(( u'LanguageSettings' , u'LanguageSettings' , ), 283, (283, (), [ (16393, 10, None, "IID('{000C0353-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 96 , (3, 0, None, None) , 0 , )),
	(( u'ProductCode' , u'ProductCode' , ), 284, (284, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 100 , (3, 0, None, None) , 0 , )),
	(( u'AnswerWizard' , u'AnswerWizard' , ), 285, (285, (), [ (16393, 10, None, "IID('{000C0360-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 104 , (3, 0, None, None) , 64 , )),
	(( u'FeatureInstall' , u'FeatureInstall' , ), 286, (286, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 108 , (3, 0, None, None) , 64 , )),
	(( u'FeatureInstall' , u'FeatureInstall' , ), 286, (286, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 112 , (3, 0, None, None) , 64 , )),
	(( u'ActiveWindow' , u'ActiveWindow' , ), 287, (287, (), [ (16393, 10, None, None) , ], 1 , 1 , 4 , 0 , 116 , (3, 0, None, None) , 0 , )),
	(( u'CopyFile' , u'FilePath' , u'DestFolderPath' , u'DocItem' , ), 64098, (64098, (), [ 
			(8, 1, None, None) , (8, 1, None, None) , (16393, 10, None, None) , ], 1 , 1 , 4 , 0 , 120 , (3, 0, None, None) , 0 , )),
	(( u'AdvancedSearch' , u'Scope' , u'Filter' , u'SearchSubFolders' , u'Tag' , 
			u'AdvancedSearch' , ), 64101, (64101, (), [ (8, 1, None, None) , (12, 17, None, None) , (12, 17, None, None) , 
			(12, 17, None, None) , (16393, 10, None, "IID('{0006300B-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 3 , 124 , (3, 0, None, None) , 0 , )),
	(( u'IsSearchSynchronous' , u'LookInFolders' , u'IsSearchSynchronous' , ), 64108, (64108, (), [ (8, 1, None, None) , 
			(16395, 10, None, None) , ], 1 , 1 , 4 , 0 , 128 , (3, 0, None, None) , 0 , )),
	(( u'GetNewNickNames' , u'pvar' , ), 64072, (64072, (), [ (16396, 1, None, None) , ], 1 , 1 , 4 , 0 , 132 , (3, 0, None, None) , 64 , )),
	(( u'Reminders' , u'Reminders' , ), 64153, (64153, (), [ (16393, 10, None, "IID('{000630B1-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 136 , (3, 0, None, None) , 0 , )),
	(( u'DefaultProfileName' , u'DefaultProfileName' , ), 64214, (64214, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 140 , (3, 0, None, None) , 0 , )),
	(( u'IsTrusted' , u'IsTrusted' , ), 64499, (64499, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 144 , (3, 0, None, None) , 0 , )),
	(( u'GetObjectReference' , u'Item' , u'ReferenceType' , u'NewObject' , ), 64470, (64470, (), [ 
			(9, 1, None, None) , (3, 1, None, None) , (16393, 10, None, None) , ], 1 , 1 , 4 , 0 , 148 , (3, 0, None, None) , 0 , )),
	(( u'Assistance' , u'Assistance' , ), 64520, (64520, (), [ (16393, 10, None, "IID('{4291224C-DEFE-485B-8E69-6CF8AA85CB76}')") , ], 1 , 2 , 4 , 0 , 152 , (3, 0, None, None) , 0 , )),
	(( u'TimeZones' , u'TimeZones' , ), 64553, (64553, (), [ (16397, 10, None, "IID('{000610FC-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 156 , (3, 0, None, None) , 0 , )),
]

win32com.client.CLSIDToClass.RegisterCLSID( "{00063001-0000-0000-C000-000000000046}", _Application )
