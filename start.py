#!/usr/bin/env python
#
# Last Modified : Wed Sep 28 06:14:28  2011
#
# Adapted from dev_appserver.py distributed with the Google App Engine
# SDK by Google Inc. Modifications are Copyright (C) 2011 Sriram
# Karra. Original copyright notice as under:
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Get things rolling by setting up packaged libraries and starting the
webserver """


import os, sys, getopt, logging

if not hasattr(sys, 'version_info'):
  sys.stderr.write('Please use version 2.5 or greater.\n')
  sys.exit(1)

version_tuple = tuple(sys.version_info[:2])
if version_tuple < (2, 4):
  sys.stderr.write('Error: Python %d.%d is not supported. Please use '
                   'version 2.5 or greater.\n' % version_tuple)
  sys.exit(1)

if version_tuple == (2, 4):
  sys.stderr.write('Warning: Python 2.4 is not supported. '
                   'Please use version 2.5 or greater.\n')

DIR_PATH = os.path.abspath(os.path.dirname(os.path.realpath('outlook_sync')))
SCRIPT_DIR = os.path.join(DIR_PATH, '.')
CONFIG_DIR = os.path.join(DIR_PATH, 'config')

EXTRA_PATHS = [
  DIR_PATH,
  os.path.join(DIR_PATH, 'lib'),
  os.path.join(DIR_PATH, 'tools'),
]

SCRIPT_NAME = "ui.py"
print 'DIR_PATH = ', DIR_PATH
print 'SCRIPT_DIR = ', SCRIPT_DIR
print 'EXTRA_PATHS = ', EXTRA_PATHS

def fix_sys_path():
  """Fix the sys.path to include our extra paths."""
  sys.path = EXTRA_PATHS + sys.path
 

def run_file(globals_, script_dir=SCRIPT_DIR):
  """Execute the file at the specified path with the passed-in globals."""
  fix_sys_path()
  script_name = SCRIPT_NAME
  script_path = os.path.join(script_dir, script_name)
  print 'script_name: ', script_name
  print 'script_path: ', script_path
  globals_['karra_cwd'] = DIR_PATH
  execfile(script_path, globals_)


def main (argv=None):
  if (argv is None):
    argv = sys.argv
    try:
      opts, args = getopt.gnu_getopt(argv[1:],"ht", ["help", "t"])
    except getopt.error, msg:
      print msg
      print "for help use --help"
      sys.exit(2)

  print 'os.getcwd(): ', os.getcwd()
  run_file(globals())

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
