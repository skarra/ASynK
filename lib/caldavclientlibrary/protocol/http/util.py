##
# Copyright (c) 2006-2013 Apple Inc. All rights reserved.
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


def parsetoken(text, delimiters=" \t"):

    if not text:
        return "", ""

    if text[0] == '"':
        return parsequoted(text, delimiters)
    else:
        for pos, c in enumerate(text):
            if c in delimiters:
                token = text[0:pos]
                break
        else:
            return text, ""

        return token, lstripdelimiters(text[pos:], delimiters)



def parsequoted(text, delimiters=" \t"):

    assert(text)
    assert(text[0] == '"')

    pos = 1
    while True:
        next_pos = text.find('"', pos)
        if next_pos == -1:
            return text[1:].replace("\\\\", "\\").replace("\\\"", "\""), ""
        if text[next_pos - 1] == '\\':
            pos = next_pos + 1
        else:
            return (
                text[1:next_pos].replace("\\\\", "\\").replace("\\\"", "\""),
                lstripdelimiters(text[next_pos + 1:], delimiters)
            )



def lstripdelimiters(text, delimiters):
    for pos, c in enumerate(text):
        if c not in delimiters:
            return text[pos:]
    else:
        return ""



def parseStatusLine(status):

    status = status.strip()

    # Must have 'HTTP/1.1' version at start
    if status[0:9] != "HTTP/1.1 ":
        return 0

    # Must have three digits followed by nothing or one space
    if not status[9:12].isdigit() or (len(status) > 12 and status[12] != " "):
        return 0

    # Read in the status code
    return int(status[9:12])
