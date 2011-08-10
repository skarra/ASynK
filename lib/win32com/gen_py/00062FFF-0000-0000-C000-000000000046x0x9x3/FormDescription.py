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
class FormDescription(DispatchBaseClass):
	CLSID = IID('{00063046-0000-0000-C000-000000000046}')
	coclass_clsid = None

	def PublishForm(self, Registry=defaultNamedNotOptArg, Folder=defaultNamedOptArg):
		return self._oleobj_.InvokeTypes(107, LCID, 1, (24, 0), ((3, 1), (12, 17)),Registry
			, Folder)

	_prop_map_get_ = {
		# Method 'Application' returns object of type '_Application'
		"Application": (61440, 2, (9, 0), (), "Application", '{00063001-0000-0000-C000-000000000046}'),
		"Category": (13060, 2, (8, 0), (), "Category", None),
		"CategorySub": (13061, 2, (8, 0), (), "CategorySub", None),
		"Class": (61450, 2, (3, 0), (), "Class", None),
		"Comment": (12292, 2, (8, 0), (), "Comment", None),
		"ContactName": (13059, 2, (8, 0), (), "ContactName", None),
		"DisplayName": (12289, 2, (8, 0), (), "DisplayName", None),
		"Hidden": (13063, 2, (11, 0), (), "Hidden", None),
		"Icon": (4093, 2, (8, 0), (), "Icon", None),
		"Locked": (102, 2, (11, 0), (), "Locked", None),
		"MessageClass": (26, 2, (8, 0), (), "MessageClass", None),
		"MiniIcon": (4092, 2, (8, 0), (), "MiniIcon", None),
		"Name": (61469, 2, (8, 0), (), "Name", None),
		"Number": (104, 2, (8, 0), (), "Number", None),
		"OneOff": (101, 2, (11, 0), (), "OneOff", None),
		"Parent": (61441, 2, (9, 0), (), "Parent", None),
		"Password": (103, 2, (8, 0), (), "Password", None),
		"ScriptText": (109, 2, (8, 0), (), "ScriptText", None),
		# Method 'Session' returns object of type '_NameSpace'
		"Session": (61451, 2, (9, 0), (), "Session", '{00063002-0000-0000-C000-000000000046}'),
		"Template": (106, 2, (8, 0), (), "Template", None),
		"UseWordMail": (105, 2, (11, 0), (), "UseWordMail", None),
		"Version": (13057, 2, (8, 0), (), "Version", None),
	}
	_prop_map_put_ = {
		"Category": ((13060, LCID, 4, 0),()),
		"CategorySub": ((13061, LCID, 4, 0),()),
		"Comment": ((12292, LCID, 4, 0),()),
		"ContactName": ((13059, LCID, 4, 0),()),
		"DisplayName": ((12289, LCID, 4, 0),()),
		"Hidden": ((13063, LCID, 4, 0),()),
		"Icon": ((4093, LCID, 4, 0),()),
		"Locked": ((102, LCID, 4, 0),()),
		"MiniIcon": ((4092, LCID, 4, 0),()),
		"Name": ((61469, LCID, 4, 0),()),
		"Number": ((104, LCID, 4, 0),()),
		"OneOff": ((101, LCID, 4, 0),()),
		"Password": ((103, LCID, 4, 0),()),
		"Template": ((106, LCID, 4, 0),()),
		"UseWordMail": ((105, LCID, 4, 0),()),
		"Version": ((13057, LCID, 4, 0),()),
	}

win32com.client.CLSIDToClass.RegisterCLSID( "{00063046-0000-0000-C000-000000000046}", FormDescription )
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

FormDescription_vtables_dispatch_ = 1
FormDescription_vtables_ = [
	(( u'Application' , u'Application' , ), 61440, (61440, (), [ (16393, 10, None, "IID('{00063001-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 28 , (3, 0, None, None) , 0 , )),
	(( u'Class' , u'Class' , ), 61450, (61450, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 32 , (3, 0, None, None) , 0 , )),
	(( u'Session' , u'Session' , ), 61451, (61451, (), [ (16393, 10, None, "IID('{00063002-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 36 , (3, 0, None, None) , 0 , )),
	(( u'Parent' , u'Parent' , ), 61441, (61441, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 40 , (3, 0, None, None) , 0 , )),
	(( u'Category' , u'Category' , ), 13060, (13060, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 44 , (3, 0, None, None) , 0 , )),
	(( u'Category' , u'Category' , ), 13060, (13060, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 48 , (3, 0, None, None) , 0 , )),
	(( u'CategorySub' , u'CategorySub' , ), 13061, (13061, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 52 , (3, 0, None, None) , 0 , )),
	(( u'CategorySub' , u'CategorySub' , ), 13061, (13061, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 56 , (3, 0, None, None) , 0 , )),
	(( u'Comment' , u'Comment' , ), 12292, (12292, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 60 , (3, 0, None, None) , 0 , )),
	(( u'Comment' , u'Comment' , ), 12292, (12292, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 64 , (3, 0, None, None) , 0 , )),
	(( u'ContactName' , u'ContactName' , ), 13059, (13059, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 68 , (3, 0, None, None) , 0 , )),
	(( u'ContactName' , u'ContactName' , ), 13059, (13059, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 72 , (3, 0, None, None) , 0 , )),
	(( u'DisplayName' , u'DisplayName' , ), 12289, (12289, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 76 , (3, 0, None, None) , 0 , )),
	(( u'DisplayName' , u'DisplayName' , ), 12289, (12289, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 80 , (3, 0, None, None) , 0 , )),
	(( u'Hidden' , u'Hidden' , ), 13063, (13063, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 84 , (3, 0, None, None) , 0 , )),
	(( u'Hidden' , u'Hidden' , ), 13063, (13063, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 88 , (3, 0, None, None) , 0 , )),
	(( u'Icon' , u'Icon' , ), 4093, (4093, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 92 , (3, 0, None, None) , 0 , )),
	(( u'Icon' , u'Icon' , ), 4093, (4093, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 96 , (3, 0, None, None) , 0 , )),
	(( u'Locked' , u'Locked' , ), 102, (102, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 100 , (3, 0, None, None) , 0 , )),
	(( u'Locked' , u'Locked' , ), 102, (102, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 104 , (3, 0, None, None) , 0 , )),
	(( u'MessageClass' , u'MessageClass' , ), 26, (26, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 108 , (3, 0, None, None) , 0 , )),
	(( u'MiniIcon' , u'MiniIcon' , ), 4092, (4092, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 112 , (3, 0, None, None) , 0 , )),
	(( u'MiniIcon' , u'MiniIcon' , ), 4092, (4092, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 116 , (3, 0, None, None) , 0 , )),
	(( u'Name' , u'Name' , ), 61469, (61469, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 120 , (3, 0, None, None) , 0 , )),
	(( u'Name' , u'Name' , ), 61469, (61469, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 124 , (3, 0, None, None) , 0 , )),
	(( u'Number' , u'Number' , ), 104, (104, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 128 , (3, 0, None, None) , 0 , )),
	(( u'Number' , u'Number' , ), 104, (104, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 132 , (3, 0, None, None) , 0 , )),
	(( u'OneOff' , u'OneOff' , ), 101, (101, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 136 , (3, 0, None, None) , 0 , )),
	(( u'OneOff' , u'OneOff' , ), 101, (101, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 140 , (3, 0, None, None) , 0 , )),
	(( u'Password' , u'Password' , ), 103, (103, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 144 , (3, 0, None, None) , 64 , )),
	(( u'Password' , u'Password' , ), 103, (103, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 148 , (3, 0, None, None) , 64 , )),
	(( u'ScriptText' , u'ScriptText' , ), 109, (109, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 152 , (3, 0, None, None) , 0 , )),
	(( u'Template' , u'Template' , ), 106, (106, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 156 , (3, 0, None, None) , 0 , )),
	(( u'Template' , u'Template' , ), 106, (106, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 160 , (3, 0, None, None) , 0 , )),
	(( u'UseWordMail' , u'UseWordMail' , ), 105, (105, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 164 , (3, 0, None, None) , 0 , )),
	(( u'UseWordMail' , u'UseWordMail' , ), 105, (105, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 168 , (3, 0, None, None) , 0 , )),
	(( u'Version' , u'Version' , ), 13057, (13057, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 172 , (3, 0, None, None) , 0 , )),
	(( u'Version' , u'Version' , ), 13057, (13057, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 176 , (3, 0, None, None) , 0 , )),
	(( u'PublishForm' , u'Registry' , u'Folder' , ), 107, (107, (), [ (3, 1, None, None) , 
			(12, 17, None, None) , ], 1 , 1 , 4 , 1 , 180 , (3, 0, None, None) , 0 , )),
]

win32com.client.CLSIDToClass.RegisterCLSID( "{00063046-0000-0000-C000-000000000046}", FormDescription )
