# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.00
# By python version 2.5.4 (r254:67916, Dec 23 2008, 15:10:54) [MSC v.1310 32 bit (Intel)]
# From type library '{00062FFF-0000-0000-C000-000000000046}'
# On Wed May 04 17:52:55 2011
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

class ItemEvents_10:
	CLSID = CLSID_Sink = IID('{0006302B-0000-0000-C000-000000000046}')
	coclass_clsid = IID('{0006103C-0000-0000-C000-000000000046}')
	_public_methods_ = [] # For COM Server support
	_dispid_to_func_ = {
		    61452 : "OnAttachmentRead",
		    61448 : "OnCustomPropertyChange",
		    61445 : "OnSend",
		    61442 : "OnWrite",
		    61453 : "OnBeforeAttachmentSave",
		    62568 : "OnForward",
		    62566 : "OnReply",
		    62567 : "OnReplyAll",
		    61441 : "OnRead",
		    64429 : "OnUnload",
		    61449 : "OnPropertyChange",
		    64427 : "OnBeforeAttachmentRead",
		    61451 : "OnAttachmentAdd",
		    61446 : "OnCustomAction",
		    64432 : "OnBeforeAttachmentAdd",
		    64430 : "OnAttachmentRemove",
		    64117 : "OnBeforeDelete",
		    61444 : "OnClose",
		    61450 : "OnBeforeCheckNames",
		    64434 : "OnBeforeAttachmentWriteToTempFile",
		    64514 : "OnBeforeAutoSave",
		    64431 : "OnBeforeAttachmentPreview",
		    61443 : "OnOpen",
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
#	def OnAttachmentRead(self, Attachment=defaultNamedNotOptArg):
#	def OnCustomPropertyChange(self, Name=defaultNamedNotOptArg):
#	def OnSend(self, Cancel=defaultNamedNotOptArg):
#	def OnWrite(self, Cancel=defaultNamedNotOptArg):
#	def OnBeforeAttachmentSave(self, Attachment=defaultNamedNotOptArg, Cancel=defaultNamedNotOptArg):
#	def OnForward(self, Forward=defaultNamedNotOptArg, Cancel=defaultNamedNotOptArg):
#	def OnReply(self, Response=defaultNamedNotOptArg, Cancel=defaultNamedNotOptArg):
#	def OnReplyAll(self, Response=defaultNamedNotOptArg, Cancel=defaultNamedNotOptArg):
#	def OnRead(self):
#	def OnUnload(self):
#	def OnPropertyChange(self, Name=defaultNamedNotOptArg):
#	def OnBeforeAttachmentRead(self, Attachment=defaultNamedNotOptArg, Cancel=defaultNamedNotOptArg):
#	def OnAttachmentAdd(self, Attachment=defaultNamedNotOptArg):
#	def OnCustomAction(self, Action=defaultNamedNotOptArg, Response=defaultNamedNotOptArg, Cancel=defaultNamedNotOptArg):
#	def OnBeforeAttachmentAdd(self, Attachment=defaultNamedNotOptArg, Cancel=defaultNamedNotOptArg):
#	def OnAttachmentRemove(self, Attachment=defaultNamedNotOptArg):
#	def OnBeforeDelete(self, Item=defaultNamedNotOptArg, Cancel=defaultNamedNotOptArg):
#	def OnClose(self, Cancel=defaultNamedNotOptArg):
#	def OnBeforeCheckNames(self, Cancel=defaultNamedNotOptArg):
#	def OnBeforeAttachmentWriteToTempFile(self, Attachment=defaultNamedNotOptArg, Cancel=defaultNamedNotOptArg):
#	def OnBeforeAutoSave(self, Cancel=defaultNamedNotOptArg):
#	def OnBeforeAttachmentPreview(self, Attachment=defaultNamedNotOptArg, Cancel=defaultNamedNotOptArg):
#	def OnOpen(self, Cancel=defaultNamedNotOptArg):


win32com.client.CLSIDToClass.RegisterCLSID( "{0006302B-0000-0000-C000-000000000046}", ItemEvents_10 )
