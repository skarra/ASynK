## 
## Created       : Sat May 12 11:31:29 IST 2012
## Last Modified : Thu May 17 11:50:42 IST 2012
## 
## Copyright (C) 2012 by Sriram Karra <karra.etc@gmail.com>
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
##

import os

from google.appengine.ext             import webapp, db
from google.appengine.ext.webapp      import template
from google.appengine.ext.webapp.util import run_wsgi_app

class MainPage(webapp.RequestHandler):
    def get(self):
        intro = ''
        path =  os.path.join(os.path.dirname(__file__), 'intro.html')
        with open(path, 'r') as f:
            intro = f.read()

        template_values = {
            'intro_html': intro,
            }

        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication([('/', MainPage),
                                      ],
                                     debug=True)

def main():
    run_wsgi_app(application)
 
if __name__ == "__main__":
    main()
