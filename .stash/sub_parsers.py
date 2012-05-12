## Wed Apr 11 14:53:23 IST 2012 I dabbled briefly with subcommands, but it was
## impossible to provide a default subcommand, and one of the key requirements
## - essentially for Windows users - is to be able to run the program without
## any arguments, and be taken to the webserver option. So shelving this
## approach for now.

# def setup_parser_abandoned ():
#     p = argparse.ArgumentParser(description='ASynK: PIM Android Sync by Karra')

#     sp = p.add_subparsers(help='Action Groups')
   
#     mp = sp.add_parser('manage',   help='House Keeping Activities')
#     yp = sp.add_parser('sync',     help='Perform Sync')
#     wp = sp.add_parser('startweb', help='Start webserver for UI. Default action')

#     yp.add_argument('--dry-run', action='store_true',
#                    help='Do not sync, but merely show what will happen '
#                    'if a sync is performed.')

#     mp.add_argument('--op', action='store',
#                    choices = ('list-folders',
#                               'del-folder',
#                               'list-items',
#                               'print-item',
#                               'del-item',
#                               'clear-sync-artifacts',),
#                    help='Specific management operation to be performed.')

#     mp.add_argument('--remote-db', action='store', choices=('bb', 'gc', 'ol'),
#                     help=('Specifies which remote db''s sync data to be ' +
#                           'cleared with clear-sync-artifacts'))

#     meg = mp.add_mutually_exclusive_group()
#     meg.add_argument('--folder-name', action='store',
#                      help='For folder operations specify the name of the '
#                      'folder to operate on.')
#     meg.add_argument('--folder-id', action='store',
#                      help='For folder operations specify the ID of the '
#                      'folder to operate on.')
#     meg.add_argument('--item-id', action='store',
#                      help='For Item operations specify the ID of the '
#                      'Item to operate on.')

#     ## Let's group some of the global options into logical groupings...

#     # A Group for Google authentication
#     gg = p.add_argument_group('Google Authentication')

#     gg.add_argument('--user', action='store', 
#                    help=('Google username. Relevant only if --db=gc is used'))

#     gg.add_argument('--pwd', action='store', 
#                    help=('Google password. Relevant only if --db=gc is used'))


#     # A Group for BBDB stuff
#     gb = p.add_argument_group('BBDB Paramters')
#     gb.add_argument('--file', action='store', default='~/.bbdb',
#                    help='BBDB File is --db=bb is used.')

#     wp.add_argument('--port', action='store', type=int,
#                     help=('Port number on which to start web server.'))

#     p.add_argument('--db',  action='append', choices=('bb', 'gc', 'ol'),
#                    help=('DB IDs required for most actions. ' +
#                          'Some actions need two DB IDs - do it with two --db ' +
#                          'flags. When doing so remember that order might be ' + 
#                          'important for certain operations.'))

#     p.add_argument('--version', action='version', version='%(prog)s 1.0')

#     return p
