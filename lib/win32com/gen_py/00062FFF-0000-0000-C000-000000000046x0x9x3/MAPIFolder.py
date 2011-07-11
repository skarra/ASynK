# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.00
# By python version 2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
# From type library '{00062FFF-0000-0000-C000-000000000046}'
# On Wed May 04 17:52:41 2011
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
class MAPIFolder(DispatchBaseClass):
	CLSID = IID('{00063006-0000-0000-C000-000000000046}')
	coclass_clsid = IID('{000610F7-0000-0000-C000-000000000046}')

	def AddToFavorites(self, fNoUI=defaultNamedOptArg, Name=defaultNamedOptArg):
		return self._oleobj_.InvokeTypes(64097, LCID, 1, (24, 0), ((12, 17), (12, 17)),fNoUI
			, Name)

	def AddToPFFavorites(self):
		return self._oleobj_.InvokeTypes(12565, LCID, 1, (24, 0), (),)

	# Result is of type MAPIFolder
	def CopyTo(self, DestinationFolder=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(61490, LCID, 1, (9, 0), ((9, 1),),DestinationFolder
			)
		if ret is not None:
			ret = Dispatch(ret, u'CopyTo', '{00063006-0000-0000-C000-000000000046}')
		return ret

	def Delete(self):
		return self._oleobj_.InvokeTypes(61509, LCID, 1, (24, 0), (),)

	def Display(self):
		return self._oleobj_.InvokeTypes(12548, LCID, 1, (24, 0), (),)

	# Result is of type CalendarSharing
	def GetCalendarExporter(self):
		ret = self._oleobj_.InvokeTypes(64418, LCID, 1, (13, 0), (),)
		if ret is not None:
			# See if this IUnknown is really an IDispatch
			try:
				ret = ret.QueryInterface(pythoncom.IID_IDispatch)
			except pythoncom.error:
				return ret
			ret = Dispatch(ret, u'GetCalendarExporter', '{000610E2-0000-0000-C000-000000000046}')
		return ret

	# Result is of type _Explorer
	def GetExplorer(self, DisplayMode=defaultNamedOptArg):
		ret = self._oleobj_.InvokeTypes(12545, LCID, 1, (9, 0), ((12, 17),),DisplayMode
			)
		if ret is not None:
			ret = Dispatch(ret, u'GetExplorer', '{00063003-0000-0000-C000-000000000046}')
		return ret

	# Result is of type _StorageItem
	def GetStorage(self, StorageIdentifier=defaultNamedNotOptArg, StorageIdentifierType=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(64264, LCID, 1, (9, 0), ((8, 1), (3, 1)),StorageIdentifier
			, StorageIdentifierType)
		if ret is not None:
			ret = Dispatch(ret, u'GetStorage', '{000630CB-0000-0000-C000-000000000046}')
		return ret

	# Result is of type Table
	def GetTable(self, Filter=defaultNamedOptArg, TableContents=defaultNamedOptArg):
		ret = self._oleobj_.InvokeTypes(64285, LCID, 1, (13, 0), ((12, 17), (12, 17)),Filter
			, TableContents)
		if ret is not None:
			# See if this IUnknown is really an IDispatch
			try:
				ret = ret.QueryInterface(pythoncom.IID_IDispatch)
			except pythoncom.error:
				return ret
			ret = Dispatch(ret, u'GetTable', '{000610D2-0000-0000-C000-000000000046}')
		return ret

	def MoveTo(self, DestinationFolder=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(61492, LCID, 1, (24, 0), ((9, 1),),DestinationFolder
			)

	_prop_map_get_ = {
		"AddressBookName": (64110, 2, (8, 0), (), "AddressBookName", None),
		# Method 'Application' returns object of type '_Application'
		"Application": (61440, 2, (9, 0), (), "Application", '{00063001-0000-0000-C000-000000000046}'),
		"Class": (61450, 2, (3, 0), (), "Class", None),
		# Method 'CurrentView' returns object of type 'View'
		"CurrentView": (8704, 2, (9, 0), (), "CurrentView", '{00063095-0000-0000-C000-000000000046}'),
		"CustomViewsOnly": (64070, 2, (11, 0), (), "CustomViewsOnly", None),
		"DefaultItemType": (12550, 2, (3, 0), (), "DefaultItemType", None),
		"DefaultMessageClass": (12551, 2, (8, 0), (), "DefaultMessageClass", None),
		"Description": (12292, 2, (8, 0), (), "Description", None),
		"EntryID": (61470, 2, (8, 0), (), "EntryID", None),
		"FolderPath": (64120, 2, (8, 0), (), "FolderPath", None),
		# Method 'Folders' returns object of type '_Folders'
		"Folders": (8451, 2, (9, 0), (), "Folders", '{00063040-0000-0000-C000-000000000046}'),
		"FullFolderPath": (64145, 2, (8, 0), (), "FullFolderPath", None),
		"InAppFolderSyncObject": (64075, 2, (11, 0), (), "InAppFolderSyncObject", None),
		"IsSharePointFolder": (64182, 2, (11, 0), (), "IsSharePointFolder", None),
		# Method 'Items' returns object of type '_Items'
		"Items": (12544, 2, (9, 0), (), "Items", '{00063041-0000-0000-C000-000000000046}'),
		"MAPIOBJECT": (61696, 2, (13, 0), (), "MAPIOBJECT", None),
		"Name": (12289, 2, (8, 0), (), "Name", None),
		"Parent": (61441, 2, (9, 0), (), "Parent", None),
		# Method 'PropertyAccessor' returns object of type 'PropertyAccessor'
		"PropertyAccessor": (64253, 2, (13, 0), (), "PropertyAccessor", '{0006102D-0000-0000-C000-000000000046}'),
		# Method 'Session' returns object of type '_NameSpace'
		"Session": (61451, 2, (9, 0), (), "Session", '{00063002-0000-0000-C000-000000000046}'),
		"ShowAsOutlookAB": (64111, 2, (11, 0), (), "ShowAsOutlookAB", None),
		"ShowItemCount": (64194, 2, (3, 0), (), "ShowItemCount", None),
		# Method 'Store' returns object of type 'Store'
		"Store": (64217, 2, (13, 0), (), "Store", '{000610C7-0000-0000-C000-000000000046}'),
		"StoreID": (12552, 2, (8, 0), (), "StoreID", None),
		"UnReadItemCount": (13827, 2, (3, 0), (), "UnReadItemCount", None),
		# Method 'UserDefinedProperties' returns object of type 'UserDefinedProperties'
		"UserDefinedProperties": (63510, 2, (13, 0), (), "UserDefinedProperties", '{00061047-0000-0000-C000-000000000046}'),
		"UserPermissions": (12561, 2, (9, 0), (), "UserPermissions", None),
		# Method 'Views' returns object of type '_Views'
		"Views": (12553, 2, (9, 0), (), "Views", '{0006308D-0000-0000-C000-000000000046}'),
		"WebViewAllowNavigation": (12564, 2, (11, 0), (), "WebViewAllowNavigation", None),
		"WebViewOn": (12562, 2, (11, 0), (), "WebViewOn", None),
		"WebViewURL": (12563, 2, (8, 0), (), "WebViewURL", None),
	}
	_prop_map_put_ = {
		"AddressBookName": ((64110, LCID, 4, 0),()),
		"CustomViewsOnly": ((64070, LCID, 4, 0),()),
		"Description": ((12292, LCID, 4, 0),()),
		"InAppFolderSyncObject": ((64075, LCID, 4, 0),()),
		"Name": ((12289, LCID, 4, 0),()),
		"ShowAsOutlookAB": ((64111, LCID, 4, 0),()),
		"ShowItemCount": ((64194, LCID, 4, 0),()),
		"WebViewAllowNavigation": ((12564, LCID, 4, 0),()),
		"WebViewOn": ((12562, LCID, 4, 0),()),
		"WebViewURL": ((12563, LCID, 4, 0),()),
	}

win32com.client.CLSIDToClass.RegisterCLSID( "{00063006-0000-0000-C000-000000000046}", MAPIFolder )
# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.00
# By python version 2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
# From type library '{00062FFF-0000-0000-C000-000000000046}'
# On Wed May 04 17:52:41 2011
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

MAPIFolder_vtables_dispatch_ = 1
MAPIFolder_vtables_ = [
	(( u'Application' , u'Application' , ), 61440, (61440, (), [ (16393, 10, None, "IID('{00063001-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 28 , (3, 0, None, None) , 0 , )),
	(( u'Class' , u'Class' , ), 61450, (61450, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 32 , (3, 0, None, None) , 0 , )),
	(( u'Session' , u'Session' , ), 61451, (61451, (), [ (16393, 10, None, "IID('{00063002-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 36 , (3, 0, None, None) , 0 , )),
	(( u'Parent' , u'Parent' , ), 61441, (61441, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 40 , (3, 0, None, None) , 0 , )),
	(( u'DefaultItemType' , u'DefaultItemType' , ), 12550, (12550, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 44 , (3, 0, None, None) , 0 , )),
	(( u'DefaultMessageClass' , u'DefaultMessageClass' , ), 12551, (12551, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 48 , (3, 0, None, None) , 0 , )),
	(( u'Description' , u'Description' , ), 12292, (12292, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 52 , (3, 0, None, None) , 0 , )),
	(( u'Description' , u'Description' , ), 12292, (12292, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 56 , (3, 0, None, None) , 0 , )),
	(( u'EntryID' , u'EntryID' , ), 61470, (61470, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 60 , (3, 0, None, None) , 0 , )),
	(( u'Folders' , u'Folders' , ), 8451, (8451, (), [ (16393, 10, None, "IID('{00063040-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 64 , (3, 0, None, None) , 0 , )),
	(( u'Items' , u'Items' , ), 12544, (12544, (), [ (16393, 10, None, "IID('{00063041-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 68 , (3, 0, None, None) , 0 , )),
	(( u'Name' , u'Name' , ), 12289, (12289, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 72 , (3, 0, None, None) , 0 , )),
	(( u'Name' , u'Name' , ), 12289, (12289, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 76 , (3, 0, None, None) , 0 , )),
	(( u'StoreID' , u'StoreID' , ), 12552, (12552, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 80 , (3, 0, None, None) , 0 , )),
	(( u'UnReadItemCount' , u'UnReadItemCount' , ), 13827, (13827, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 84 , (3, 0, None, None) , 0 , )),
	(( u'CopyTo' , u'DestinationFolder' , u'Folder' , ), 61490, (61490, (), [ (9, 1, None, "IID('{00063006-0000-0000-C000-000000000046}')") , 
			(16393, 10, None, "IID('{00063006-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 88 , (3, 0, None, None) , 0 , )),
	(( u'Delete' , ), 61509, (61509, (), [ ], 1 , 1 , 4 , 0 , 92 , (3, 0, None, None) , 0 , )),
	(( u'Display' , ), 12548, (12548, (), [ ], 1 , 1 , 4 , 0 , 96 , (3, 0, None, None) , 0 , )),
	(( u'GetExplorer' , u'DisplayMode' , u'Explorer' , ), 12545, (12545, (), [ (12, 17, None, None) , 
			(16393, 10, None, "IID('{00063003-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 1 , 100 , (3, 0, None, None) , 0 , )),
	(( u'MoveTo' , u'DestinationFolder' , ), 61492, (61492, (), [ (9, 1, None, "IID('{00063006-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 104 , (3, 0, None, None) , 0 , )),
	(( u'UserPermissions' , u'UserPermissions' , ), 12561, (12561, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 108 , (3, 0, None, None) , 64 , )),
	(( u'WebViewOn' , u'WebViewOn' , ), 12562, (12562, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 112 , (3, 0, None, None) , 0 , )),
	(( u'WebViewOn' , u'WebViewOn' , ), 12562, (12562, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 116 , (3, 0, None, None) , 0 , )),
	(( u'WebViewURL' , u'WebViewURL' , ), 12563, (12563, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 120 , (3, 0, None, None) , 0 , )),
	(( u'WebViewURL' , u'WebViewURL' , ), 12563, (12563, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 124 , (3, 0, None, None) , 0 , )),
	(( u'WebViewAllowNavigation' , u'WebViewAllowNavigation' , ), 12564, (12564, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 128 , (3, 0, None, None) , 64 , )),
	(( u'WebViewAllowNavigation' , u'WebViewAllowNavigation' , ), 12564, (12564, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 132 , (3, 0, None, None) , 64 , )),
	(( u'AddToPFFavorites' , ), 12565, (12565, (), [ ], 1 , 1 , 4 , 0 , 136 , (3, 0, None, None) , 0 , )),
	(( u'AddressBookName' , u'AddressBookName' , ), 64110, (64110, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 140 , (3, 0, None, None) , 0 , )),
	(( u'AddressBookName' , u'AddressBookName' , ), 64110, (64110, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 144 , (3, 0, None, None) , 0 , )),
	(( u'ShowAsOutlookAB' , u'ShowAsOutlookAB' , ), 64111, (64111, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 148 , (3, 0, None, None) , 0 , )),
	(( u'ShowAsOutlookAB' , u'ShowAsOutlookAB' , ), 64111, (64111, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 152 , (3, 0, None, None) , 0 , )),
	(( u'FolderPath' , u'FolderPath' , ), 64120, (64120, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 156 , (3, 0, None, None) , 0 , )),
	(( u'AddToFavorites' , u'fNoUI' , u'Name' , ), 64097, (64097, (), [ (12, 17, None, None) , 
			(12, 17, None, None) , ], 1 , 1 , 4 , 2 , 160 , (3, 0, None, None) , 64 , )),
	(( u'InAppFolderSyncObject' , u'InAppFolderSyncObject' , ), 64075, (64075, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 164 , (3, 0, None, None) , 0 , )),
	(( u'InAppFolderSyncObject' , u'InAppFolderSyncObject' , ), 64075, (64075, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 168 , (3, 0, None, None) , 0 , )),
	(( u'CurrentView' , u'CurrentView' , ), 8704, (8704, (), [ (16393, 10, None, "IID('{00063095-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 172 , (3, 0, None, None) , 0 , )),
	(( u'CustomViewsOnly' , u'CustomViewsOnly' , ), 64070, (64070, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 176 , (3, 0, None, None) , 0 , )),
	(( u'CustomViewsOnly' , u'CustomViewsOnly' , ), 64070, (64070, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 180 , (3, 0, None, None) , 0 , )),
	(( u'Views' , u'Views' , ), 12553, (12553, (), [ (16393, 10, None, "IID('{0006308D-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 184 , (3, 0, None, None) , 0 , )),
	(( u'MAPIOBJECT' , u'MAPIOBJECT' , ), 61696, (61696, (), [ (16397, 10, None, None) , ], 1 , 2 , 4 , 0 , 188 , (3, 0, None, None) , 64 , )),
	(( u'FullFolderPath' , u'FullFolderPath' , ), 64145, (64145, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 192 , (3, 0, None, None) , 64 , )),
	(( u'IsSharePointFolder' , u'IsSharePointFolder' , ), 64182, (64182, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 196 , (3, 0, None, None) , 0 , )),
	(( u'ShowItemCount' , u'ShowItemCount' , ), 64194, (64194, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 200 , (3, 0, None, None) , 0 , )),
	(( u'ShowItemCount' , u'ShowItemCount' , ), 64194, (64194, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 204 , (3, 0, None, None) , 0 , )),
	(( u'Store' , u'Store' , ), 64217, (64217, (), [ (16397, 10, None, "IID('{000610C7-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 208 , (3, 0, None, None) , 0 , )),
	(( u'GetStorage' , u'StorageIdentifier' , u'StorageIdentifierType' , u'StorageItem' , ), 64264, (64264, (), [ 
			(8, 1, None, None) , (3, 1, None, None) , (16393, 10, None, "IID('{000630CB-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 212 , (3, 0, None, None) , 0 , )),
	(( u'GetTable' , u'Filter' , u'TableContents' , u'Table' , ), 64285, (64285, (), [ 
			(12, 17, None, None) , (12, 17, None, None) , (16397, 10, None, "IID('{000610D2-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 2 , 216 , (3, 0, None, None) , 0 , )),
	(( u'PropertyAccessor' , u'PropertyAccessor' , ), 64253, (64253, (), [ (16397, 10, None, "IID('{0006102D-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 220 , (3, 0, None, None) , 0 , )),
	(( u'GetCalendarExporter' , u'Exporter' , ), 64418, (64418, (), [ (16397, 10, None, "IID('{000610E2-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 224 , (3, 0, None, None) , 0 , )),
	(( u'UserDefinedProperties' , u'UserDefinedProperties' , ), 63510, (63510, (), [ (16397, 10, None, "IID('{00061047-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 228 , (3, 0, None, None) , 0 , )),
]

win32com.client.CLSIDToClass.RegisterCLSID( "{00063006-0000-0000-C000-000000000046}", MAPIFolder )
