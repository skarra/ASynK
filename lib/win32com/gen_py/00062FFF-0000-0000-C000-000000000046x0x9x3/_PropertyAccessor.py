# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.00
# By python version 2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
# From type library '{00062FFF-0000-0000-C000-000000000046}'
# On Mon Jun 20 13:21:17 2011
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
class _PropertyAccessor(DispatchBaseClass):
	CLSID = IID('{0006302D-0000-0000-C000-000000000046}')
	coclass_clsid = IID('{0006102D-0000-0000-C000-000000000046}')

	def BinaryToString(self, Value=defaultNamedNotOptArg):
		# Result is a Unicode object
		return self._oleobj_.InvokeTypes(64259, LCID, 1, (8, 0), ((12, 1),),Value
			)

	def DeleteProperties(self, SchemaNames=defaultNamedNotOptArg):
		return self._ApplyTypes_(64402, 1, (12, 0), ((16396, 1),), u'DeleteProperties', None,SchemaNames
			)

	def DeleteProperty(self, SchemaName=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64401, LCID, 1, (24, 0), ((8, 1),),SchemaName
			)

	def GetProperties(self, SchemaNames=defaultNamedNotOptArg):
		return self._ApplyTypes_(64254, 1, (12, 0), ((12, 1),), u'GetProperties', None,SchemaNames
			)

	def GetProperty(self, SchemaName=defaultNamedNotOptArg):
		return self._ApplyTypes_(64251, 1, (12, 0), ((8, 1),), u'GetProperty', None,SchemaName
			)

	def LocalTimeToUTC(self, Value=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64257, LCID, 1, (7, 0), ((7, 1),),Value
			)

	def SetProperties(self, SchemaNames=defaultNamedNotOptArg, Values=defaultNamedNotOptArg):
		return self._ApplyTypes_(64255, 1, (12, 0), ((12, 1), (12, 1)), u'SetProperties', None,SchemaNames
			, Values)

	def SetProperty(self, SchemaName=defaultNamedNotOptArg, Value=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64252, LCID, 1, (24, 0), ((8, 1), (12, 1)),SchemaName
			, Value)

	def StringToBinary(self, Value=defaultNamedNotOptArg):
		return self._ApplyTypes_(64258, 1, (12, 0), ((8, 1),), u'StringToBinary', None,Value
			)

	def UTCToLocalTime(self, Value=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64256, LCID, 1, (7, 0), ((7, 1),),Value
			)

	_prop_map_get_ = {
		# Method 'Application' returns object of type '_Application'
		"Application": (61440, 2, (9, 0), (), "Application", '{00063001-0000-0000-C000-000000000046}'),
		"Class": (61450, 2, (3, 0), (), "Class", None),
		"Parent": (61441, 2, (9, 0), (), "Parent", None),
		# Method 'Session' returns object of type '_NameSpace'
		"Session": (61451, 2, (9, 0), (), "Session", '{00063002-0000-0000-C000-000000000046}'),
	}
	_prop_map_put_ = {
	}

win32com.client.CLSIDToClass.RegisterCLSID( "{0006302D-0000-0000-C000-000000000046}", _PropertyAccessor )
# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.00
# By python version 2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
# From type library '{00062FFF-0000-0000-C000-000000000046}'
# On Mon Jun 20 13:21:17 2011
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

_PropertyAccessor_vtables_dispatch_ = 1
_PropertyAccessor_vtables_ = [
	(( u'Application' , u'Application' , ), 61440, (61440, (), [ (16393, 10, None, "IID('{00063001-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 28 , (3, 0, None, None) , 0 , )),
	(( u'Class' , u'Class' , ), 61450, (61450, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 32 , (3, 0, None, None) , 0 , )),
	(( u'Session' , u'Session' , ), 61451, (61451, (), [ (16393, 10, None, "IID('{00063002-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 36 , (3, 0, None, None) , 0 , )),
	(( u'Parent' , u'Parent' , ), 61441, (61441, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 40 , (3, 0, None, None) , 0 , )),
	(( u'GetProperty' , u'SchemaName' , u'Value' , ), 64251, (64251, (), [ (8, 1, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 44 , (3, 0, None, None) , 0 , )),
	(( u'SetProperty' , u'SchemaName' , u'Value' , ), 64252, (64252, (), [ (8, 1, None, None) , 
			(12, 1, None, None) , ], 1 , 1 , 4 , 0 , 48 , (3, 0, None, None) , 0 , )),
	(( u'GetProperties' , u'SchemaNames' , u'Values' , ), 64254, (64254, (), [ (12, 1, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 52 , (3, 0, None, None) , 0 , )),
	(( u'SetProperties' , u'SchemaNames' , u'Values' , u'ErrorResults' , ), 64255, (64255, (), [ 
			(12, 1, None, None) , (12, 1, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 56 , (3, 0, None, None) , 0 , )),
	(( u'UTCToLocalTime' , u'Value' , u'ReturnValue' , ), 64256, (64256, (), [ (7, 1, None, None) , 
			(16391, 10, None, None) , ], 1 , 1 , 4 , 0 , 60 , (3, 0, None, None) , 0 , )),
	(( u'LocalTimeToUTC' , u'Value' , u'ReturnValue' , ), 64257, (64257, (), [ (7, 1, None, None) , 
			(16391, 10, None, None) , ], 1 , 1 , 4 , 0 , 64 , (3, 0, None, None) , 0 , )),
	(( u'StringToBinary' , u'Value' , u'ReturnValue' , ), 64258, (64258, (), [ (8, 1, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 68 , (3, 0, None, None) , 0 , )),
	(( u'BinaryToString' , u'Value' , u'ReturnValue' , ), 64259, (64259, (), [ (12, 1, None, None) , 
			(16392, 10, None, None) , ], 1 , 1 , 4 , 0 , 72 , (3, 0, None, None) , 0 , )),
	(( u'DeleteProperty' , u'SchemaName' , ), 64401, (64401, (), [ (8, 1, None, None) , ], 1 , 1 , 4 , 0 , 76 , (3, 0, None, None) , 0 , )),
	(( u'DeleteProperties' , u'SchemaNames' , u'ErrorResults' , ), 64402, (64402, (), [ (16396, 1, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 80 , (3, 0, None, None) , 0 , )),
]

win32com.client.CLSIDToClass.RegisterCLSID( "{0006302D-0000-0000-C000-000000000046}", _PropertyAccessor )
