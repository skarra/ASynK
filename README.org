Created : Wed Aug 24 22:41:42 IST 2011

This is only a short introduction and some key points of interest. For more
details on how to use ASynK please refer to the included documentation, or the
official website for ASynK is at: http://asynk.io/ You will find
links to latest download, complete documentation, and other information on
that website.

* About

  ASynK - Awesome Sync (by Karra), is a flexible Contacts synchronization platform
  written in Python. High level features include:

  - ASynK allows two-way sync of Contacts across any two supported sources -
    Google Contacts, Microsoft Outlook, Microsoft Exchange Server, any CardDAV
    server and Emacs BBDB.
  
  - You can use ASynK to copy contacts from one Google account to another
    (say from a Google Apps account at work to a personal address before you
    leave your job). You can do this at the level of folders (see below)

  - ASynK is the only two-way synchronization option for BBDB known to be in
    existence today. So if you are keen to keep your BBDB content synchronized
    with a mobile device or Outlook, look no further.
  
  - ASynK works on Windows, MacOS X, and Linux. Outlook synchronization
    only works on Windows.
  
  - Synchronization is granular to the level of 'Folders', i.e. you can
    synchronize one folder of Google Contacts with a Outlook folder (on
    Windows at work, say), and another Google folder in the same account with
    BBDB (On your Mac, say)
  
  - The infrastructure is there to add more database and item types
    (i.e. tasks, notes, etc.), but currently only Contacts synchronization is
    supported.
    
  - It is free software, and released under the GNU AGPL (Affero GPL) version
    3

* Installation

** Fresh Installation

As you are reading this file, the most efficient installation is to
recursively clone this git repository to your machine. Then see the
section titled Usage below to invoke ASynK.

: git clone  --recursive https://github.com/skarra/ASynK.git

** Updating an earlier install

   If you are updating your ASynK installation from an earlier version,
   please note that many new git-submodules are added to the project. So for
   your update to work properly you need to update all
   sub-modules. Recommended way to do this would be to fun the following
   command from the root of your ASynK directory, after you pull in the latest
   changes

: git submodule update --init --recursive

** Dependencies

   ASynK is completely written in Python. For most use cases and set ups you
   only need to have Python 2.x (x >= 7) installed. Some additional
   dependencies include:

   - If you wish to sync from/to MS Outlook:
     - MS Windows
     - Python 2.x (2.7 or later) for Windows
     - MS Outlook
     - Pywin32 from Mark Hammond, available from
       http://sourceforge.net/projects/pywin32/

   - On Debian (and likely Ubuntu) you will need the following packages:
        sudo apt-get install python-argparse

   - The following python packages.
     - dateutil
     - httplib2
     - oauth2client
     - PyOpenSSL
     - google-api-python-client

     You could install all of them with just 

: $ pip install -r requirements.txt

* Usage

   The recommended way to use ASynK is to first create your own 'sync profile'
   which specifies which folders and PIM DBs you want to keep in sync. Refer
   to the documentation for more details.

   For the really impatient, ASynK comes with two default sync profiles that
   kick in if no other profile is configured.

: $ python asynk.py --op=sync [--dry-run] [--log=debug]

   If you run the above command on Windows, the entire default outlook
   contacts folder will get synched to "My Contacts" on Google Contacts. (You
   will be prompted for your google username and password). 

   On any non-windows platform if you have a  ~/.bbdb will simply be "backed
   up" to /tmp/asynk.bbdb.

   For further usage help, try "python asynk.py -h"
