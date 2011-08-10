# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.00
# By python version 2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
# From type library '{00062FFF-0000-0000-C000-000000000046}'
# On Mon Jun 20 13:17:27 2011
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
class _Inspector(DispatchBaseClass):
	CLSID = IID('{00063005-0000-0000-C000-000000000046}')
	coclass_clsid = IID('{00063058-0000-0000-C000-000000000046}')

	def Activate(self):
		return self._oleobj_.InvokeTypes(8467, LCID, 1, (24, 0), (),)

	def Close(self, SaveMode=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(8451, LCID, 1, (24, 0), ((3, 1),),SaveMode
			)

	def Display(self, Modal=defaultNamedOptArg):
		return self._oleobj_.InvokeTypes(8452, LCID, 1, (24, 0), ((12, 17),),Modal
			)

	def HideFormPage(self, PageName=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(8456, LCID, 1, (24, 0), ((8, 1),),PageName
			)

	def IsWordMail(self):
		return self._oleobj_.InvokeTypes(8453, LCID, 1, (11, 0), (),)

	def NewFormRegion(self):
		ret = self._oleobj_.InvokeTypes(64493, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, u'NewFormRegion', None)
		return ret

	def OpenFormRegion(self, Path=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(64511, LCID, 1, (9, 0), ((8, 1),),Path
			)
		if ret is not None:
			ret = Dispatch(ret, u'OpenFormRegion', None)
		return ret

	def SaveFormRegion(self, Page=defaultNamedNotOptArg, FileName=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64512, LCID, 1, (24, 0), ((9, 1), (8, 1)),Page
			, FileName)

	def SetControlItemProperty(self, Control=defaultNamedNotOptArg, PropertyName=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64201, LCID, 1, (24, 0), ((9, 1), (8, 1)),Control
			, PropertyName)

	def SetCurrentFormPage(self, PageName=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(8460, LCID, 1, (24, 0), ((8, 1),),PageName
			)

	def ShowFormPage(self, PageName=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(8457, LCID, 1, (24, 0), ((8, 1),),PageName
			)

	_prop_map_get_ = {
		# Method 'Application' returns object of type '_Application'
		"Application": (61440, 2, (9, 0), (), "Application", '{00063001-0000-0000-C000-000000000046}'),
		"Caption": (8465, 2, (8, 0), (), "Caption", None),
		"Class": (61450, 2, (3, 0), (), "Class", None),
		# Method 'CommandBars' returns object of type 'CommandBars'
		"CommandBars": (8448, 2, (13, 0), (), "CommandBars", '{55F88893-7708-11D1-ACEB-006008961DA5}'),
		"CurrentItem": (8450, 2, (9, 0), (), "CurrentItem", None),
		"EditorType": (8464, 2, (3, 0), (), "EditorType", None),
		"HTMLEditor": (8462, 2, (9, 0), (), "HTMLEditor", None),
		"Height": (8468, 2, (3, 0), (), "Height", None),
		"Left": (8469, 2, (3, 0), (), "Left", None),
		"ModifiedFormPages": (8454, 2, (9, 0), (), "ModifiedFormPages", None),
		"Parent": (61441, 2, (9, 0), (), "Parent", None),
		# Method 'Session' returns object of type '_NameSpace'
		"Session": (61451, 2, (9, 0), (), "Session", '{00063002-0000-0000-C000-000000000046}'),
		"Top": (8470, 2, (3, 0), (), "Top", None),
		"Width": (8471, 2, (3, 0), (), "Width", None),
		"WindowState": (8466, 2, (3, 0), (), "WindowState", None),
		"WordEditor": (8463, 2, (9, 0), (), "WordEditor", None),
	}
	_prop_map_put_ = {
		"Height": ((8468, LCID, 4, 0),()),
		"Left": ((8469, LCID, 4, 0),()),
		"Top": ((8470, LCID, 4, 0),()),
		"Width": ((8471, LCID, 4, 0),()),
		"WindowState": ((8466, LCID, 4, 0),()),
	}

win32com.client.CLSIDToClass.RegisterCLSID( "{00063005-0000-0000-C000-000000000046}", _Inspector )
# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.00
# By python version 2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
# From type library '{00062FFF-0000-0000-C000-000000000046}'
# On Mon Jun 20 13:17:27 2011
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

_Inspector_vtables_dispatch_ = 1
_Inspector_vtables_ = [
	(( u'Application' , u'Application' , ), 61440, (61440, (), [ (16393, 10, None, "IID('{00063001-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 28 , (3, 0, None, None) , 0 , )),
	(( u'Class' , u'Class' , ), 61450, (61450, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 32 , (3, 0, None, None) , 0 , )),
	(( u'Session' , u'Session' , ), 61451, (61451, (), [ (16393, 10, None, "IID('{00063002-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 36 , (3, 0, None, None) , 0 , )),
	(( u'Parent' , u'Parent' , ), 61441, (61441, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 40 , (3, 0, None, None) , 0 , )),
	(( u'CommandBars' , u'CommandBars' , ), 8448, (8448, (), [ (16397, 10, None, "IID('{55F88893-7708-11D1-ACEB-006008961DA5}')") , ], 1 , 2 , 4 , 0 , 44 , (3, 0, None, None) , 0 , )),
	(( u'CurrentItem' , u'CurrentItem' , ), 8450, (8450, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 48 , (3, 0, None, None) , 0 , )),
	(( u'EditorType' , u'EditorType' , ), 8464, (8464, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 52 , (3, 0, None, None) , 0 , )),
	(( u'ModifiedFormPages' , u'ModifiedFormPages' , ), 8454, (8454, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 56 , (3, 0, None, None) , 0 , )),
	(( u'Close' , u'SaveMode' , ), 8451, (8451, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 60 , (3, 0, None, None) , 0 , )),
	(( u'Display' , u'Modal' , ), 8452, (8452, (), [ (12, 17, None, None) , ], 1 , 1 , 4 , 1 , 64 , (3, 0, None, None) , 0 , )),
	(( u'HideFormPage' , u'PageName' , ), 8456, (8456, (), [ (8, 1, None, None) , ], 1 , 1 , 4 , 0 , 68 , (3, 0, None, None) , 0 , )),
	(( u'IsWordMail' , u'IsWordMail' , ), 8453, (8453, (), [ (16395, 10, None, None) , ], 1 , 1 , 4 , 0 , 72 , (3, 0, None, None) , 0 , )),
	(( u'SetCurrentFormPage' , u'PageName' , ), 8460, (8460, (), [ (8, 1, None, None) , ], 1 , 1 , 4 , 0 , 76 , (3, 0, None, None) , 0 , )),
	(( u'ShowFormPage' , u'PageName' , ), 8457, (8457, (), [ (8, 1, None, None) , ], 1 , 1 , 4 , 0 , 80 , (3, 0, None, None) , 0 , )),
	(( u'HTMLEditor' , u'HTMLEditor' , ), 8462, (8462, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 84 , (3, 0, None, None) , 64 , )),
	(( u'WordEditor' , u'WordEditor' , ), 8463, (8463, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 88 , (3, 0, None, None) , 0 , )),
	(( u'Caption' , u'Caption' , ), 8465, (8465, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 92 , (3, 0, None, None) , 0 , )),
	(( u'Height' , u'Height' , ), 8468, (8468, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 96 , (3, 0, None, None) , 0 , )),
	(( u'Height' , u'Height' , ), 8468, (8468, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 100 , (3, 0, None, None) , 0 , )),
	(( u'Left' , u'Left' , ), 8469, (8469, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 104 , (3, 0, None, None) , 0 , )),
	(( u'Left' , u'Left' , ), 8469, (8469, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 108 , (3, 0, None, None) , 0 , )),
	(( u'Top' , u'Top' , ), 8470, (8470, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 112 , (3, 0, None, None) , 0 , )),
	(( u'Top' , u'Top' , ), 8470, (8470, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 116 , (3, 0, None, None) , 0 , )),
	(( u'Width' , u'Width' , ), 8471, (8471, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 120 , (3, 0, None, None) , 0 , )),
	(( u'Width' , u'Width' , ), 8471, (8471, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 124 , (3, 0, None, None) , 0 , )),
	(( u'WindowState' , u'WindowState' , ), 8466, (8466, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 128 , (3, 0, None, None) , 0 , )),
	(( u'WindowState' , u'WindowState' , ), 8466, (8466, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 132 , (3, 0, None, None) , 0 , )),
	(( u'Activate' , ), 8467, (8467, (), [ ], 1 , 1 , 4 , 0 , 136 , (3, 0, None, None) , 0 , )),
	(( u'SetControlItemProperty' , u'Control' , u'PropertyName' , ), 64201, (64201, (), [ (9, 1, None, None) , 
			(8, 1, None, None) , ], 1 , 1 , 4 , 0 , 140 , (3, 0, None, None) , 0 , )),
	(( u'NewFormRegion' , u'Form' , ), 64493, (64493, (), [ (16393, 10, None, None) , ], 1 , 1 , 4 , 0 , 144 , (3, 0, None, None) , 0 , )),
	(( u'OpenFormRegion' , u'Path' , u'Form' , ), 64511, (64511, (), [ (8, 1, None, None) , 
			(16393, 10, None, None) , ], 1 , 1 , 4 , 0 , 148 , (3, 0, None, None) , 0 , )),
	(( u'SaveFormRegion' , u'Page' , u'FileName' , ), 64512, (64512, (), [ (9, 1, None, None) , 
			(8, 1, None, None) , ], 1 , 1 , 4 , 0 , 152 , (3, 0, None, None) , 0 , )),
]

win32com.client.CLSIDToClass.RegisterCLSID( "{00063005-0000-0000-C000-000000000046}", _Inspector )
