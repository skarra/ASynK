In May 2015 Google turned off ClientLogin method of authentication used by ASynK. This method has been deprecated in favour of oAuth since 2012. oAuth is considered the cutting edge in authentication and authorization. But it is a f-ing PITA for programmers and open source software.

Anyways, setting up Google Contacts to be used with ASynK (without modifying anything else) needs some patience. Please read on for more details.

The good news is it can be made to work.

Step 1. Setting up your Google Account
--------------------------------------

1. Go to https://console.developers.google.com
2. If you have more than one active gmail account, switch to the one you want ASynK to sync to
3. Create a new project. You can call it 'My ASynK'
4. Click on the newly created project
5. Click on APIs & Auth -> API
 - Search for 'Contacts API'
 - Click on 'Enable API'
6. Click on APIs & Auth -> Credentials
 - click on the blue 'Create new Client ID' button
 - select third bullet 'Installed application' for application type
 - select 'Other' for Installed application type
 - click on the blue 'Create Client ID' button

Step 2. Saving your credentials to your user-dir
-

- After you are done creating a new client ID, you will be taken to screen where there will be a 'Download JSON' button. Click on it.

- Once it is downloaded rename it to something smaller, and move it to your `~/.asynk` directory. Actually any location or name will do, as long as you can remember it.

Step 3. Authentication
-

   username: your gmail username
   password: the path to your credentials json you downloaded in step 2

You can use netrc or keyboard input. `--gcuser` and `--gcpw` commandline flags are not currently working

Step 4. You will have to install some additional python packages. For e.g.
-

    $ pip install httplib2 oauth2client PyOpenSSL

There may be a few others, so please tell if you additional are required.

Step 5. Update your submodules
-

Some of the submodules have been updated. So you may have to do the following as well:

    $ git pull --recurse-submodules
    $ git submodule update --recursive
