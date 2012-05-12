##
## gc_tasks.py
##
## Created       : Wed Dec 07 17:56:32 IST 2011
## Last Modified : Wed Dec 07 18:06:40 IST 2011
##
## Copyright (C) Sriram Karra <karra.etc@gmail.com>
## All Rights Reserved
##
## Licensed under the GPL v3
##

import httplib2
import gflags

import oauth2 as oauth
from   apiclient.discovery  import build
from   apiclient.oauth      import OAuthCredentials
from   oauth2client.file    import Storage
from   oauth2client.client  import OAuth2WebServerFlow
from   oauth2client.tools   import run

FLAGS = gflags.FLAGS

oa2_client_id     = '1044947297499.apps.googleusercontent.com'
oa2_client_secret = '8yDDiuu9c0G1rVLF8FjVzKPh'
oa2_redirect_uri  = 'urn:ietf:wg:oauth:2.0:oob'
tasks_url         = 'https://www.googleapis.com/auth/tasks'

oa_url_base = 'https://accounts.google.com/o/oauth2/auth'

# Set up a Flow object to be used if we need to authenticate. This
# sample uses OAuth 2.0, and we set up the OAuth2WebServerFlow with
# the information it needs to authenticate. Note that it is called
# the Web Server Flow, but it can also handle the flow for native
# applications
# The client_id and client_secret are copied from the API Access tab on
# the Google APIs Console
FLOW = OAuth2WebServerFlow(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    scope='https://www.googleapis.com/auth/tasks',
    user_agent='YOUR_APPLICATION_NAME/YOUR_APPLICATION_VERSION')

# To disable the local server feature, uncomment the following line:
# FLAGS.auth_local_webserver = False

# If the Credentials don't exist or are invalid, run through the native client
# flow. The Storage object will ensure that if successful the good
# Credentials will get written back to a file.
storage = Storage('tasks.dat')
credentials = storage.get()
if credentials is None or credentials.invalid == True:
  credentials = run(FLOW, storage)

# Create an httplib2.Http object to handle our HTTP requests and authorize it
# with our good Credentials.
http = httplib2.Http()
http = credentials.authorize(http)

# Build a service object for interacting with the API. Visit
# the Google APIs Console
# to get a developerKey for your own application.
service = build(serviceName='tasks', version='v1', http=http,
       developerKey='YOUR_DEVELOPER_KEY')
