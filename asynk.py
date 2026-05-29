##
## Created :Tue Apr 10 15:55:20 IST 2012
## SPDX-FileCopyrightText: 2012-2026 Sriram Karra <karra.etc@gmail.com>
## SPDX-License-Identifier: AGPL-3.0-only
##
## This file is part of ASynK
##
## Entry point for ASynK. Delegates immediately to the subcommand-based
## CLI implemented in asynk_subcmds.py.
##

import os, sys

ASYNK_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXTRA_PATHS = [os.path.join(ASYNK_BASE_DIR, 'lib'),
               os.path.join(ASYNK_BASE_DIR, 'asynk'),]
sys.path = EXTRA_PATHS + sys.path

def main (argv=sys.argv):
    from asynk_subcmds import subcmd_main
    return subcmd_main(argv)

if __name__ == "__main__":
    main()
