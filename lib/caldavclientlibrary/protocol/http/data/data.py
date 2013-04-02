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


class Data(object):

    def __init__(self):
        pass


    def start(self):
        pass


    def stop(self):
        pass



class RequestData(Data):

    def getContentLength(self):
        return self.content_length


    def getContentType(self):
        return self.content_type


    def read(self):
        raise NotImplementedError



class ResponseData(Data):

    def write(self, data):
        raise NotImplementedError


    def clear(self):
        raise NotImplementedError
