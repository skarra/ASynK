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

from win32com.client import CoClassBaseClass
import sys
__import__('win32com.gen_py.00062FFF-0000-0000-C000-000000000046x0x9x3.ItemEvents')
ItemEvents = sys.modules['win32com.gen_py.00062FFF-0000-0000-C000-000000000046x0x9x3.ItemEvents'].ItemEvents
__import__('win32com.gen_py.00062FFF-0000-0000-C000-000000000046x0x9x3.ItemEvents_10')
ItemEvents_10 = sys.modules['win32com.gen_py.00062FFF-0000-0000-C000-000000000046x0x9x3.ItemEvents_10'].ItemEvents_10
__import__('win32com.gen_py.00062FFF-0000-0000-C000-000000000046x0x9x3._DistListItem')
_DistListItem = sys.modules['win32com.gen_py.00062FFF-0000-0000-C000-000000000046x0x9x3._DistListItem']._DistListItem
class DistListItem(CoClassBaseClass): # A CoClass
	CLSID = IID('{0006103C-0000-0000-C000-000000000046}')
	coclass_sources = [
		ItemEvents,
		ItemEvents_10,
	]
	default_source = ItemEvents_10
	coclass_interfaces = [
		_DistListItem,
	]
	default_interface = _DistListItem

win32com.client.CLSIDToClass.RegisterCLSID( "{0006103C-0000-0000-C000-000000000046}", DistListItem )
