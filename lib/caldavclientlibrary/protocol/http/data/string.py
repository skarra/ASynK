##
# Copyright (c) 2006-2007 Apple Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##

from caldavclientlibrary.protocol.http.data.data import ResponseData
from caldavclientlibrary.protocol.http.data.data import RequestData
from StringIO import StringIO

class RequestDataString(RequestData):

    def __init__(self, text, content_type):

        # Cache file name
        self.text = text

        # Determine size of stream
        self.content_length = len(text)

        self.content_type = content_type


    def read(self):
        return self.text, False



class ResponseDataString(ResponseData):

    def __init__(self):
        self.stream = StringIO()


    def getData(self):
        return self.stream.getvalue()


    def write(self, data):
        self.stream.write(data)


    def clear(self):
        # Throw out existing data and start from scratch
        self.stream = StringIO()
