#!/usr/bin/python
##
## Created : Sun Sep 01 15:03:28 IST 2013
##
## Copyright (C) 2013 Pushkar Dubey and Sriram Karra <karra.etc@gmail.com>
##
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero General Public License as published by the
## Free Software Foundation, version 3 of the License
##
## ASynK is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
## FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
## License for more details.
##
## You should have a copy of the license in the doc/ directory of ASynK.  If
## not, see <http://www.gnu.org/licenses/>.

from subprocess import check_output, Popen, STDOUT, PIPE
from tornado    import ioloop, web, websocket
from tempfile   import gettempdir
from time       import sleep
import webbrowser, json, os

INDEX_HTML = os.path.join("ui", "static", "index.html")
CUR_DIR = os.path.dirname(__file__)

class MainHandler(web.RequestHandler):
    def get (self):
        self.render(INDEX_HTML)

class Profiles(web.RequestHandler):
    def get (self):
        res=check_output(["python","asynk.py","--op=list-profile-names"],
                         stderr=STDOUT).split()
        pos = 0
        profile = []
        for x in range(res.count("Profile:")):
            pos = res.index("Profile:", pos+1)
            profile += [res[pos+1]]
        self.write(json.dumps(profile))

class ProfileData(web.RequestHandler):
    def get (self, pid):
        detail = {}
        res = check_output(["python","asynk.py","--op=show-profile",
                          "--name="+pid], stderr=STDOUT).split()
        pos = res.index(pid)
        posdb1 = res.index("DB",pos)
        detail['db1'] = res[posdb1+3]

        if detail['db1'] in ["gc","cd"]:
            detail['uname1']=res[res.index("Store",posdb1)+3]

        posdb2 = res.index("DB",posdb1+1)
        detail['db2'] = res[posdb2+3]

        if detail['db2'] in ["gc","cd"]:
            detail['uname2']=res[res.index("Store",posdb2)+3]

        self.write (json.dumps(detail))


class AppWebSocket(websocket.WebSocketHandler):
    def open (self):
        print "WebSocket opened"

    def on_message (self, cmd):
        file_stdout = open(gettempdir()+'/appout.txt', 'w')
        file_stdin = open(gettempdir()+'/appout.txt', 'r')
        proc = Popen(cmd.split(), stdout=file_stdout, stderr=STDOUT, stdin=PIPE)
        proc.stdin.write("xyz\n")
        self.write_message (cmd+"<br>")

        while proc.poll()==None:
            msg=file_stdin.readline().strip()
            if msg!="":
                self.write_message(msg+"<br>")
            else:
                sleep(0.1)

    def on_close (self):
        print "WebSocket closed"


static_path = os.path.join(CUR_DIR, 'ui', 'static')

application = web.Application([
    (r"/", MainHandler),
    (r"/profiles",Profiles),
    (r"/pdata/([^/]+)", ProfileData),
    (r"/appresponse", AppWebSocket),
    (r"/static/(.*)",web.StaticFileHandler,
     {'path' : static_path})
])

if __name__ == "__main__":
    webbrowser.open("http://localhost:8888")
    application.listen(8888)
    ioloop.IOLoop.instance().start()

