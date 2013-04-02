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
import stat
import os

class RequestDataFile(RequestData):

    def __init__(self, fname, content_type):

        # Cache file name
        self.fname = fname

        # Determine size of stream
        self.content_length = os.stat(self.fname)[stat.ST_SIZE]

        self.content_type = content_type


    def start(self):
        # Create an input file stream
        self.stream = open(self.fname, "r")


    def stop(self):
        self.stream.close()
        self.stream = None


    def read(self):
        data = self.stream.read(8192)
        if data:
            return data, True
        else:
            return data, False



class ResponseDataFile(ResponseData):

    def __init__(self, fname):
        self.fname = fname


    def start(self):
        # Create an input file stream
        self.stream = open(self.fname, "w")


    def stop(self):
        self.stream.close()
        self.stream = None


    def write(self, data):
        self.stream.write(data)


    def clear(self):
        # Throw out existing data and start from scratch
        self.stop()
        self.start()
