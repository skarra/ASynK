#!/usr/bin/env python

## Created	 : Wed May 18 13:16:17  2011
## Last Modified : Mon May 30 19:08:10  2011
##
## Copyright 2011 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GPL v3
## 

from tornado import ioloop, web
from tools import contacts

class MainHandler(web.RequestHandler):
    def get(self):
        contacts.DumpDefaultAddressBook(self)

application = web.Application([
    (r"/", MainHandler),
])

if __name__ == "__main__":
    application.listen(8888)
    print 'Staring ioloop...'
    ioloop.IOLoop.instance().start()
