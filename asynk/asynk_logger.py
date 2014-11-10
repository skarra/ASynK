## 
## Created : Sun Oct 05 15:34:47 IST 2014
## 
## Copyright (C) 2014 by Sriram Karra <karra.etc@gmail.com>
## 
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero GPL (GNU AGPL) as published by the
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

import datetime, logging, os, string
import utils

class ASynKLogger:
    def __init__ (self, config):
        self.config = config

    def setup (self):
        """Set up the logging settings to the defaults. The log directory is
        created inside asynk_user_dir, which is assumed to exist already"""

        config = self.config
        formatter = logging.Formatter('[%(asctime)s.%(msecs)03d '
                                      '%(levelname)8s] %(message)s',
                                      datefmt='%H:%M:%S')
    
        ## First the console logger - the logging level may be changed later after
        ## the command line arguments are parsed properly.

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
    
        self.consoleLogger = logging.StreamHandler()
        self.consoleLogger.setLevel(logging.INFO)
        self.consoleLogger.setFormatter(formatter)
        logger.addHandler(self.consoleLogger)
    
        ## Now the more detailed debug logs which are written to file in a default
        ## logs/ directory. The location of the directory is read from the
        ## configuration file.
    
        logdir = os.path.join(config.get_user_dir(), config.get_log_dir())
        if not os.path.exists(logdir):
            logging.info('Creating Logs directory at: %s', logdir)
            os.mkdir(logdir)
    
        stamp   = string.replace(str(datetime.datetime.now()), ' ', '.')
        stamp   = string.replace(stamp, ':', '-')
        logname = os.path.abspath(os.path.join(logdir, 'asynk_logs.' + stamp))
        logging.info('Debug logging to file: %s', logname)
    
        fileLogger = logging.FileHandler(logname, 'w')
        fileLogger.setLevel(logging.DEBUG)
        fileLogger.setFormatter(formatter)
        logger.addHandler(fileLogger)
    
    def clear_old_logs (self):
        config = self.config
        logdir = os.path.join(config.get_user_dir(), config.get_log_dir())
        if not os.path.exists(logdir):
            return
    
        period = config.get_log_hold_period()
        logging.info('Deleting log files older than %d days, if any...', period)
        utils.del_files_older_than(logdir, period)
        logging.info('Deleting log files older than %d days, if any...done',
                     period)
    
