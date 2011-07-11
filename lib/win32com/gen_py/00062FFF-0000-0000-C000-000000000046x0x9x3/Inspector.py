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

from win32com.client import CoClassBaseClass
import sys
__import__('win32com.gen_py.00062FFF-0000-0000-C000-000000000046x0x9x3.InspectorEvents_10')
InspectorEvents_10 = sys.modules['win32com.gen_py.00062FFF-0000-0000-C000-000000000046x0x9x3.InspectorEvents_10'].InspectorEvents_10
__import__('win32com.gen_py.00062FFF-0000-0000-C000-000000000046x0x9x3.InspectorEvents')
InspectorEvents = sys.modules['win32com.gen_py.00062FFF-0000-0000-C000-000000000046x0x9x3.InspectorEvents'].InspectorEvents
__import__('win32com.gen_py.00062FFF-0000-0000-C000-000000000046x0x9x3._Inspector')
_Inspector = sys.modules['win32com.gen_py.00062FFF-0000-0000-C000-000000000046x0x9x3._Inspector']._Inspector
class Inspector(CoClassBaseClass): # A CoClass
	CLSID = IID('{00063058-0000-0000-C000-000000000046}')
	coclass_sources = [
		InspectorEvents_10,
		InspectorEvents,
	]
	default_source = InspectorEvents_10
	coclass_interfaces = [
		_Inspector,
	]
	default_interface = _Inspector

win32com.client.CLSIDToClass.RegisterCLSID( "{00063058-0000-0000-C000-000000000046}", Inspector )
