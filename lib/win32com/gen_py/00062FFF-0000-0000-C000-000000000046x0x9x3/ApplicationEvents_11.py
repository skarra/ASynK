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

class ApplicationEvents_11:
	CLSID = CLSID_Sink = IID('{0006302C-0000-0000-C000-000000000046}')
	coclass_clsid = IID('{0006F03A-0000-0000-C000-000000000046}')
	_public_methods_ = [] # For COM Server support
	_dispid_to_func_ = {
		    61447 : "OnQuit",
		    64423 : "OnItemLoad",
		    64107 : "OnAdvancedSearchStopped",
		    64322 : "OnFolderContextMenuDisplay",
		    61442 : "OnItemSend",
		    61446 : "OnStartup",
		    64321 : "OnItemContextMenuDisplay",
		    64422 : "OnContextMenuClose",
		    64323 : "OnStoreContextMenuDisplay",
		    64144 : "OnMAPILogonComplete",
		    64324 : "OnShortcutContextMenuDisplay",
		    64318 : "OnAttachmentContextMenuDisplay",
		    61443 : "OnNewMail",
		    64181 : "OnNewMailEx",
		    61444 : "OnReminder",
		    64320 : "OnViewContextMenuDisplay",
		    61445 : "OnOptionsPagesAdd",
		    64106 : "OnAdvancedSearchComplete",
		    64513 : "OnBeforeFolderSharingDialog",
		}

	def __init__(self, oobj = None):
		if oobj is None:
			self._olecp = None
		else:
			import win32com.server.util
			from win32com.server.policy import EventHandlerPolicy
			cpc=oobj._oleobj_.QueryInterface(pythoncom.IID_IConnectionPointContainer)
			cp=cpc.FindConnectionPoint(self.CLSID_Sink)
			cookie=cp.Advise(win32com.server.util.wrap(self, usePolicy=EventHandlerPolicy))
			self._olecp,self._olecp_cookie = cp,cookie
	def __del__(self):
		try:
			self.close()
		except pythoncom.com_error:
			pass
	def close(self):
		if self._olecp is not None:
			cp,cookie,self._olecp,self._olecp_cookie = self._olecp,self._olecp_cookie,None,None
			cp.Unadvise(cookie)
	def _query_interface_(self, iid):
		import win32com.server.util
		if iid==self.CLSID_Sink: return win32com.server.util.wrap(self)

	# Event Handlers
	# If you create handlers, they should have the following prototypes:
#	def OnQuit(self):
#	def OnItemLoad(self, Item=defaultNamedNotOptArg):
#	def OnAdvancedSearchStopped(self, SearchObject=defaultNamedNotOptArg):
#	def OnFolderContextMenuDisplay(self, CommandBar=defaultNamedNotOptArg, Folder=defaultNamedNotOptArg):
#	def OnItemSend(self, Item=defaultNamedNotOptArg, Cancel=defaultNamedNotOptArg):
#	def OnStartup(self):
#	def OnItemContextMenuDisplay(self, CommandBar=defaultNamedNotOptArg, Selection=defaultNamedNotOptArg):
#	def OnContextMenuClose(self, ContextMenu=defaultNamedNotOptArg):
#	def OnStoreContextMenuDisplay(self, CommandBar=defaultNamedNotOptArg, Store=defaultNamedNotOptArg):
#	def OnMAPILogonComplete(self):
#	def OnShortcutContextMenuDisplay(self, CommandBar=defaultNamedNotOptArg, Shortcut=defaultNamedNotOptArg):
#	def OnAttachmentContextMenuDisplay(self, CommandBar=defaultNamedNotOptArg, Attachments=defaultNamedNotOptArg):
#	def OnNewMail(self):
#	def OnNewMailEx(self, EntryIDCollection=defaultNamedNotOptArg):
#	def OnReminder(self, Item=defaultNamedNotOptArg):
#	def OnViewContextMenuDisplay(self, CommandBar=defaultNamedNotOptArg, View=defaultNamedNotOptArg):
#	def OnOptionsPagesAdd(self, Pages=defaultNamedNotOptArg):
#	def OnAdvancedSearchComplete(self, SearchObject=defaultNamedNotOptArg):
#	def OnBeforeFolderSharingDialog(self, FolderToShare=defaultNamedNotOptArg, Cancel=defaultNamedNotOptArg):


win32com.client.CLSIDToClass.RegisterCLSID( "{0006302C-0000-0000-C000-000000000046}", ApplicationEvents_11 )
