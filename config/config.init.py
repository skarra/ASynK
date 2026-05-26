##
## This is where you would customize ASynK's configuration settings. You can
## have any python code in here. Ensure you do not break the basic structure
## of the 'config' object which should be a dictionary as defined in the base
## .json configuration files that are distributed with the sources. You can
## view all the json configurations in the directory asynk_app_root/config/
## directory.
##


def customize_config (config):
    """The input 'config' object is a dictionary containing the ASynK
    Configuration. This method is invoked immediately after the main
    configuration file is read and parsed. You can view the format and
    contents of the configuration dictionary in the file ./config_v5.json
    which is heavily commented and should be largely self-explanatory.

    This method should return the config object after making any
    customizations as required."""

    ## The following line to increase the backup retention duration from the
    ## 'default' 7 days to 10 days

    config['backup_hold_period'] = 10

    ## Uncomment the following line to change the name of the log directory
    ## from the default 'logs' to 'logfiles'

    # config['log_dir'] = 'logfiles'

    ## Uncomment this line if you are synching with a carddav server and want
    ## to see detailed request and response interaction with the Carddav
    ## server.

    # config['db_config']['cd']['log'] =  True

    ## Uncomment this line if you are synching with Google Contacts and want
    ## to see detailed request and response interaction with the server (for
    ## some requests and responses only)

    # config['db_config']['gc']['log'] =  True

    ## Exchange Online (Microsoft 365) works out of the box with the
    ## default client_id shipped in config_v9.json.  Uncomment below
    ## only if you want to use your own Entra ID app registration.

    # config['db_config']['ex']['client_id'] = 'YOUR-AZURE-AD-CLIENT-ID'

    ## Optionally restrict to a specific Entra ID tenant:
    # config['db_config']['ex']['tenant_id'] = 'YOUR-TENANT-ID'
