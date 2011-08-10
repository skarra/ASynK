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
class _NameSpace(DispatchBaseClass):
	CLSID = IID('{00063002-0000-0000-C000-000000000046}')
	coclass_clsid = IID('{0006308B-0000-0000-C000-000000000046}')

	def AddStore(self, Store=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(8473, LCID, 1, (24, 0), ((12, 1),),Store
			)

	def AddStoreEx(self, Store=defaultNamedNotOptArg, Type=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64197, LCID, 1, (24, 0), ((12, 1), (3, 1)),Store
			, Type)

	def CompareEntryIDs(self, FirstEntryID=defaultNamedNotOptArg, SecondEntryID=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64508, LCID, 1, (11, 0), ((8, 1), (8, 1)),FirstEntryID
			, SecondEntryID)

	# Result is of type Recipient
	def CreateRecipient(self, RecipientName=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(8458, LCID, 1, (9, 0), ((8, 1),),RecipientName
			)
		if ret is not None:
			ret = Dispatch(ret, u'CreateRecipient', '{00063045-0000-0000-C000-000000000046}')
		return ret

	# Result is of type SharingItem
	def CreateSharingItem(self, Context=defaultNamedNotOptArg, Provider=defaultNamedOptArg):
		ret = self._oleobj_.InvokeTypes(64484, LCID, 1, (13, 0), ((12, 1), (12, 17)),Context
			, Provider)
		if ret is not None:
			# See if this IUnknown is really an IDispatch
			try:
				ret = ret.QueryInterface(pythoncom.IID_IDispatch)
			except pythoncom.error:
				return ret
			ret = Dispatch(ret, u'CreateSharingItem', '{00061067-0000-0000-C000-000000000046}')
		return ret

	def Dial(self, ContactItem=defaultNamedOptArg):
		return self._oleobj_.InvokeTypes(64013, LCID, 1, (24, 0), ((12, 17),),ContactItem
			)

	# Result is of type AddressEntry
	def GetAddressEntryFromID(self, ID=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(64260, LCID, 1, (9, 0), ((8, 1),),ID
			)
		if ret is not None:
			ret = Dispatch(ret, u'GetAddressEntryFromID', '{0006304B-0000-0000-C000-000000000046}')
		return ret

	# Result is of type MAPIFolder
	def GetDefaultFolder(self, FolderType=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(8459, LCID, 1, (9, 0), ((3, 1),),FolderType
			)
		if ret is not None:
			ret = Dispatch(ret, u'GetDefaultFolder', '{00063006-0000-0000-C000-000000000046}')
		return ret

	# Result is of type MAPIFolder
	def GetFolderFromID(self, EntryIDFolder=defaultNamedNotOptArg, EntryIDStore=defaultNamedOptArg):
		ret = self._oleobj_.InvokeTypes(8456, LCID, 1, (9, 0), ((8, 1), (12, 17)),EntryIDFolder
			, EntryIDStore)
		if ret is not None:
			ret = Dispatch(ret, u'GetFolderFromID', '{00063006-0000-0000-C000-000000000046}')
		return ret

	# Result is of type AddressList
	def GetGlobalAddressList(self):
		ret = self._oleobj_.InvokeTypes(64261, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, u'GetGlobalAddressList', '{00063049-0000-0000-C000-000000000046}')
		return ret

	def GetItemFromID(self, EntryIDItem=defaultNamedNotOptArg, EntryIDStore=defaultNamedOptArg):
		ret = self._oleobj_.InvokeTypes(8457, LCID, 1, (9, 0), ((8, 1), (12, 17)),EntryIDItem
			, EntryIDStore)
		if ret is not None:
			ret = Dispatch(ret, u'GetItemFromID', None)
		return ret

	# Result is of type Recipient
	def GetRecipientFromID(self, EntryID=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(8455, LCID, 1, (9, 0), ((8, 1),),EntryID
			)
		if ret is not None:
			ret = Dispatch(ret, u'GetRecipientFromID', '{00063045-0000-0000-C000-000000000046}')
		return ret

	# Result is of type SelectNamesDialog
	def GetSelectNamesDialog(self):
		ret = self._oleobj_.InvokeTypes(64225, LCID, 1, (13, 0), (),)
		if ret is not None:
			# See if this IUnknown is really an IDispatch
			try:
				ret = ret.QueryInterface(pythoncom.IID_IDispatch)
			except pythoncom.error:
				return ret
			ret = Dispatch(ret, u'GetSelectNamesDialog', '{000610C8-0000-0000-C000-000000000046}')
		return ret

	# Result is of type MAPIFolder
	def GetSharedDefaultFolder(self, Recipient=defaultNamedNotOptArg, FolderType=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(8460, LCID, 1, (9, 0), ((9, 1), (3, 1)),Recipient
			, FolderType)
		if ret is not None:
			ret = Dispatch(ret, u'GetSharedDefaultFolder', '{00063006-0000-0000-C000-000000000046}')
		return ret

	# Result is of type Store
	def GetStoreFromID(self, ID=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(64262, LCID, 1, (13, 0), ((8, 1),),ID
			)
		if ret is not None:
			# See if this IUnknown is really an IDispatch
			try:
				ret = ret.QueryInterface(pythoncom.IID_IDispatch)
			except pythoncom.error:
				return ret
			ret = Dispatch(ret, u'GetStoreFromID', '{000610C7-0000-0000-C000-000000000046}')
		return ret

	def Logoff(self):
		return self._oleobj_.InvokeTypes(8454, LCID, 1, (24, 0), (),)

	def Logon(self, Profile=defaultNamedOptArg, Password=defaultNamedOptArg, ShowDialog=defaultNamedOptArg, NewSession=defaultNamedOptArg):
		return self._oleobj_.InvokeTypes(8453, LCID, 1, (24, 0), ((12, 17), (12, 17), (12, 17), (12, 17)),Profile
			, Password, ShowDialog, NewSession)

	# Result is of type MAPIFolder
	def OpenSharedFolder(self, Path=defaultNamedNotOptArg, Name=defaultNamedOptArg, DownloadAttachments=defaultNamedOptArg, UseTTL=defaultNamedOptArg):
		ret = self._oleobj_.InvokeTypes(64502, LCID, 1, (9, 0), ((8, 1), (12, 17), (12, 17), (12, 17)),Path
			, Name, DownloadAttachments, UseTTL)
		if ret is not None:
			ret = Dispatch(ret, u'OpenSharedFolder', '{00063006-0000-0000-C000-000000000046}')
		return ret

	def OpenSharedItem(self, Path=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(64503, LCID, 1, (9, 0), ((8, 1),),Path
			)
		if ret is not None:
			ret = Dispatch(ret, u'OpenSharedItem', None)
		return ret

	# Result is of type MAPIFolder
	def PickFolder(self):
		ret = self._oleobj_.InvokeTypes(8462, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, u'PickFolder', '{00063006-0000-0000-C000-000000000046}')
		return ret

	def RefreshRemoteHeaders(self):
		return self._oleobj_.InvokeTypes(8471, LCID, 1, (24, 0), (),)

	def RemoveStore(self, Folder=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(8474, LCID, 1, (24, 0), ((9, 1),),Folder
			)

	def SendAndReceive(self, showProgressDialog=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64215, LCID, 1, (24, 0), ((11, 1),),showProgressDialog
			)

	_prop_map_get_ = {
		# Method 'Accounts' returns object of type 'Accounts'
		"Accounts": (64208, 2, (13, 0), (), "Accounts", '{000610C4-0000-0000-C000-000000000046}'),
		# Method 'AddressLists' returns object of type 'AddressLists'
		"AddressLists": (8461, 2, (9, 0), (), "AddressLists", '{00063048-0000-0000-C000-000000000046}'),
		# Method 'Application' returns object of type '_Application'
		"Application": (61440, 2, (9, 0), (), "Application", '{00063001-0000-0000-C000-000000000046}'),
		"AutoDiscoverConnectionMode": (64558, 2, (3, 0), (), "AutoDiscoverConnectionMode", None),
		"AutoDiscoverXml": (64515, 2, (8, 0), (), "AutoDiscoverXml", None),
		# Method 'Categories' returns object of type 'Categories'
		"Categories": (64421, 2, (13, 0), (), "Categories", '{000610E4-0000-0000-C000-000000000046}'),
		"Class": (61450, 2, (3, 0), (), "Class", None),
		"CurrentProfileName": (64213, 2, (8, 0), (), "CurrentProfileName", None),
		# Method 'CurrentUser' returns object of type 'Recipient'
		"CurrentUser": (8449, 2, (9, 0), (), "CurrentUser", '{00063045-0000-0000-C000-000000000046}'),
		# Method 'DefaultStore' returns object of type 'Store'
		"DefaultStore": (64236, 2, (13, 0), (), "DefaultStore", '{000610C7-0000-0000-C000-000000000046}'),
		"ExchangeConnectionMode": (64193, 2, (3, 0), (), "ExchangeConnectionMode", None),
		"ExchangeMailboxServerName": (64517, 2, (8, 0), (), "ExchangeMailboxServerName", None),
		"ExchangeMailboxServerVersion": (64516, 2, (8, 0), (), "ExchangeMailboxServerVersion", None),
		# Method 'Folders' returns object of type '_Folders'
		"Folders": (8451, 2, (9, 0), (), "Folders", '{00063040-0000-0000-C000-000000000046}'),
		"MAPIOBJECT": (61696, 2, (13, 0), (), "MAPIOBJECT", None),
		"Offline": (64076, 2, (11, 0), (), "Offline", None),
		"Parent": (61441, 2, (9, 0), (), "Parent", None),
		# Method 'Session' returns object of type '_NameSpace'
		"Session": (61451, 2, (9, 0), (), "Session", '{00063002-0000-0000-C000-000000000046}'),
		# Method 'Stores' returns object of type 'Stores'
		"Stores": (64216, 2, (13, 0), (), "Stores", '{000610C6-0000-0000-C000-000000000046}'),
		# Method 'SyncObjects' returns object of type 'SyncObjects'
		"SyncObjects": (8472, 2, (9, 0), (), "SyncObjects", '{00063086-0000-0000-C000-000000000046}'),
		"Type": (8452, 2, (8, 0), (), "Type", None),
	}
	_prop_map_put_ = {
	}

win32com.client.CLSIDToClass.RegisterCLSID( "{00063002-0000-0000-C000-000000000046}", _NameSpace )
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

_NameSpace_vtables_dispatch_ = 1
_NameSpace_vtables_ = [
	(( u'Application' , u'Application' , ), 61440, (61440, (), [ (16393, 10, None, "IID('{00063001-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 28 , (3, 0, None, None) , 0 , )),
	(( u'Class' , u'Class' , ), 61450, (61450, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 32 , (3, 0, None, None) , 0 , )),
	(( u'Session' , u'Session' , ), 61451, (61451, (), [ (16393, 10, None, "IID('{00063002-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 36 , (3, 0, None, None) , 0 , )),
	(( u'Parent' , u'Parent' , ), 61441, (61441, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 40 , (3, 0, None, None) , 0 , )),
	(( u'CurrentUser' , u'CurrentUser' , ), 8449, (8449, (), [ (16393, 10, None, "IID('{00063045-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 44 , (3, 0, None, None) , 0 , )),
	(( u'Folders' , u'Folders' , ), 8451, (8451, (), [ (16393, 10, None, "IID('{00063040-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 48 , (3, 0, None, None) , 0 , )),
	(( u'Type' , u'Type' , ), 8452, (8452, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 52 , (3, 0, None, None) , 0 , )),
	(( u'AddressLists' , u'AddressLists' , ), 8461, (8461, (), [ (16393, 10, None, "IID('{00063048-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 56 , (3, 0, None, None) , 0 , )),
	(( u'CreateRecipient' , u'RecipientName' , u'Recipient' , ), 8458, (8458, (), [ (8, 1, None, None) , 
			(16393, 10, None, "IID('{00063045-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 60 , (3, 0, None, None) , 0 , )),
	(( u'GetDefaultFolder' , u'FolderType' , u'Folder' , ), 8459, (8459, (), [ (3, 1, None, None) , 
			(16393, 10, None, "IID('{00063006-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 64 , (3, 0, None, None) , 0 , )),
	(( u'GetFolderFromID' , u'EntryIDFolder' , u'EntryIDStore' , u'Folder' , ), 8456, (8456, (), [ 
			(8, 1, None, None) , (12, 17, None, None) , (16393, 10, None, "IID('{00063006-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 1 , 68 , (3, 0, None, None) , 0 , )),
	(( u'GetItemFromID' , u'EntryIDItem' , u'EntryIDStore' , u'Item' , ), 8457, (8457, (), [ 
			(8, 1, None, None) , (12, 17, None, None) , (16393, 10, None, None) , ], 1 , 1 , 4 , 1 , 72 , (3, 0, None, None) , 0 , )),
	(( u'GetRecipientFromID' , u'EntryID' , u'Recipient' , ), 8455, (8455, (), [ (8, 1, None, None) , 
			(16393, 10, None, "IID('{00063045-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 76 , (3, 0, None, None) , 0 , )),
	(( u'GetSharedDefaultFolder' , u'Recipient' , u'FolderType' , u'Folder' , ), 8460, (8460, (), [ 
			(9, 1, None, "IID('{00063045-0000-0000-C000-000000000046}')") , (3, 1, None, None) , (16393, 10, None, "IID('{00063006-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 80 , (3, 0, None, None) , 0 , )),
	(( u'Logoff' , ), 8454, (8454, (), [ ], 1 , 1 , 4 , 0 , 84 , (3, 0, None, None) , 0 , )),
	(( u'Logon' , u'Profile' , u'Password' , u'ShowDialog' , u'NewSession' , 
			), 8453, (8453, (), [ (12, 17, None, None) , (12, 17, None, None) , (12, 17, None, None) , (12, 17, None, None) , ], 1 , 1 , 4 , 4 , 88 , (3, 0, None, None) , 0 , )),
	(( u'PickFolder' , u'Folder' , ), 8462, (8462, (), [ (16393, 10, None, "IID('{00063006-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 92 , (3, 0, None, None) , 0 , )),
	(( u'RefreshRemoteHeaders' , ), 8471, (8471, (), [ ], 1 , 1 , 4 , 0 , 96 , (3, 0, None, None) , 64 , )),
	(( u'SyncObjects' , u'SyncObjects' , ), 8472, (8472, (), [ (16393, 10, None, "IID('{00063086-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 100 , (3, 0, None, None) , 0 , )),
	(( u'AddStore' , u'Store' , ), 8473, (8473, (), [ (12, 1, None, None) , ], 1 , 1 , 4 , 0 , 104 , (3, 0, None, None) , 0 , )),
	(( u'RemoveStore' , u'Folder' , ), 8474, (8474, (), [ (9, 1, None, "IID('{00063006-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 108 , (3, 0, None, None) , 0 , )),
	(( u'Offline' , u'Offline' , ), 64076, (64076, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 112 , (3, 0, None, None) , 0 , )),
	(( u'Dial' , u'ContactItem' , ), 64013, (64013, (), [ (12, 17, None, None) , ], 1 , 1 , 4 , 1 , 116 , (3, 0, None, None) , 0 , )),
	(( u'MAPIOBJECT' , u'MAPIOBJECT' , ), 61696, (61696, (), [ (16397, 10, None, None) , ], 1 , 2 , 4 , 0 , 120 , (3, 0, None, None) , 64 , )),
	(( u'ExchangeConnectionMode' , u'ExchangeConnectionMode' , ), 64193, (64193, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 124 , (3, 0, None, None) , 0 , )),
	(( u'AddStoreEx' , u'Store' , u'Type' , ), 64197, (64197, (), [ (12, 1, None, None) , 
			(3, 1, None, None) , ], 1 , 1 , 4 , 0 , 128 , (3, 0, None, None) , 0 , )),
	(( u'Accounts' , u'Accounts' , ), 64208, (64208, (), [ (16397, 10, None, "IID('{000610C4-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 132 , (3, 0, None, None) , 0 , )),
	(( u'CurrentProfileName' , u'CurrentProfileName' , ), 64213, (64213, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 136 , (3, 0, None, None) , 0 , )),
	(( u'Stores' , u'Stores' , ), 64216, (64216, (), [ (16397, 10, None, "IID('{000610C6-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 140 , (3, 0, None, None) , 0 , )),
	(( u'GetSelectNamesDialog' , u'SelectNamesDialog' , ), 64225, (64225, (), [ (16397, 10, None, "IID('{000610C8-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 144 , (3, 0, None, None) , 0 , )),
	(( u'SendAndReceive' , u'showProgressDialog' , ), 64215, (64215, (), [ (11, 1, None, None) , ], 1 , 1 , 4 , 0 , 148 , (3, 0, None, None) , 0 , )),
	(( u'DefaultStore' , u'DefaultStore' , ), 64236, (64236, (), [ (16397, 10, None, "IID('{000610C7-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 152 , (3, 0, None, None) , 0 , )),
	(( u'GetAddressEntryFromID' , u'ID' , u'AddressEntry' , ), 64260, (64260, (), [ (8, 1, None, None) , 
			(16393, 10, None, "IID('{0006304B-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 156 , (3, 0, None, None) , 0 , )),
	(( u'GetGlobalAddressList' , u'globalAddressList' , ), 64261, (64261, (), [ (16393, 10, None, "IID('{00063049-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 160 , (3, 0, None, None) , 0 , )),
	(( u'GetStoreFromID' , u'ID' , u'Store' , ), 64262, (64262, (), [ (8, 1, None, None) , 
			(16397, 10, None, "IID('{000610C7-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 164 , (3, 0, None, None) , 0 , )),
	(( u'Categories' , u'Categories' , ), 64421, (64421, (), [ (16397, 10, None, "IID('{000610E4-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 168 , (3, 0, None, None) , 0 , )),
	(( u'OpenSharedFolder' , u'Path' , u'Name' , u'DownloadAttachments' , u'UseTTL' , 
			u'ret' , ), 64502, (64502, (), [ (8, 1, None, None) , (12, 17, None, None) , (12, 17, None, None) , 
			(12, 17, None, None) , (16393, 10, None, "IID('{00063006-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 3 , 172 , (3, 0, None, None) , 0 , )),
	(( u'OpenSharedItem' , u'Path' , u'Item' , ), 64503, (64503, (), [ (8, 1, None, None) , 
			(16393, 10, None, None) , ], 1 , 1 , 4 , 0 , 176 , (3, 0, None, None) , 0 , )),
	(( u'CreateSharingItem' , u'Context' , u'Provider' , u'Item' , ), 64484, (64484, (), [ 
			(12, 1, None, None) , (12, 17, None, None) , (16397, 10, None, "IID('{00061067-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 1 , 180 , (3, 0, None, None) , 0 , )),
	(( u'ExchangeMailboxServerName' , u'ExchangeMailboxServerName' , ), 64517, (64517, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 184 , (3, 0, None, None) , 0 , )),
	(( u'ExchangeMailboxServerVersion' , u'ExchangeMailboxServerVersion' , ), 64516, (64516, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 188 , (3, 0, None, None) , 0 , )),
	(( u'CompareEntryIDs' , u'FirstEntryID' , u'SecondEntryID' , u'Result' , ), 64508, (64508, (), [ 
			(8, 1, None, None) , (8, 1, None, None) , (16395, 10, None, None) , ], 1 , 1 , 4 , 0 , 192 , (3, 0, None, None) , 0 , )),
	(( u'AutoDiscoverXml' , u'AutoDiscoverXml' , ), 64515, (64515, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 196 , (3, 0, None, None) , 0 , )),
	(( u'AutoDiscoverConnectionMode' , u'AutoDiscoverConnectionMode' , ), 64558, (64558, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 200 , (3, 0, None, None) , 0 , )),
]

win32com.client.CLSIDToClass.RegisterCLSID( "{00063002-0000-0000-C000-000000000046}", _NameSpace )
