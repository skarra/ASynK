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
class _ContactItem(DispatchBaseClass):
	CLSID = IID('{00063021-0000-0000-C000-000000000046}')
	coclass_clsid = IID('{00061031-0000-0000-C000-000000000046}')

	def AddBusinessCardLogoPicture(self, Path=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64527, LCID, 1, (24, 0), ((8, 1),),Path
			)

	def AddPicture(self, Path=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64189, LCID, 1, (24, 0), ((8, 1),),Path
			)

	def ClearTaskFlag(self):
		return self._oleobj_.InvokeTypes(64521, LCID, 1, (24, 0), (),)

	def Close(self, SaveMode=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(61475, LCID, 1, (24, 0), ((3, 1),),SaveMode
			)

	def Copy(self):
		ret = self._oleobj_.InvokeTypes(61490, LCID, 1, (9, 0), (),)
		if ret is not None:
			ret = Dispatch(ret, u'Copy', None)
		return ret

	def Delete(self):
		return self._oleobj_.InvokeTypes(61514, LCID, 1, (24, 0), (),)

	def Display(self, Modal=defaultNamedOptArg):
		return self._oleobj_.InvokeTypes(61606, LCID, 1, (24, 0), ((12, 17),),Modal
			)

	# Result is of type MailItem
	def ForwardAsBusinessCard(self):
		ret = self._oleobj_.InvokeTypes(64404, LCID, 1, (13, 0), (),)
		if ret is not None:
			# See if this IUnknown is really an IDispatch
			try:
				ret = ret.QueryInterface(pythoncom.IID_IDispatch)
			except pythoncom.error:
				return ret
			ret = Dispatch(ret, u'ForwardAsBusinessCard', '{00061033-0000-0000-C000-000000000046}')
		return ret

	# Result is of type MailItem
	def ForwardAsVcard(self):
		ret = self._oleobj_.InvokeTypes(63649, LCID, 1, (13, 0), (),)
		if ret is not None:
			# See if this IUnknown is really an IDispatch
			try:
				ret = ret.QueryInterface(pythoncom.IID_IDispatch)
			except pythoncom.error:
				return ret
			ret = Dispatch(ret, u'ForwardAsVcard', '{00061033-0000-0000-C000-000000000046}')
		return ret

	def MarkAsTask(self, MarkInterval=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64510, LCID, 1, (24, 0), ((3, 1),),MarkInterval
			)

	def Move(self, DestFldr=defaultNamedNotOptArg):
		ret = self._oleobj_.InvokeTypes(61492, LCID, 1, (9, 0), ((9, 1),),DestFldr
			)
		if ret is not None:
			ret = Dispatch(ret, u'Move', None)
		return ret

	def PrintOut(self):
		return self._oleobj_.InvokeTypes(61491, LCID, 1, (24, 0), (),)

	def RemovePicture(self):
		return self._oleobj_.InvokeTypes(64190, LCID, 1, (24, 0), (),)

	def ResetBusinessCard(self):
		return self._oleobj_.InvokeTypes(64526, LCID, 1, (24, 0), (),)

	def Save(self):
		return self._oleobj_.InvokeTypes(61512, LCID, 1, (24, 0), (),)

	def SaveAs(self, Path=defaultNamedNotOptArg, Type=defaultNamedOptArg):
		return self._oleobj_.InvokeTypes(61521, LCID, 1, (24, 0), ((8, 1), (12, 17)),Path
			, Type)

	def SaveBusinessCardImage(self, Path=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64407, LCID, 1, (24, 0), ((8, 1),),Path
			)

	def ShowBusinessCardEditor(self):
		return self._oleobj_.InvokeTypes(64405, LCID, 1, (24, 0), (),)

	def ShowCategoriesDialog(self):
		return self._oleobj_.InvokeTypes(64011, LCID, 1, (24, 0), (),)

	def ShowCheckPhoneDialog(self, PhoneNumber=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(64471, LCID, 1, (24, 0), ((3, 1),),PhoneNumber
			)

	_prop_map_get_ = {
		"Account": (14848, 2, (8, 0), (), "Account", None),
		# Method 'Actions' returns object of type 'Actions'
		"Actions": (63511, 2, (9, 0), (), "Actions", '{0006303E-0000-0000-C000-000000000046}'),
		"Anniversary": (14913, 2, (7, 0), (), "Anniversary", None),
		# Method 'Application' returns object of type '_Application'
		"Application": (61440, 2, (9, 0), (), "Application", '{00063001-0000-0000-C000-000000000046}'),
		"AssistantName": (14896, 2, (8, 0), (), "AssistantName", None),
		"AssistantTelephoneNumber": (14894, 2, (8, 0), (), "AssistantTelephoneNumber", None),
		# Method 'Attachments' returns object of type 'Attachments'
		"Attachments": (63509, 2, (9, 0), (), "Attachments", '{0006303C-0000-0000-C000-000000000046}'),
		"AutoResolvedWinner": (64186, 2, (11, 0), (), "AutoResolvedWinner", None),
		"BillingInformation": (34101, 2, (8, 0), (), "BillingInformation", None),
		"Birthday": (14914, 2, (7, 0), (), "Birthday", None),
		"Body": (37120, 2, (8, 0), (), "Body", None),
		"Business2TelephoneNumber": (14875, 2, (8, 0), (), "Business2TelephoneNumber", None),
		"BusinessAddress": (32795, 2, (8, 0), (), "BusinessAddress", None),
		"BusinessAddressCity": (32838, 2, (8, 0), (), "BusinessAddressCity", None),
		"BusinessAddressCountry": (32841, 2, (8, 0), (), "BusinessAddressCountry", None),
		"BusinessAddressPostOfficeBox": (32842, 2, (8, 0), (), "BusinessAddressPostOfficeBox", None),
		"BusinessAddressPostalCode": (32840, 2, (8, 0), (), "BusinessAddressPostalCode", None),
		"BusinessAddressState": (32839, 2, (8, 0), (), "BusinessAddressState", None),
		"BusinessAddressStreet": (32837, 2, (8, 0), (), "BusinessAddressStreet", None),
		"BusinessCardLayoutXml": (64525, 2, (8, 0), (), "BusinessCardLayoutXml", None),
		"BusinessCardType": (64528, 2, (3, 0), (), "BusinessCardType", None),
		"BusinessFaxNumber": (14884, 2, (8, 0), (), "BusinessFaxNumber", None),
		"BusinessHomePage": (14929, 2, (8, 0), (), "BusinessHomePage", None),
		"BusinessTelephoneNumber": (14856, 2, (8, 0), (), "BusinessTelephoneNumber", None),
		"CallbackTelephoneNumber": (14850, 2, (8, 0), (), "CallbackTelephoneNumber", None),
		"CarTelephoneNumber": (14878, 2, (8, 0), (), "CarTelephoneNumber", None),
		"Categories": (36865, 2, (8, 0), (), "Categories", None),
		"Children": (32780, 2, (8, 0), (), "Children", None),
		"Class": (61450, 2, (3, 0), (), "Class", None),
		"Companies": (34107, 2, (8, 0), (), "Companies", None),
		"CompanyAndFullName": (32792, 2, (8, 0), (), "CompanyAndFullName", None),
		"CompanyLastFirstNoSpace": (32818, 2, (8, 0), (), "CompanyLastFirstNoSpace", None),
		"CompanyLastFirstSpaceOnly": (32819, 2, (8, 0), (), "CompanyLastFirstSpaceOnly", None),
		"CompanyMainTelephoneNumber": (14935, 2, (8, 0), (), "CompanyMainTelephoneNumber", None),
		"CompanyName": (14870, 2, (8, 0), (), "CompanyName", None),
		"ComputerNetworkName": (14921, 2, (8, 0), (), "ComputerNetworkName", None),
		# Method 'Conflicts' returns object of type 'Conflicts'
		"Conflicts": (64187, 2, (9, 0), (), "Conflicts", '{000630C2-0000-0000-C000-000000000046}'),
		"ConversationIndex": (64192, 2, (8, 0), (), "ConversationIndex", None),
		"ConversationTopic": (112, 2, (8, 0), (), "ConversationTopic", None),
		"CreationTime": (12295, 2, (7, 0), (), "CreationTime", None),
		"CustomerID": (14922, 2, (8, 0), (), "CustomerID", None),
		"Department": (14872, 2, (8, 0), (), "Department", None),
		"DownloadState": (64077, 2, (3, 0), (), "DownloadState", None),
		"Email1Address": (32899, 2, (8, 0), (), "Email1Address", None),
		"Email1AddressType": (32898, 2, (8, 0), (), "Email1AddressType", None),
		"Email1DisplayName": (32896, 2, (8, 0), (), "Email1DisplayName", None),
		"Email1EntryID": (32901, 2, (8, 0), (), "Email1EntryID", None),
		"Email2Address": (32915, 2, (8, 0), (), "Email2Address", None),
		"Email2AddressType": (32914, 2, (8, 0), (), "Email2AddressType", None),
		"Email2DisplayName": (32912, 2, (8, 0), (), "Email2DisplayName", None),
		"Email2EntryID": (32917, 2, (8, 0), (), "Email2EntryID", None),
		"Email3Address": (32931, 2, (8, 0), (), "Email3Address", None),
		"Email3AddressType": (32930, 2, (8, 0), (), "Email3AddressType", None),
		"Email3DisplayName": (32928, 2, (8, 0), (), "Email3DisplayName", None),
		"Email3EntryID": (32933, 2, (8, 0), (), "Email3EntryID", None),
		"EntryID": (61470, 2, (8, 0), (), "EntryID", None),
		"FTPSite": (14924, 2, (8, 0), (), "FTPSite", None),
		"FileAs": (32773, 2, (8, 0), (), "FileAs", None),
		"FirstName": (14854, 2, (8, 0), (), "FirstName", None),
		# Method 'FormDescription' returns object of type 'FormDescription'
		"FormDescription": (61589, 2, (9, 0), (), "FormDescription", '{00063046-0000-0000-C000-000000000046}'),
		"FullName": (12289, 2, (8, 0), (), "FullName", None),
		"FullNameAndCompany": (32793, 2, (8, 0), (), "FullNameAndCompany", None),
		"Gender": (14925, 2, (3, 0), (), "Gender", None),
		# Method 'GetInspector' returns object of type '_Inspector'
		"GetInspector": (61502, 2, (9, 0), (), "GetInspector", '{00063005-0000-0000-C000-000000000046}'),
		"GovernmentIDNumber": (14855, 2, (8, 0), (), "GovernmentIDNumber", None),
		"HasPicture": (64191, 2, (11, 0), (), "HasPicture", None),
		"Hobby": (14915, 2, (8, 0), (), "Hobby", None),
		"Home2TelephoneNumber": (14895, 2, (8, 0), (), "Home2TelephoneNumber", None),
		"HomeAddress": (32794, 2, (8, 0), (), "HomeAddress", None),
		"HomeAddressCity": (14937, 2, (8, 0), (), "HomeAddressCity", None),
		"HomeAddressCountry": (14938, 2, (8, 0), (), "HomeAddressCountry", None),
		"HomeAddressPostOfficeBox": (14942, 2, (8, 0), (), "HomeAddressPostOfficeBox", None),
		"HomeAddressPostalCode": (14939, 2, (8, 0), (), "HomeAddressPostalCode", None),
		"HomeAddressState": (14940, 2, (8, 0), (), "HomeAddressState", None),
		"HomeAddressStreet": (14941, 2, (8, 0), (), "HomeAddressStreet", None),
		"HomeFaxNumber": (14885, 2, (8, 0), (), "HomeFaxNumber", None),
		"HomeTelephoneNumber": (14857, 2, (8, 0), (), "HomeTelephoneNumber", None),
		"IMAddress": (32866, 2, (8, 0), (), "IMAddress", None),
		"ISDNNumber": (14893, 2, (8, 0), (), "ISDNNumber", None),
		"Importance": (23, 2, (3, 0), (), "Importance", None),
		"Initials": (14858, 2, (8, 0), (), "Initials", None),
		"InternetFreeBusyAddress": (32984, 2, (8, 0), (), "InternetFreeBusyAddress", None),
		"IsConflict": (64164, 2, (11, 0), (), "IsConflict", None),
		"IsMarkedAsTask": (64522, 2, (11, 0), (), "IsMarkedAsTask", None),
		# Method 'ItemProperties' returns object of type 'ItemProperties'
		"ItemProperties": (64009, 2, (9, 0), (), "ItemProperties", '{000630A8-0000-0000-C000-000000000046}'),
		"JobTitle": (14871, 2, (8, 0), (), "JobTitle", None),
		"Journal": (32805, 2, (11, 0), (), "Journal", None),
		"Language": (14860, 2, (8, 0), (), "Language", None),
		"LastFirstAndSuffix": (32822, 2, (8, 0), (), "LastFirstAndSuffix", None),
		"LastFirstNoSpace": (32816, 2, (8, 0), (), "LastFirstNoSpace", None),
		"LastFirstNoSpaceAndSuffix": (32824, 2, (8, 0), (), "LastFirstNoSpaceAndSuffix", None),
		"LastFirstNoSpaceCompany": (32820, 2, (8, 0), (), "LastFirstNoSpaceCompany", None),
		"LastFirstSpaceOnly": (32817, 2, (8, 0), (), "LastFirstSpaceOnly", None),
		"LastFirstSpaceOnlyCompany": (32821, 2, (8, 0), (), "LastFirstSpaceOnlyCompany", None),
		"LastModificationTime": (12296, 2, (7, 0), (), "LastModificationTime", None),
		"LastName": (14865, 2, (8, 0), (), "LastName", None),
		"LastNameAndFirstName": (32791, 2, (8, 0), (), "LastNameAndFirstName", None),
		# Method 'Links' returns object of type 'Links'
		"Links": (62469, 2, (9, 0), (), "Links", '{0006308A-0000-0000-C000-000000000046}'),
		"MAPIOBJECT": (61696, 2, (13, 0), (), "MAPIOBJECT", None),
		"MailingAddress": (14869, 2, (8, 0), (), "MailingAddress", None),
		"MailingAddressCity": (14887, 2, (8, 0), (), "MailingAddressCity", None),
		"MailingAddressCountry": (14886, 2, (8, 0), (), "MailingAddressCountry", None),
		"MailingAddressPostOfficeBox": (14891, 2, (8, 0), (), "MailingAddressPostOfficeBox", None),
		"MailingAddressPostalCode": (14890, 2, (8, 0), (), "MailingAddressPostalCode", None),
		"MailingAddressState": (14888, 2, (8, 0), (), "MailingAddressState", None),
		"MailingAddressStreet": (14889, 2, (8, 0), (), "MailingAddressStreet", None),
		"ManagerName": (14926, 2, (8, 0), (), "ManagerName", None),
		"MarkForDownload": (34161, 2, (3, 0), (), "MarkForDownload", None),
		"MessageClass": (26, 2, (8, 0), (), "MessageClass", None),
		"MiddleName": (14916, 2, (8, 0), (), "MiddleName", None),
		"Mileage": (34100, 2, (8, 0), (), "Mileage", None),
		"MobileTelephoneNumber": (14876, 2, (8, 0), (), "MobileTelephoneNumber", None),
		"NetMeetingAlias": (32863, 2, (8, 0), (), "NetMeetingAlias", None),
		"NetMeetingServer": (32864, 2, (8, 0), (), "NetMeetingServer", None),
		"NickName": (14927, 2, (8, 0), (), "NickName", None),
		"NoAging": (34062, 2, (11, 0), (), "NoAging", None),
		"OfficeLocation": (14873, 2, (8, 0), (), "OfficeLocation", None),
		"OrganizationalIDNumber": (14864, 2, (8, 0), (), "OrganizationalIDNumber", None),
		"OtherAddress": (32796, 2, (8, 0), (), "OtherAddress", None),
		"OtherAddressCity": (14943, 2, (8, 0), (), "OtherAddressCity", None),
		"OtherAddressCountry": (14944, 2, (8, 0), (), "OtherAddressCountry", None),
		"OtherAddressPostOfficeBox": (14948, 2, (8, 0), (), "OtherAddressPostOfficeBox", None),
		"OtherAddressPostalCode": (14945, 2, (8, 0), (), "OtherAddressPostalCode", None),
		"OtherAddressState": (14946, 2, (8, 0), (), "OtherAddressState", None),
		"OtherAddressStreet": (14947, 2, (8, 0), (), "OtherAddressStreet", None),
		"OtherFaxNumber": (14883, 2, (8, 0), (), "OtherFaxNumber", None),
		"OtherTelephoneNumber": (14879, 2, (8, 0), (), "OtherTelephoneNumber", None),
		"OutlookInternalVersion": (34130, 2, (3, 0), (), "OutlookInternalVersion", None),
		"OutlookVersion": (34132, 2, (8, 0), (), "OutlookVersion", None),
		"PagerNumber": (14881, 2, (8, 0), (), "PagerNumber", None),
		"Parent": (61441, 2, (9, 0), (), "Parent", None),
		"PersonalHomePage": (14928, 2, (8, 0), (), "PersonalHomePage", None),
		"PrimaryTelephoneNumber": (14874, 2, (8, 0), (), "PrimaryTelephoneNumber", None),
		"Profession": (14918, 2, (8, 0), (), "Profession", None),
		# Method 'PropertyAccessor' returns object of type 'PropertyAccessor'
		"PropertyAccessor": (64253, 2, (13, 0), (), "PropertyAccessor", '{0006102D-0000-0000-C000-000000000046}'),
		"RadioTelephoneNumber": (14877, 2, (8, 0), (), "RadioTelephoneNumber", None),
		"ReferredBy": (14919, 2, (8, 0), (), "ReferredBy", None),
		"ReminderOverrideDefault": (34076, 2, (11, 0), (), "ReminderOverrideDefault", None),
		"ReminderPlaySound": (34078, 2, (11, 0), (), "ReminderPlaySound", None),
		"ReminderSet": (34051, 2, (11, 0), (), "ReminderSet", None),
		"ReminderSoundFile": (34079, 2, (8, 0), (), "ReminderSoundFile", None),
		"ReminderTime": (34050, 2, (7, 0), (), "ReminderTime", None),
		"Saved": (61603, 2, (11, 0), (), "Saved", None),
		"SelectedMailingAddress": (32802, 2, (3, 0), (), "SelectedMailingAddress", None),
		"Sensitivity": (54, 2, (3, 0), (), "Sensitivity", None),
		# Method 'Session' returns object of type '_NameSpace'
		"Session": (61451, 2, (9, 0), (), "Session", '{00063002-0000-0000-C000-000000000046}'),
		"Size": (3592, 2, (3, 0), (), "Size", None),
		"Spouse": (14920, 2, (8, 0), (), "Spouse", None),
		"Subject": (55, 2, (8, 0), (), "Subject", None),
		"Suffix": (14853, 2, (8, 0), (), "Suffix", None),
		"TTYTDDTelephoneNumber": (14923, 2, (8, 0), (), "TTYTDDTelephoneNumber", None),
		"TaskCompletedDate": (33039, 2, (7, 0), (), "TaskCompletedDate", None),
		"TaskDueDate": (33029, 2, (7, 0), (), "TaskDueDate", None),
		"TaskStartDate": (33028, 2, (7, 0), (), "TaskStartDate", None),
		"TaskSubject": (64543, 2, (8, 0), (), "TaskSubject", None),
		"TelexNumber": (14892, 2, (8, 0), (), "TelexNumber", None),
		"Title": (14917, 2, (8, 0), (), "Title", None),
		"ToDoTaskOrdinal": (34208, 2, (7, 0), (), "ToDoTaskOrdinal", None),
		"UnRead": (61468, 2, (11, 0), (), "UnRead", None),
		"User1": (32847, 2, (8, 0), (), "User1", None),
		"User2": (32848, 2, (8, 0), (), "User2", None),
		"User3": (32849, 2, (8, 0), (), "User3", None),
		"User4": (32850, 2, (8, 0), (), "User4", None),
		"UserCertificate": (32790, 2, (8, 0), (), "UserCertificate", None),
		# Method 'UserProperties' returns object of type 'UserProperties'
		"UserProperties": (63510, 2, (9, 0), (), "UserProperties", '{0006303D-0000-0000-C000-000000000046}'),
		"WebPage": (32811, 2, (8, 0), (), "WebPage", None),
		"YomiCompanyName": (32814, 2, (8, 0), (), "YomiCompanyName", None),
		"YomiFirstName": (32812, 2, (8, 0), (), "YomiFirstName", None),
		"YomiLastName": (32813, 2, (8, 0), (), "YomiLastName", None),
	}
	_prop_map_put_ = {
		"Account": ((14848, LCID, 4, 0),()),
		"Anniversary": ((14913, LCID, 4, 0),()),
		"AssistantName": ((14896, LCID, 4, 0),()),
		"AssistantTelephoneNumber": ((14894, LCID, 4, 0),()),
		"BillingInformation": ((34101, LCID, 4, 0),()),
		"Birthday": ((14914, LCID, 4, 0),()),
		"Body": ((37120, LCID, 4, 0),()),
		"Business2TelephoneNumber": ((14875, LCID, 4, 0),()),
		"BusinessAddress": ((32795, LCID, 4, 0),()),
		"BusinessAddressCity": ((32838, LCID, 4, 0),()),
		"BusinessAddressCountry": ((32841, LCID, 4, 0),()),
		"BusinessAddressPostOfficeBox": ((32842, LCID, 4, 0),()),
		"BusinessAddressPostalCode": ((32840, LCID, 4, 0),()),
		"BusinessAddressState": ((32839, LCID, 4, 0),()),
		"BusinessAddressStreet": ((32837, LCID, 4, 0),()),
		"BusinessCardLayoutXml": ((64525, LCID, 4, 0),()),
		"BusinessFaxNumber": ((14884, LCID, 4, 0),()),
		"BusinessHomePage": ((14929, LCID, 4, 0),()),
		"BusinessTelephoneNumber": ((14856, LCID, 4, 0),()),
		"CallbackTelephoneNumber": ((14850, LCID, 4, 0),()),
		"CarTelephoneNumber": ((14878, LCID, 4, 0),()),
		"Categories": ((36865, LCID, 4, 0),()),
		"Children": ((32780, LCID, 4, 0),()),
		"Companies": ((34107, LCID, 4, 0),()),
		"CompanyMainTelephoneNumber": ((14935, LCID, 4, 0),()),
		"CompanyName": ((14870, LCID, 4, 0),()),
		"ComputerNetworkName": ((14921, LCID, 4, 0),()),
		"CustomerID": ((14922, LCID, 4, 0),()),
		"Department": ((14872, LCID, 4, 0),()),
		"Email1Address": ((32899, LCID, 4, 0),()),
		"Email1AddressType": ((32898, LCID, 4, 0),()),
		"Email1DisplayName": ((32896, LCID, 4, 0),()),
		"Email2Address": ((32915, LCID, 4, 0),()),
		"Email2AddressType": ((32914, LCID, 4, 0),()),
		"Email2DisplayName": ((32912, LCID, 4, 0),()),
		"Email3Address": ((32931, LCID, 4, 0),()),
		"Email3AddressType": ((32930, LCID, 4, 0),()),
		"Email3DisplayName": ((32928, LCID, 4, 0),()),
		"FTPSite": ((14924, LCID, 4, 0),()),
		"FileAs": ((32773, LCID, 4, 0),()),
		"FirstName": ((14854, LCID, 4, 0),()),
		"FullName": ((12289, LCID, 4, 0),()),
		"Gender": ((14925, LCID, 4, 0),()),
		"GovernmentIDNumber": ((14855, LCID, 4, 0),()),
		"Hobby": ((14915, LCID, 4, 0),()),
		"Home2TelephoneNumber": ((14895, LCID, 4, 0),()),
		"HomeAddress": ((32794, LCID, 4, 0),()),
		"HomeAddressCity": ((14937, LCID, 4, 0),()),
		"HomeAddressCountry": ((14938, LCID, 4, 0),()),
		"HomeAddressPostOfficeBox": ((14942, LCID, 4, 0),()),
		"HomeAddressPostalCode": ((14939, LCID, 4, 0),()),
		"HomeAddressState": ((14940, LCID, 4, 0),()),
		"HomeAddressStreet": ((14941, LCID, 4, 0),()),
		"HomeFaxNumber": ((14885, LCID, 4, 0),()),
		"HomeTelephoneNumber": ((14857, LCID, 4, 0),()),
		"IMAddress": ((32866, LCID, 4, 0),()),
		"ISDNNumber": ((14893, LCID, 4, 0),()),
		"Importance": ((23, LCID, 4, 0),()),
		"Initials": ((14858, LCID, 4, 0),()),
		"InternetFreeBusyAddress": ((32984, LCID, 4, 0),()),
		"JobTitle": ((14871, LCID, 4, 0),()),
		"Journal": ((32805, LCID, 4, 0),()),
		"Language": ((14860, LCID, 4, 0),()),
		"LastName": ((14865, LCID, 4, 0),()),
		"MailingAddress": ((14869, LCID, 4, 0),()),
		"MailingAddressCity": ((14887, LCID, 4, 0),()),
		"MailingAddressCountry": ((14886, LCID, 4, 0),()),
		"MailingAddressPostOfficeBox": ((14891, LCID, 4, 0),()),
		"MailingAddressPostalCode": ((14890, LCID, 4, 0),()),
		"MailingAddressState": ((14888, LCID, 4, 0),()),
		"MailingAddressStreet": ((14889, LCID, 4, 0),()),
		"ManagerName": ((14926, LCID, 4, 0),()),
		"MarkForDownload": ((34161, LCID, 4, 0),()),
		"MessageClass": ((26, LCID, 4, 0),()),
		"MiddleName": ((14916, LCID, 4, 0),()),
		"Mileage": ((34100, LCID, 4, 0),()),
		"MobileTelephoneNumber": ((14876, LCID, 4, 0),()),
		"NetMeetingAlias": ((32863, LCID, 4, 0),()),
		"NetMeetingServer": ((32864, LCID, 4, 0),()),
		"NickName": ((14927, LCID, 4, 0),()),
		"NoAging": ((34062, LCID, 4, 0),()),
		"OfficeLocation": ((14873, LCID, 4, 0),()),
		"OrganizationalIDNumber": ((14864, LCID, 4, 0),()),
		"OtherAddress": ((32796, LCID, 4, 0),()),
		"OtherAddressCity": ((14943, LCID, 4, 0),()),
		"OtherAddressCountry": ((14944, LCID, 4, 0),()),
		"OtherAddressPostOfficeBox": ((14948, LCID, 4, 0),()),
		"OtherAddressPostalCode": ((14945, LCID, 4, 0),()),
		"OtherAddressState": ((14946, LCID, 4, 0),()),
		"OtherAddressStreet": ((14947, LCID, 4, 0),()),
		"OtherFaxNumber": ((14883, LCID, 4, 0),()),
		"OtherTelephoneNumber": ((14879, LCID, 4, 0),()),
		"PagerNumber": ((14881, LCID, 4, 0),()),
		"PersonalHomePage": ((14928, LCID, 4, 0),()),
		"PrimaryTelephoneNumber": ((14874, LCID, 4, 0),()),
		"Profession": ((14918, LCID, 4, 0),()),
		"RadioTelephoneNumber": ((14877, LCID, 4, 0),()),
		"ReferredBy": ((14919, LCID, 4, 0),()),
		"ReminderOverrideDefault": ((34076, LCID, 4, 0),()),
		"ReminderPlaySound": ((34078, LCID, 4, 0),()),
		"ReminderSet": ((34051, LCID, 4, 0),()),
		"ReminderSoundFile": ((34079, LCID, 4, 0),()),
		"ReminderTime": ((34050, LCID, 4, 0),()),
		"SelectedMailingAddress": ((32802, LCID, 4, 0),()),
		"Sensitivity": ((54, LCID, 4, 0),()),
		"Spouse": ((14920, LCID, 4, 0),()),
		"Subject": ((55, LCID, 4, 0),()),
		"Suffix": ((14853, LCID, 4, 0),()),
		"TTYTDDTelephoneNumber": ((14923, LCID, 4, 0),()),
		"TaskCompletedDate": ((33039, LCID, 4, 0),()),
		"TaskDueDate": ((33029, LCID, 4, 0),()),
		"TaskStartDate": ((33028, LCID, 4, 0),()),
		"TaskSubject": ((64543, LCID, 4, 0),()),
		"TelexNumber": ((14892, LCID, 4, 0),()),
		"Title": ((14917, LCID, 4, 0),()),
		"ToDoTaskOrdinal": ((34208, LCID, 4, 0),()),
		"UnRead": ((61468, LCID, 4, 0),()),
		"User1": ((32847, LCID, 4, 0),()),
		"User2": ((32848, LCID, 4, 0),()),
		"User3": ((32849, LCID, 4, 0),()),
		"User4": ((32850, LCID, 4, 0),()),
		"UserCertificate": ((32790, LCID, 4, 0),()),
		"WebPage": ((32811, LCID, 4, 0),()),
		"YomiCompanyName": ((32814, LCID, 4, 0),()),
		"YomiFirstName": ((32812, LCID, 4, 0),()),
		"YomiLastName": ((32813, LCID, 4, 0),()),
	}

win32com.client.CLSIDToClass.RegisterCLSID( "{00063021-0000-0000-C000-000000000046}", _ContactItem )
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

_ContactItem_vtables_dispatch_ = 1
_ContactItem_vtables_ = [
	(( u'Application' , u'Application' , ), 61440, (61440, (), [ (16393, 10, None, "IID('{00063001-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 28 , (3, 0, None, None) , 0 , )),
	(( u'Class' , u'Class' , ), 61450, (61450, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 32 , (3, 0, None, None) , 0 , )),
	(( u'Session' , u'Session' , ), 61451, (61451, (), [ (16393, 10, None, "IID('{00063002-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 36 , (3, 0, None, None) , 0 , )),
	(( u'Parent' , u'Parent' , ), 61441, (61441, (), [ (16393, 10, None, None) , ], 1 , 2 , 4 , 0 , 40 , (3, 0, None, None) , 0 , )),
	(( u'Actions' , u'Actions' , ), 63511, (63511, (), [ (16393, 10, None, "IID('{0006303E-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 44 , (3, 0, None, None) , 0 , )),
	(( u'Attachments' , u'Attachments' , ), 63509, (63509, (), [ (16393, 10, None, "IID('{0006303C-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 48 , (3, 0, None, None) , 0 , )),
	(( u'BillingInformation' , u'BillingInformation' , ), 34101, (34101, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 52 , (3, 0, None, None) , 0 , )),
	(( u'BillingInformation' , u'BillingInformation' , ), 34101, (34101, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 56 , (3, 0, None, None) , 0 , )),
	(( u'Body' , u'Body' , ), 37120, (37120, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 60 , (3, 0, None, None) , 0 , )),
	(( u'Body' , u'Body' , ), 37120, (37120, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 64 , (3, 0, None, None) , 0 , )),
	(( u'Categories' , u'Categories' , ), 36865, (36865, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 68 , (3, 0, None, None) , 0 , )),
	(( u'Categories' , u'Categories' , ), 36865, (36865, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 72 , (3, 0, None, None) , 0 , )),
	(( u'Companies' , u'Companies' , ), 34107, (34107, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 76 , (3, 0, None, None) , 0 , )),
	(( u'Companies' , u'Companies' , ), 34107, (34107, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 80 , (3, 0, None, None) , 0 , )),
	(( u'ConversationIndex' , u'ConversationIndex' , ), 64192, (64192, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 84 , (3, 0, None, None) , 0 , )),
	(( u'ConversationTopic' , u'ConversationTopic' , ), 112, (112, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 88 , (3, 0, None, None) , 0 , )),
	(( u'CreationTime' , u'CreationTime' , ), 12295, (12295, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 92 , (3, 0, None, None) , 0 , )),
	(( u'EntryID' , u'EntryID' , ), 61470, (61470, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 96 , (3, 0, None, None) , 0 , )),
	(( u'FormDescription' , u'FormDescription' , ), 61589, (61589, (), [ (16393, 10, None, "IID('{00063046-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 100 , (3, 0, None, None) , 0 , )),
	(( u'GetInspector' , u'GetInspector' , ), 61502, (61502, (), [ (16393, 10, None, "IID('{00063005-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 104 , (3, 0, None, None) , 0 , )),
	(( u'Importance' , u'Importance' , ), 23, (23, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 108 , (3, 0, None, None) , 0 , )),
	(( u'Importance' , u'Importance' , ), 23, (23, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 112 , (3, 0, None, None) , 0 , )),
	(( u'LastModificationTime' , u'LastModificationTime' , ), 12296, (12296, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 116 , (3, 0, None, None) , 0 , )),
	(( u'MAPIOBJECT' , u'MAPIOBJECT' , ), 61696, (61696, (), [ (16397, 10, None, None) , ], 1 , 2 , 4 , 0 , 120 , (3, 0, None, None) , 64 , )),
	(( u'MessageClass' , u'MessageClass' , ), 26, (26, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 124 , (3, 0, None, None) , 0 , )),
	(( u'MessageClass' , u'MessageClass' , ), 26, (26, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 128 , (3, 0, None, None) , 0 , )),
	(( u'Mileage' , u'Mileage' , ), 34100, (34100, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 132 , (3, 0, None, None) , 0 , )),
	(( u'Mileage' , u'Mileage' , ), 34100, (34100, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 136 , (3, 0, None, None) , 0 , )),
	(( u'NoAging' , u'NoAging' , ), 34062, (34062, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 140 , (3, 0, None, None) , 0 , )),
	(( u'NoAging' , u'NoAging' , ), 34062, (34062, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 144 , (3, 0, None, None) , 0 , )),
	(( u'OutlookInternalVersion' , u'OutlookInternalVersion' , ), 34130, (34130, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 148 , (3, 0, None, None) , 0 , )),
	(( u'OutlookVersion' , u'OutlookVersion' , ), 34132, (34132, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 152 , (3, 0, None, None) , 0 , )),
	(( u'Saved' , u'Saved' , ), 61603, (61603, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 156 , (3, 0, None, None) , 0 , )),
	(( u'Sensitivity' , u'Sensitivity' , ), 54, (54, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 160 , (3, 0, None, None) , 0 , )),
	(( u'Sensitivity' , u'Sensitivity' , ), 54, (54, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 164 , (3, 0, None, None) , 0 , )),
	(( u'Size' , u'Size' , ), 3592, (3592, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 168 , (3, 0, None, None) , 0 , )),
	(( u'Subject' , u'Subject' , ), 55, (55, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 172 , (3, 0, None, None) , 0 , )),
	(( u'Subject' , u'Subject' , ), 55, (55, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 176 , (3, 0, None, None) , 0 , )),
	(( u'UnRead' , u'UnRead' , ), 61468, (61468, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 180 , (3, 0, None, None) , 0 , )),
	(( u'UnRead' , u'UnRead' , ), 61468, (61468, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 184 , (3, 0, None, None) , 0 , )),
	(( u'UserProperties' , u'UserProperties' , ), 63510, (63510, (), [ (16393, 10, None, "IID('{0006303D-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 188 , (3, 0, None, None) , 0 , )),
	(( u'Close' , u'SaveMode' , ), 61475, (61475, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 192 , (3, 0, None, None) , 0 , )),
	(( u'Copy' , u'Item' , ), 61490, (61490, (), [ (16393, 10, None, None) , ], 1 , 1 , 4 , 0 , 196 , (3, 0, None, None) , 0 , )),
	(( u'Delete' , ), 61514, (61514, (), [ ], 1 , 1 , 4 , 0 , 200 , (3, 0, None, None) , 0 , )),
	(( u'Display' , u'Modal' , ), 61606, (61606, (), [ (12, 17, None, None) , ], 1 , 1 , 4 , 1 , 204 , (3, 0, None, None) , 0 , )),
	(( u'Move' , u'DestFldr' , u'Item' , ), 61492, (61492, (), [ (9, 1, None, "IID('{00063006-0000-0000-C000-000000000046}')") , 
			(16393, 10, None, None) , ], 1 , 1 , 4 , 0 , 208 , (3, 0, None, None) , 0 , )),
	(( u'PrintOut' , ), 61491, (61491, (), [ ], 1 , 1 , 4 , 0 , 212 , (3, 0, None, None) , 0 , )),
	(( u'Save' , ), 61512, (61512, (), [ ], 1 , 1 , 4 , 0 , 216 , (3, 0, None, None) , 0 , )),
	(( u'SaveAs' , u'Path' , u'Type' , ), 61521, (61521, (), [ (8, 1, None, None) , 
			(12, 17, None, None) , ], 1 , 1 , 4 , 1 , 220 , (3, 0, None, None) , 0 , )),
	(( u'Account' , u'Account' , ), 14848, (14848, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 224 , (3, 0, None, None) , 0 , )),
	(( u'Account' , u'Account' , ), 14848, (14848, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 228 , (3, 0, None, None) , 0 , )),
	(( u'Anniversary' , u'Anniversary' , ), 14913, (14913, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 232 , (3, 0, None, None) , 0 , )),
	(( u'Anniversary' , u'Anniversary' , ), 14913, (14913, (), [ (7, 1, None, None) , ], 1 , 4 , 4 , 0 , 236 , (3, 0, None, None) , 0 , )),
	(( u'AssistantName' , u'AssistantName' , ), 14896, (14896, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 240 , (3, 0, None, None) , 0 , )),
	(( u'AssistantName' , u'AssistantName' , ), 14896, (14896, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 244 , (3, 0, None, None) , 0 , )),
	(( u'AssistantTelephoneNumber' , u'AssistantTelephoneNumber' , ), 14894, (14894, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 248 , (3, 0, None, None) , 0 , )),
	(( u'AssistantTelephoneNumber' , u'AssistantTelephoneNumber' , ), 14894, (14894, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 252 , (3, 0, None, None) , 0 , )),
	(( u'Birthday' , u'Birthday' , ), 14914, (14914, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 256 , (3, 0, None, None) , 0 , )),
	(( u'Birthday' , u'Birthday' , ), 14914, (14914, (), [ (7, 1, None, None) , ], 1 , 4 , 4 , 0 , 260 , (3, 0, None, None) , 0 , )),
	(( u'Business2TelephoneNumber' , u'Business2TelephoneNumber' , ), 14875, (14875, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 264 , (3, 0, None, None) , 0 , )),
	(( u'Business2TelephoneNumber' , u'Business2TelephoneNumber' , ), 14875, (14875, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 268 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddress' , u'BusinessAddress' , ), 32795, (32795, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 272 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddress' , u'BusinessAddress' , ), 32795, (32795, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 276 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddressCity' , u'BusinessAddressCity' , ), 32838, (32838, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 280 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddressCity' , u'BusinessAddressCity' , ), 32838, (32838, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 284 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddressCountry' , u'BusinessAddressCountry' , ), 32841, (32841, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 288 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddressCountry' , u'BusinessAddressCountry' , ), 32841, (32841, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 292 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddressPostalCode' , u'BusinessAddressPostalCode' , ), 32840, (32840, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 296 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddressPostalCode' , u'BusinessAddressPostalCode' , ), 32840, (32840, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 300 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddressPostOfficeBox' , u'BusinessAddressPostOfficeBox' , ), 32842, (32842, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 304 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddressPostOfficeBox' , u'BusinessAddressPostOfficeBox' , ), 32842, (32842, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 308 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddressState' , u'BusinessAddressState' , ), 32839, (32839, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 312 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddressState' , u'BusinessAddressState' , ), 32839, (32839, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 316 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddressStreet' , u'BusinessAddressStreet' , ), 32837, (32837, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 320 , (3, 0, None, None) , 0 , )),
	(( u'BusinessAddressStreet' , u'BusinessAddressStreet' , ), 32837, (32837, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 324 , (3, 0, None, None) , 0 , )),
	(( u'BusinessFaxNumber' , u'BusinessFaxNumber' , ), 14884, (14884, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 328 , (3, 0, None, None) , 0 , )),
	(( u'BusinessFaxNumber' , u'BusinessFaxNumber' , ), 14884, (14884, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 332 , (3, 0, None, None) , 0 , )),
	(( u'BusinessHomePage' , u'BusinessHomePage' , ), 14929, (14929, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 336 , (3, 0, None, None) , 0 , )),
	(( u'BusinessHomePage' , u'BusinessHomePage' , ), 14929, (14929, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 340 , (3, 0, None, None) , 0 , )),
	(( u'BusinessTelephoneNumber' , u'BusinessTelephoneNumber' , ), 14856, (14856, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 344 , (3, 0, None, None) , 0 , )),
	(( u'BusinessTelephoneNumber' , u'BusinessTelephoneNumber' , ), 14856, (14856, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 348 , (3, 0, None, None) , 0 , )),
	(( u'CallbackTelephoneNumber' , u'CallbackTelephoneNumber' , ), 14850, (14850, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 352 , (3, 0, None, None) , 0 , )),
	(( u'CallbackTelephoneNumber' , u'CallbackTelephoneNumber' , ), 14850, (14850, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 356 , (3, 0, None, None) , 0 , )),
	(( u'CarTelephoneNumber' , u'CarTelephoneNumber' , ), 14878, (14878, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 360 , (3, 0, None, None) , 0 , )),
	(( u'CarTelephoneNumber' , u'CarTelephoneNumber' , ), 14878, (14878, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 364 , (3, 0, None, None) , 0 , )),
	(( u'Children' , u'Children' , ), 32780, (32780, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 368 , (3, 0, None, None) , 0 , )),
	(( u'Children' , u'Children' , ), 32780, (32780, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 372 , (3, 0, None, None) , 0 , )),
	(( u'CompanyAndFullName' , u'CompanyAndFullName' , ), 32792, (32792, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 376 , (3, 0, None, None) , 0 , )),
	(( u'CompanyLastFirstNoSpace' , u'CompanyLastFirstNoSpace' , ), 32818, (32818, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 380 , (3, 0, None, None) , 0 , )),
	(( u'CompanyLastFirstSpaceOnly' , u'CompanyLastFirstSpaceOnly' , ), 32819, (32819, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 384 , (3, 0, None, None) , 0 , )),
	(( u'CompanyMainTelephoneNumber' , u'CompanyMainTelephoneNumber' , ), 14935, (14935, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 388 , (3, 0, None, None) , 0 , )),
	(( u'CompanyMainTelephoneNumber' , u'CompanyMainTelephoneNumber' , ), 14935, (14935, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 392 , (3, 0, None, None) , 0 , )),
	(( u'CompanyName' , u'CompanyName' , ), 14870, (14870, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 396 , (3, 0, None, None) , 0 , )),
	(( u'CompanyName' , u'CompanyName' , ), 14870, (14870, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 400 , (3, 0, None, None) , 0 , )),
	(( u'ComputerNetworkName' , u'ComputerNetworkName' , ), 14921, (14921, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 404 , (3, 0, None, None) , 0 , )),
	(( u'ComputerNetworkName' , u'ComputerNetworkName' , ), 14921, (14921, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 408 , (3, 0, None, None) , 0 , )),
	(( u'CustomerID' , u'CustomerID' , ), 14922, (14922, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 412 , (3, 0, None, None) , 0 , )),
	(( u'CustomerID' , u'CustomerID' , ), 14922, (14922, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 416 , (3, 0, None, None) , 0 , )),
	(( u'Department' , u'Department' , ), 14872, (14872, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 420 , (3, 0, None, None) , 0 , )),
	(( u'Department' , u'Department' , ), 14872, (14872, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 424 , (3, 0, None, None) , 0 , )),
	(( u'Email1Address' , u'Email1Address' , ), 32899, (32899, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 428 , (3, 0, None, None) , 0 , )),
	(( u'Email1Address' , u'Email1Address' , ), 32899, (32899, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 432 , (3, 0, None, None) , 0 , )),
	(( u'Email1AddressType' , u'Email1AddressType' , ), 32898, (32898, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 436 , (3, 0, None, None) , 0 , )),
	(( u'Email1AddressType' , u'Email1AddressType' , ), 32898, (32898, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 440 , (3, 0, None, None) , 0 , )),
	(( u'Email1DisplayName' , u'Email1DisplayName' , ), 32896, (32896, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 444 , (3, 0, None, None) , 0 , )),
	(( u'Email1EntryID' , u'Email1EntryID' , ), 32901, (32901, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 448 , (3, 0, None, None) , 0 , )),
	(( u'Email2Address' , u'Email2Address' , ), 32915, (32915, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 452 , (3, 0, None, None) , 0 , )),
	(( u'Email2Address' , u'Email2Address' , ), 32915, (32915, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 456 , (3, 0, None, None) , 0 , )),
	(( u'Email2AddressType' , u'Email2AddressType' , ), 32914, (32914, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 460 , (3, 0, None, None) , 0 , )),
	(( u'Email2AddressType' , u'Email2AddressType' , ), 32914, (32914, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 464 , (3, 0, None, None) , 0 , )),
	(( u'Email2DisplayName' , u'Email2DisplayName' , ), 32912, (32912, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 468 , (3, 0, None, None) , 0 , )),
	(( u'Email2EntryID' , u'Email2EntryID' , ), 32917, (32917, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 472 , (3, 0, None, None) , 0 , )),
	(( u'Email3Address' , u'Email3Address' , ), 32931, (32931, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 476 , (3, 0, None, None) , 0 , )),
	(( u'Email3Address' , u'Email3Address' , ), 32931, (32931, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 480 , (3, 0, None, None) , 0 , )),
	(( u'Email3AddressType' , u'Email3AddressType' , ), 32930, (32930, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 484 , (3, 0, None, None) , 0 , )),
	(( u'Email3AddressType' , u'Email3AddressType' , ), 32930, (32930, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 488 , (3, 0, None, None) , 0 , )),
	(( u'Email3DisplayName' , u'Email3DisplayName' , ), 32928, (32928, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 492 , (3, 0, None, None) , 0 , )),
	(( u'Email3EntryID' , u'Email3EntryID' , ), 32933, (32933, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 496 , (3, 0, None, None) , 0 , )),
	(( u'FileAs' , u'FileAs' , ), 32773, (32773, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 500 , (3, 0, None, None) , 0 , )),
	(( u'FileAs' , u'FileAs' , ), 32773, (32773, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 504 , (3, 0, None, None) , 0 , )),
	(( u'FirstName' , u'FirstName' , ), 14854, (14854, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 508 , (3, 0, None, None) , 0 , )),
	(( u'FirstName' , u'FirstName' , ), 14854, (14854, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 512 , (3, 0, None, None) , 0 , )),
	(( u'FTPSite' , u'FTPSite' , ), 14924, (14924, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 516 , (3, 0, None, None) , 0 , )),
	(( u'FTPSite' , u'FTPSite' , ), 14924, (14924, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 520 , (3, 0, None, None) , 0 , )),
	(( u'FullName' , u'FullName' , ), 12289, (12289, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 524 , (3, 0, None, None) , 0 , )),
	(( u'FullName' , u'FullName' , ), 12289, (12289, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 528 , (3, 0, None, None) , 0 , )),
	(( u'FullNameAndCompany' , u'FullNameAndCompany' , ), 32793, (32793, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 532 , (3, 0, None, None) , 0 , )),
	(( u'Gender' , u'Gender' , ), 14925, (14925, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 536 , (3, 0, None, None) , 0 , )),
	(( u'Gender' , u'Gender' , ), 14925, (14925, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 540 , (3, 0, None, None) , 0 , )),
	(( u'GovernmentIDNumber' , u'GovernmentIDNumber' , ), 14855, (14855, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 544 , (3, 0, None, None) , 0 , )),
	(( u'GovernmentIDNumber' , u'GovernmentIDNumber' , ), 14855, (14855, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 548 , (3, 0, None, None) , 0 , )),
	(( u'Hobby' , u'Hobby' , ), 14915, (14915, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 552 , (3, 0, None, None) , 0 , )),
	(( u'Hobby' , u'Hobby' , ), 14915, (14915, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 556 , (3, 0, None, None) , 0 , )),
	(( u'Home2TelephoneNumber' , u'Home2TelephoneNumber' , ), 14895, (14895, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 560 , (3, 0, None, None) , 0 , )),
	(( u'Home2TelephoneNumber' , u'Home2TelephoneNumber' , ), 14895, (14895, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 564 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddress' , u'HomeAddress' , ), 32794, (32794, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 568 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddress' , u'HomeAddress' , ), 32794, (32794, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 572 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddressCity' , u'HomeAddressCity' , ), 14937, (14937, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 576 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddressCity' , u'HomeAddressCity' , ), 14937, (14937, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 580 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddressCountry' , u'HomeAddressCountry' , ), 14938, (14938, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 584 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddressCountry' , u'HomeAddressCountry' , ), 14938, (14938, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 588 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddressPostalCode' , u'HomeAddressPostalCode' , ), 14939, (14939, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 592 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddressPostalCode' , u'HomeAddressPostalCode' , ), 14939, (14939, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 596 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddressPostOfficeBox' , u'HomeAddressPostOfficeBox' , ), 14942, (14942, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 600 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddressPostOfficeBox' , u'HomeAddressPostOfficeBox' , ), 14942, (14942, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 604 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddressState' , u'HomeAddressState' , ), 14940, (14940, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 608 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddressState' , u'HomeAddressState' , ), 14940, (14940, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 612 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddressStreet' , u'HomeAddressStreet' , ), 14941, (14941, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 616 , (3, 0, None, None) , 0 , )),
	(( u'HomeAddressStreet' , u'HomeAddressStreet' , ), 14941, (14941, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 620 , (3, 0, None, None) , 0 , )),
	(( u'HomeFaxNumber' , u'HomeFaxNumber' , ), 14885, (14885, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 624 , (3, 0, None, None) , 0 , )),
	(( u'HomeFaxNumber' , u'HomeFaxNumber' , ), 14885, (14885, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 628 , (3, 0, None, None) , 0 , )),
	(( u'HomeTelephoneNumber' , u'HomeTelephoneNumber' , ), 14857, (14857, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 632 , (3, 0, None, None) , 0 , )),
	(( u'HomeTelephoneNumber' , u'HomeTelephoneNumber' , ), 14857, (14857, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 636 , (3, 0, None, None) , 0 , )),
	(( u'Initials' , u'Initials' , ), 14858, (14858, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 640 , (3, 0, None, None) , 0 , )),
	(( u'Initials' , u'Initials' , ), 14858, (14858, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 644 , (3, 0, None, None) , 0 , )),
	(( u'InternetFreeBusyAddress' , u'InternetFreeBusyAddress' , ), 32984, (32984, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 648 , (3, 0, None, None) , 0 , )),
	(( u'InternetFreeBusyAddress' , u'InternetFreeBusyAddress' , ), 32984, (32984, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 652 , (3, 0, None, None) , 0 , )),
	(( u'ISDNNumber' , u'ISDNNumber' , ), 14893, (14893, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 656 , (3, 0, None, None) , 0 , )),
	(( u'ISDNNumber' , u'ISDNNumber' , ), 14893, (14893, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 660 , (3, 0, None, None) , 0 , )),
	(( u'JobTitle' , u'JobTitle' , ), 14871, (14871, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 664 , (3, 0, None, None) , 0 , )),
	(( u'JobTitle' , u'JobTitle' , ), 14871, (14871, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 668 , (3, 0, None, None) , 0 , )),
	(( u'Journal' , u'Journal' , ), 32805, (32805, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 672 , (3, 0, None, None) , 0 , )),
	(( u'Journal' , u'Journal' , ), 32805, (32805, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 676 , (3, 0, None, None) , 0 , )),
	(( u'Language' , u'Language' , ), 14860, (14860, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 680 , (3, 0, None, None) , 0 , )),
	(( u'Language' , u'Language' , ), 14860, (14860, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 684 , (3, 0, None, None) , 0 , )),
	(( u'LastFirstAndSuffix' , u'LastFirstAndSuffix' , ), 32822, (32822, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 688 , (3, 0, None, None) , 0 , )),
	(( u'LastFirstNoSpace' , u'LastFirstNoSpace' , ), 32816, (32816, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 692 , (3, 0, None, None) , 0 , )),
	(( u'LastFirstNoSpaceCompany' , u'LastFirstNoSpaceCompany' , ), 32820, (32820, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 696 , (3, 0, None, None) , 0 , )),
	(( u'LastFirstSpaceOnly' , u'LastFirstSpaceOnly' , ), 32817, (32817, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 700 , (3, 0, None, None) , 0 , )),
	(( u'LastFirstSpaceOnlyCompany' , u'LastFirstSpaceOnlyCompany' , ), 32821, (32821, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 704 , (3, 0, None, None) , 0 , )),
	(( u'LastName' , u'LastName' , ), 14865, (14865, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 708 , (3, 0, None, None) , 0 , )),
	(( u'LastName' , u'LastName' , ), 14865, (14865, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 712 , (3, 0, None, None) , 0 , )),
	(( u'LastNameAndFirstName' , u'LastNameAndFirstName' , ), 32791, (32791, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 716 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddress' , u'MailingAddress' , ), 14869, (14869, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 720 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddress' , u'MailingAddress' , ), 14869, (14869, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 724 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddressCity' , u'MailingAddressCity' , ), 14887, (14887, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 728 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddressCity' , u'MailingAddressCity' , ), 14887, (14887, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 732 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddressCountry' , u'MailingAddressCountry' , ), 14886, (14886, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 736 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddressCountry' , u'MailingAddressCountry' , ), 14886, (14886, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 740 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddressPostalCode' , u'MailingAddressPostalCode' , ), 14890, (14890, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 744 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddressPostalCode' , u'MailingAddressPostalCode' , ), 14890, (14890, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 748 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddressPostOfficeBox' , u'MailingAddressPostOfficeBox' , ), 14891, (14891, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 752 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddressPostOfficeBox' , u'MailingAddressPostOfficeBox' , ), 14891, (14891, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 756 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddressState' , u'MailingAddressState' , ), 14888, (14888, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 760 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddressState' , u'MailingAddressState' , ), 14888, (14888, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 764 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddressStreet' , u'MailingAddressStreet' , ), 14889, (14889, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 768 , (3, 0, None, None) , 0 , )),
	(( u'MailingAddressStreet' , u'MailingAddressStreet' , ), 14889, (14889, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 772 , (3, 0, None, None) , 0 , )),
	(( u'ManagerName' , u'ManagerName' , ), 14926, (14926, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 776 , (3, 0, None, None) , 0 , )),
	(( u'ManagerName' , u'ManagerName' , ), 14926, (14926, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 780 , (3, 0, None, None) , 0 , )),
	(( u'MiddleName' , u'MiddleName' , ), 14916, (14916, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 784 , (3, 0, None, None) , 0 , )),
	(( u'MiddleName' , u'MiddleName' , ), 14916, (14916, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 788 , (3, 0, None, None) , 0 , )),
	(( u'MobileTelephoneNumber' , u'MobileTelephoneNumber' , ), 14876, (14876, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 792 , (3, 0, None, None) , 0 , )),
	(( u'MobileTelephoneNumber' , u'MobileTelephoneNumber' , ), 14876, (14876, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 796 , (3, 0, None, None) , 0 , )),
	(( u'NetMeetingAlias' , u'NetMeetingAlias' , ), 32863, (32863, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 800 , (3, 0, None, None) , 0 , )),
	(( u'NetMeetingAlias' , u'NetMeetingAlias' , ), 32863, (32863, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 804 , (3, 0, None, None) , 0 , )),
	(( u'NetMeetingServer' , u'NetMeetingServer' , ), 32864, (32864, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 808 , (3, 0, None, None) , 0 , )),
	(( u'NetMeetingServer' , u'NetMeetingServer' , ), 32864, (32864, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 812 , (3, 0, None, None) , 0 , )),
	(( u'NickName' , u'NickName' , ), 14927, (14927, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 816 , (3, 0, None, None) , 0 , )),
	(( u'NickName' , u'NickName' , ), 14927, (14927, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 820 , (3, 0, None, None) , 0 , )),
	(( u'OfficeLocation' , u'OfficeLocation' , ), 14873, (14873, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 824 , (3, 0, None, None) , 0 , )),
	(( u'OfficeLocation' , u'OfficeLocation' , ), 14873, (14873, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 828 , (3, 0, None, None) , 0 , )),
	(( u'OrganizationalIDNumber' , u'OrganizationalIDNumber' , ), 14864, (14864, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 832 , (3, 0, None, None) , 0 , )),
	(( u'OrganizationalIDNumber' , u'OrganizationalIDNumber' , ), 14864, (14864, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 836 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddress' , u'OtherAddress' , ), 32796, (32796, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 840 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddress' , u'OtherAddress' , ), 32796, (32796, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 844 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddressCity' , u'OtherAddressCity' , ), 14943, (14943, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 848 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddressCity' , u'OtherAddressCity' , ), 14943, (14943, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 852 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddressCountry' , u'OtherAddressCountry' , ), 14944, (14944, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 856 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddressCountry' , u'OtherAddressCountry' , ), 14944, (14944, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 860 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddressPostalCode' , u'OtherAddressPostalCode' , ), 14945, (14945, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 864 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddressPostalCode' , u'OtherAddressPostalCode' , ), 14945, (14945, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 868 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddressPostOfficeBox' , u'OtherAddressPostOfficeBox' , ), 14948, (14948, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 872 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddressPostOfficeBox' , u'OtherAddressPostOfficeBox' , ), 14948, (14948, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 876 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddressState' , u'OtherAddressState' , ), 14946, (14946, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 880 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddressState' , u'OtherAddressState' , ), 14946, (14946, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 884 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddressStreet' , u'OtherAddressStreet' , ), 14947, (14947, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 888 , (3, 0, None, None) , 0 , )),
	(( u'OtherAddressStreet' , u'OtherAddressStreet' , ), 14947, (14947, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 892 , (3, 0, None, None) , 0 , )),
	(( u'OtherFaxNumber' , u'OtherFaxNumber' , ), 14883, (14883, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 896 , (3, 0, None, None) , 0 , )),
	(( u'OtherFaxNumber' , u'OtherFaxNumber' , ), 14883, (14883, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 900 , (3, 0, None, None) , 0 , )),
	(( u'OtherTelephoneNumber' , u'OtherTelephoneNumber' , ), 14879, (14879, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 904 , (3, 0, None, None) , 0 , )),
	(( u'OtherTelephoneNumber' , u'OtherTelephoneNumber' , ), 14879, (14879, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 908 , (3, 0, None, None) , 0 , )),
	(( u'PagerNumber' , u'PagerNumber' , ), 14881, (14881, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 912 , (3, 0, None, None) , 0 , )),
	(( u'PagerNumber' , u'PagerNumber' , ), 14881, (14881, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 916 , (3, 0, None, None) , 0 , )),
	(( u'PersonalHomePage' , u'PersonalHomePage' , ), 14928, (14928, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 920 , (3, 0, None, None) , 0 , )),
	(( u'PersonalHomePage' , u'PersonalHomePage' , ), 14928, (14928, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 924 , (3, 0, None, None) , 0 , )),
	(( u'PrimaryTelephoneNumber' , u'PrimaryTelephoneNumber' , ), 14874, (14874, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 928 , (3, 0, None, None) , 0 , )),
	(( u'PrimaryTelephoneNumber' , u'PrimaryTelephoneNumber' , ), 14874, (14874, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 932 , (3, 0, None, None) , 0 , )),
	(( u'Profession' , u'Profession' , ), 14918, (14918, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 936 , (3, 0, None, None) , 0 , )),
	(( u'Profession' , u'Profession' , ), 14918, (14918, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 940 , (3, 0, None, None) , 0 , )),
	(( u'RadioTelephoneNumber' , u'RadioTelephoneNumber' , ), 14877, (14877, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 944 , (3, 0, None, None) , 0 , )),
	(( u'RadioTelephoneNumber' , u'RadioTelephoneNumber' , ), 14877, (14877, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 948 , (3, 0, None, None) , 0 , )),
	(( u'ReferredBy' , u'ReferredBy' , ), 14919, (14919, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 952 , (3, 0, None, None) , 0 , )),
	(( u'ReferredBy' , u'ReferredBy' , ), 14919, (14919, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 956 , (3, 0, None, None) , 0 , )),
	(( u'SelectedMailingAddress' , u'SelectedMailingAddress' , ), 32802, (32802, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 960 , (3, 0, None, None) , 0 , )),
	(( u'SelectedMailingAddress' , u'SelectedMailingAddress' , ), 32802, (32802, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 964 , (3, 0, None, None) , 0 , )),
	(( u'Spouse' , u'Spouse' , ), 14920, (14920, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 968 , (3, 0, None, None) , 0 , )),
	(( u'Spouse' , u'Spouse' , ), 14920, (14920, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 972 , (3, 0, None, None) , 0 , )),
	(( u'Suffix' , u'Suffix' , ), 14853, (14853, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 976 , (3, 0, None, None) , 0 , )),
	(( u'Suffix' , u'Suffix' , ), 14853, (14853, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 980 , (3, 0, None, None) , 0 , )),
	(( u'TelexNumber' , u'TelexNumber' , ), 14892, (14892, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 984 , (3, 0, None, None) , 0 , )),
	(( u'TelexNumber' , u'TelexNumber' , ), 14892, (14892, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 988 , (3, 0, None, None) , 0 , )),
	(( u'Title' , u'Title' , ), 14917, (14917, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 992 , (3, 0, None, None) , 0 , )),
	(( u'Title' , u'Title' , ), 14917, (14917, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 996 , (3, 0, None, None) , 0 , )),
	(( u'TTYTDDTelephoneNumber' , u'TTYTDDTelephoneNumber' , ), 14923, (14923, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1000 , (3, 0, None, None) , 0 , )),
	(( u'TTYTDDTelephoneNumber' , u'TTYTDDTelephoneNumber' , ), 14923, (14923, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1004 , (3, 0, None, None) , 0 , )),
	(( u'User1' , u'User1' , ), 32847, (32847, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1008 , (3, 0, None, None) , 0 , )),
	(( u'User1' , u'User1' , ), 32847, (32847, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1012 , (3, 0, None, None) , 0 , )),
	(( u'User2' , u'User2' , ), 32848, (32848, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1016 , (3, 0, None, None) , 0 , )),
	(( u'User2' , u'User2' , ), 32848, (32848, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1020 , (3, 0, None, None) , 0 , )),
	(( u'User3' , u'User3' , ), 32849, (32849, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1024 , (3, 0, None, None) , 0 , )),
	(( u'User3' , u'User3' , ), 32849, (32849, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1028 , (3, 0, None, None) , 0 , )),
	(( u'User4' , u'User4' , ), 32850, (32850, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1032 , (3, 0, None, None) , 0 , )),
	(( u'User4' , u'User4' , ), 32850, (32850, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1036 , (3, 0, None, None) , 0 , )),
	(( u'UserCertificate' , u'UserCertificate' , ), 32790, (32790, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1040 , (3, 0, None, None) , 64 , )),
	(( u'UserCertificate' , u'UserCertificate' , ), 32790, (32790, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1044 , (3, 0, None, None) , 64 , )),
	(( u'WebPage' , u'WebPage' , ), 32811, (32811, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1048 , (3, 0, None, None) , 0 , )),
	(( u'WebPage' , u'WebPage' , ), 32811, (32811, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1052 , (3, 0, None, None) , 0 , )),
	(( u'YomiCompanyName' , u'YomiCompanyName' , ), 32814, (32814, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1056 , (3, 0, None, None) , 0 , )),
	(( u'YomiCompanyName' , u'YomiCompanyName' , ), 32814, (32814, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1060 , (3, 0, None, None) , 0 , )),
	(( u'YomiFirstName' , u'YomiFirstName' , ), 32812, (32812, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1064 , (3, 0, None, None) , 0 , )),
	(( u'YomiFirstName' , u'YomiFirstName' , ), 32812, (32812, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1068 , (3, 0, None, None) , 0 , )),
	(( u'YomiLastName' , u'YomiLastName' , ), 32813, (32813, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1072 , (3, 0, None, None) , 0 , )),
	(( u'YomiLastName' , u'YomiLastName' , ), 32813, (32813, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1076 , (3, 0, None, None) , 0 , )),
	(( u'ForwardAsVcard' , u'Item' , ), 63649, (63649, (), [ (16397, 10, None, "IID('{00061033-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 1080 , (3, 0, None, None) , 0 , )),
	(( u'Links' , u'Links' , ), 62469, (62469, (), [ (16393, 10, None, "IID('{0006308A-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 1084 , (3, 0, None, None) , 0 , )),
	(( u'ItemProperties' , u'ItemProperties' , ), 64009, (64009, (), [ (16393, 10, None, "IID('{000630A8-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 1088 , (3, 0, None, None) , 0 , )),
	(( u'LastFirstNoSpaceAndSuffix' , u'LastFirstNoSpaceAndSuffix' , ), 32824, (32824, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1092 , (3, 0, None, None) , 0 , )),
	(( u'DownloadState' , u'DownloadState' , ), 64077, (64077, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 1096 , (3, 0, None, None) , 0 , )),
	(( u'ShowCategoriesDialog' , ), 64011, (64011, (), [ ], 1 , 1 , 4 , 0 , 1100 , (3, 0, None, None) , 0 , )),
	(( u'IMAddress' , u'IMAddress' , ), 32866, (32866, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1104 , (3, 0, None, None) , 0 , )),
	(( u'IMAddress' , u'IMAddress' , ), 32866, (32866, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1108 , (3, 0, None, None) , 0 , )),
	(( u'MarkForDownload' , u'MarkForDownload' , ), 34161, (34161, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 1112 , (3, 0, None, None) , 0 , )),
	(( u'MarkForDownload' , u'MarkForDownload' , ), 34161, (34161, (), [ (3, 1, None, None) , ], 1 , 4 , 4 , 0 , 1116 , (3, 0, None, None) , 0 , )),
	(( u'Email1DisplayName' , u'Email1DisplayName' , ), 32896, (32896, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1120 , (3, 0, None, None) , 0 , )),
	(( u'Email2DisplayName' , u'Email2DisplayName' , ), 32912, (32912, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1124 , (3, 0, None, None) , 0 , )),
	(( u'Email3DisplayName' , u'Email3DisplayName' , ), 32928, (32928, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1128 , (3, 0, None, None) , 0 , )),
	(( u'IsConflict' , u'IsConflict' , ), 64164, (64164, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 1132 , (3, 0, None, None) , 0 , )),
	(( u'AutoResolvedWinner' , u'AutoResolvedWinner' , ), 64186, (64186, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 1136 , (3, 0, None, None) , 0 , )),
	(( u'Conflicts' , u'Conflicts' , ), 64187, (64187, (), [ (16393, 10, None, "IID('{000630C2-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 1140 , (3, 0, None, None) , 0 , )),
	(( u'AddPicture' , u'Path' , ), 64189, (64189, (), [ (8, 1, None, None) , ], 1 , 1 , 4 , 0 , 1144 , (3, 0, None, None) , 0 , )),
	(( u'RemovePicture' , ), 64190, (64190, (), [ ], 1 , 1 , 4 , 0 , 1148 , (3, 0, None, None) , 0 , )),
	(( u'HasPicture' , u'HasPicture' , ), 64191, (64191, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 1152 , (3, 0, None, None) , 0 , )),
	(( u'PropertyAccessor' , u'PropertyAccessor' , ), 64253, (64253, (), [ (16397, 10, None, "IID('{0006102D-0000-0000-C000-000000000046}')") , ], 1 , 2 , 4 , 0 , 1156 , (3, 0, None, None) , 0 , )),
	(( u'ForwardAsBusinessCard' , u'Item' , ), 64404, (64404, (), [ (16397, 10, None, "IID('{00061033-0000-0000-C000-000000000046}')") , ], 1 , 1 , 4 , 0 , 1160 , (3, 0, None, None) , 0 , )),
	(( u'ShowBusinessCardEditor' , ), 64405, (64405, (), [ ], 1 , 1 , 4 , 0 , 1164 , (3, 0, None, None) , 0 , )),
	(( u'SaveBusinessCardImage' , u'Path' , ), 64407, (64407, (), [ (8, 1, None, None) , ], 1 , 1 , 4 , 0 , 1168 , (3, 0, None, None) , 0 , )),
	(( u'ShowCheckPhoneDialog' , u'PhoneNumber' , ), 64471, (64471, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 1172 , (3, 0, None, None) , 0 , )),
	(( u'TaskSubject' , u'TaskSubject' , ), 64543, (64543, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1176 , (3, 0, None, None) , 0 , )),
	(( u'TaskSubject' , u'TaskSubject' , ), 64543, (64543, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1180 , (3, 0, None, None) , 0 , )),
	(( u'TaskDueDate' , u'TaskDueDate' , ), 33029, (33029, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 1184 , (3, 0, None, None) , 0 , )),
	(( u'TaskDueDate' , u'TaskDueDate' , ), 33029, (33029, (), [ (7, 1, None, None) , ], 1 , 4 , 4 , 0 , 1188 , (3, 0, None, None) , 0 , )),
	(( u'TaskStartDate' , u'TaskStartDate' , ), 33028, (33028, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 1192 , (3, 0, None, None) , 0 , )),
	(( u'TaskStartDate' , u'TaskStartDate' , ), 33028, (33028, (), [ (7, 1, None, None) , ], 1 , 4 , 4 , 0 , 1196 , (3, 0, None, None) , 0 , )),
	(( u'TaskCompletedDate' , u'TaskCompletedDate' , ), 33039, (33039, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 1200 , (3, 0, None, None) , 0 , )),
	(( u'TaskCompletedDate' , u'TaskCompletedDate' , ), 33039, (33039, (), [ (7, 1, None, None) , ], 1 , 4 , 4 , 0 , 1204 , (3, 0, None, None) , 0 , )),
	(( u'ToDoTaskOrdinal' , u'ToDoTaskOrdinal' , ), 34208, (34208, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 1208 , (3, 0, None, None) , 0 , )),
	(( u'ToDoTaskOrdinal' , u'ToDoTaskOrdinal' , ), 34208, (34208, (), [ (7, 1, None, None) , ], 1 , 4 , 4 , 0 , 1212 , (3, 0, None, None) , 0 , )),
	(( u'ReminderOverrideDefault' , u'ReminderOverrideDefault' , ), 34076, (34076, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 1216 , (3, 0, None, None) , 0 , )),
	(( u'ReminderOverrideDefault' , u'ReminderOverrideDefault' , ), 34076, (34076, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 1220 , (3, 0, None, None) , 0 , )),
	(( u'ReminderPlaySound' , u'ReminderPlaySound' , ), 34078, (34078, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 1224 , (3, 0, None, None) , 0 , )),
	(( u'ReminderPlaySound' , u'ReminderPlaySound' , ), 34078, (34078, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 1228 , (3, 0, None, None) , 0 , )),
	(( u'ReminderSet' , u'ReminderSet' , ), 34051, (34051, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 1232 , (3, 0, None, None) , 0 , )),
	(( u'ReminderSet' , u'ReminderSet' , ), 34051, (34051, (), [ (11, 1, None, None) , ], 1 , 4 , 4 , 0 , 1236 , (3, 0, None, None) , 0 , )),
	(( u'ReminderSoundFile' , u'ReminderSoundFile' , ), 34079, (34079, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1240 , (3, 0, None, None) , 0 , )),
	(( u'ReminderSoundFile' , u'ReminderSoundFile' , ), 34079, (34079, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1244 , (3, 0, None, None) , 0 , )),
	(( u'ReminderTime' , u'ReminderTime' , ), 34050, (34050, (), [ (16391, 10, None, None) , ], 1 , 2 , 4 , 0 , 1248 , (3, 0, None, None) , 0 , )),
	(( u'ReminderTime' , u'ReminderTime' , ), 34050, (34050, (), [ (7, 1, None, None) , ], 1 , 4 , 4 , 0 , 1252 , (3, 0, None, None) , 0 , )),
	(( u'MarkAsTask' , u'MarkInterval' , ), 64510, (64510, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 1256 , (3, 0, None, None) , 0 , )),
	(( u'ClearTaskFlag' , ), 64521, (64521, (), [ ], 1 , 1 , 4 , 0 , 1260 , (3, 0, None, None) , 0 , )),
	(( u'IsMarkedAsTask' , u'IsMarkedAsTask' , ), 64522, (64522, (), [ (16395, 10, None, None) , ], 1 , 2 , 4 , 0 , 1264 , (3, 0, None, None) , 0 , )),
	(( u'BusinessCardLayoutXml' , u'BusinessCardLayoutXml' , ), 64525, (64525, (), [ (16392, 10, None, None) , ], 1 , 2 , 4 , 0 , 1268 , (3, 0, None, None) , 0 , )),
	(( u'BusinessCardLayoutXml' , u'BusinessCardLayoutXml' , ), 64525, (64525, (), [ (8, 1, None, None) , ], 1 , 4 , 4 , 0 , 1272 , (3, 0, None, None) , 0 , )),
	(( u'ResetBusinessCard' , ), 64526, (64526, (), [ ], 1 , 1 , 4 , 0 , 1276 , (3, 0, None, None) , 0 , )),
	(( u'AddBusinessCardLogoPicture' , u'Path' , ), 64527, (64527, (), [ (8, 1, None, None) , ], 1 , 1 , 4 , 0 , 1280 , (3, 0, None, None) , 0 , )),
	(( u'BusinessCardType' , u'BusinessCardType' , ), 64528, (64528, (), [ (16387, 10, None, None) , ], 1 , 2 , 4 , 0 , 1284 , (3, 0, None, None) , 0 , )),
]

win32com.client.CLSIDToClass.RegisterCLSID( "{00063021-0000-0000-C000-000000000046}", _ContactItem )
