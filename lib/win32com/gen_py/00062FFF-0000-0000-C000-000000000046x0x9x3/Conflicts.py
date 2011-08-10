# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.00
# By python version 2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
# From type library '{00062FFF-0000-0000-C000-000000000046}'
# On Mon Jun 20 13:18:19 2011
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
class Conflicts(DispatchBaseClass):
	CLSID = IID('{000630C2-0000-0000-C000-000000000046}')
	coclass_clsid = None

	# Result is of type Conflict
	def GetFirst(self):
		ret = self._oleobj_.InvokeTypes(86, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, u'GetFirst', '{000630C3-0000-0000-C000-000000000046}')
		return ret

	# Result is of type Conflict
	def GetLast(self):
		ret = self._oleobj_.InvokeTypes(88, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, u'GetLast', '{000630C3-0000-0000-C000-000000000046}')
		return ret

	# Result is of type Conflict
	def GetNext(self):
		ret = self._oleobj_.InvokeTypes(87, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, u'GetNext', '{000630C3-0000-0000-C000-000000000046}')
		return ret

	# Result is of type Conflict
	def GetPrevious(self):
		ret = self._oleobj_.InvokeTypes(89, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, u'GetPrevious', '{000630C3-0000-0000-C000-000000000046}')
		return ret

	# Result is of type Conflict
	def Item(self, Index=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(81, LCID, 1, (9, 0), ((12, 1),),Index
			)
		if ret is not None:
			ret = Dispatch(ret, u'Item', '{000630C3-0000-0000-C000-000000000046}')
		return ret

	_prop_map_get_ = {
		# Method 'Application' returns object of type '_Application'
		"Application": (61440, 2, (9, 0), (), "Application", '{00063001-0000-0000-C000-000000000046}'),
		"Class": (61450, 2, (3, 0), (), "Class", None),
		"Count": (80, 2, (3, 0), (), "Count", None),
		"Parent": (61441, 2, (9, 0), (), "Parent", None),
		# Method 'Session' returns object of type '_NameSpace'
		"Session": (61451, 2, (9, 0), (), "Session", '{00063002-0000-0000-C000-000000000046}'),
	}
	_prop_map_put_ = {
	}
	#This class has Item property/method which may take args - allow indexed access
	def __getitem__(self, item):
		return self._get_good_object_(self._oleobj_.Invoke(*(81, LCID, 1, 1, item)), "Item")
	#This class has Count() property - allow len(ob) to provide this
	def __len__(self):
		return self._ApplyTypes_(*(80, 2, (3, 0), (), "Count", None))
	#This class has a __len__ - this is needed so 'if object:' always returns TRUE.
	def __nonzero__(self):
		return True

win32com.client.CLSIDToClass.RegisterCLSID( "{000630C2-0000-0000-C000-000000000046}", Conflicts )
# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.00
# By python version 2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
# From type library '{00062FFF-0000-0000-C000-000000000046}'
# On Mon Jun 20 13:18:19 2011
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

Conflicts_vtables_dispatch_ = 1
Conflicts_vtables_ = [
	(( u'Application' , u'Application' , ), 61440, (61440, (), [ (16393, 10, None, "IID('{00063001-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 28 , (3, 0, None, None) , 0 , )),
	(( u'Class' , u'Class' , ), 61450, (61450, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 32 , (3, 0, None, None) , 0 , )),
	(( u'Session' , u'Session' , ), 61451, (61451, (), [ (16393, 10, None, "IID('{00063002-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 36 , (3, 0, None, None) , 0 , )),
	(( u'Parent' , u'Parent' , ), 61441, (61441, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 40 , (3, 0, None, None) , 0 , )),
	(( u'Count' , u'Count' , ), 80, (80, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 44 , (3, 0, None, None) , 0 , )),
	(( u'Item' , u'Index' , u'Item' , ), 81, (81, (), [ (12, 1, None, None) , 
			(16393, 10, None, "IID('{000630C3-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 48 , (3, 0, None, None) , 0 , )),
	(( u'GetFirst' , u'Item' , ), 86, (86, (), [ (16393, 10, None, "IID('{000630C3-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 52 , (3, 0, None, None) , 0 , )),
	(( u'GetLast' , u'Item' , ), 88, (88, (), [ (16393, 10, None, "IID('{000630C3-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 56 , (3, 0, None, None) , 0 , )),
	(( u'GetNext' , u'Item' , ), 87, (87, (), [ (16393, 10, None, "IID('{000630C3-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 60 , (3, 0, None, None) , 0 , )),
	(( u'GetPrevious' , u'Item' , ), 89, (89, (), [ (16393, 10, None, "IID('{000630C3-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 64 , (3, 0, None, None) , 0 , )),
]

win32com.client.CLSIDToClass.RegisterCLSID( "{000630C2-0000-0000-C000-000000000046}", Conflicts )
