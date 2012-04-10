
import os, os.path, shutil, sys, traceback

## Being able to fix the sys.path thusly makes is easy to execute this
## script standalone from IDLE. Hack it is, but what the hell.
DIR_PATH    = os.path.abspath(os.path.dirname(os.path.realpath('../Gout')))
EXTRA_PATHS = [os.path.join(DIR_PATH, 'lib'), os.path.join(DIR_PATH, 'tools')]
sys.path = EXTRA_PATHS + sys.path

from   state import Config, GoutConfigError

def main (argv=None):
    if not argv:
        argv = sys.argv

    ## This module is for quick testing of the Config read/write
    ## functionality. We will make a quick copy of the main example config
    ## file into the current directory and start mucking with it.

    src  = '../app_state.json.example'
    dest = './app_state_test.json'
    shutil.copyfile(src, dest)

    config = Config(dest)

    tcnt = 0
    tcnt += 1
    print '\n### Test No. %2d ###\n' % tcnt
    print 'Label Separator: ', config.get_label_separator()
    print 'olsync_guid: ', config.get_olsync_guid()

    tcnt += 1
    print '\n### Test No. %2d ###\n' % tcnt
    print 'File Version: ', config.get_file_version()
    print 'Setting File Version to 5'
    config.set_file_version(5)
    print 'File Version: ', config.get_file_version()    

    tcnt += 1
    print '\n### Test No. %2d ###\n' % tcnt
    print 'Label Prefix: ', config.get_label_prefix()
    print 'Setting Label Prefix to "Buffoon"'
    config.set_label_prefix('Buffoon')
    print 'Label Prefix: ', config.get_label_prefix()

    tcnt += 1
    print '\n### Test No. %2d ###\n' % tcnt
    val = config.get_olsync_gid()
    print 'olsync_gid(all): ', val
    val = config.get_olsync_gid('gc')
    print 'olsync_gid(gc): ', val
    val = config.get_olsync_gid('bb')
    print 'olsync_gid(bb): ', val

    tcnt += 1
    print '\n### Test No. %2d ###\n' % tcnt
    print 'bb:gc last_sync_start: ', config.get_last_sync_start('bb', 'gc')
    print 'Resetting time to current time'
    config.set_last_sync_start('bb', 'gc', config.get_curr_time())
    print 'bb:gc last_sync_start: ', config.get_last_sync_start('bb', 'gc')

    tcnt += 1
    print '\n### Test No. %2d ###\n' % tcnt
    print 'bb:gc last_sync_stop: ', config.get_last_sync_stop('bb', 'gc')
    print 'Resetting time to current time'
    config.set_last_sync_stop('bb', 'gc', config.get_curr_time())
    print 'bb:gc last_sync_stop: ', config.get_last_sync_stop('bb', 'gc')

    try:
        tcnt += 1
        print '\n### Test No. %2d ###\n' % tcnt
        print 'Testing Invalid PIMDB config access. Should throw an exception.'
        print 'bb:abcd last_sync_start: ', config.get_last_sync_start('bb', 'abcd')
        print 'No Exception. WTF. Total Fail.'
    except GoutConfigError, e:
        print 'Hurrah. ', traceback.format_exc()

    tcnt += 1
    print '\n### Test No. %2d ###\n' % tcnt
    print 'gc:ol sync_dir: ', config.get_sync_dir('gc', 'ol')
    print 'gc:ol sync_dir setting to SYNC1WAY'
    config.set_sync_dir('gc', 'ol', 'SYNC1WAY')
    print 'gc:ol sync_dir: ', config.get_sync_dir('gc', 'ol')

    try:
        tcnt += 1
        print '\n### Test No. %2d ###\n' % tcnt
        print 'Try  Invalid value for sync_dir. Should throw Exception'
        print 'gc:ol sync_dir: ', config.get_sync_dir('gc', 'ol')
        print 'gc:ol sync_dir setting to GOOFY'
        config.set_sync_dir('gc', 'ol', 'GOOFY')
        print 'No Exception. WTF. Total Fail'
    except GoutConfigError, e:
        print 'Hurrah. ', traceback.format_exc()

    tcnt += 1
    print '\n### Test No. %2d ###\n' % tcnt
    print 'bb:ol conflict resolve: ', config.get_conflict_resolve('bb', 'ol')
    print 'bb:ol conflict_resolve to bb'
    config.set_conflict_resolve('bb', 'ol', 'bb')
    print 'bb:ol sync_dir: ', config.get_conflict_resolve('bb', 'ol')

    try:
        tcnt += 1
        print '\n### Test No. %2d ###\n' % tcnt
        print 'Try  Invalid value for conflict_resolve. Should throw Exception'
        print 'bb:ol conflict resolve: ', config.get_conflict_resolve('bb', 'ol')
        print 'bb:ol conflict_resolve to GUPPY'
        config.set_conflict_resolve('bb', 'ol', 'GUPPY')
        print 'No Exception. WTF. Total Fail'
    except GoutConfigError, e:
        print 'Hurrah. ', traceback.format_exc()
        
    tcnt += 1
    print '\n### Test No. %2d ###\n' % tcnt
    print 'ol db_config: ', config.get_db_config('ol')
    print 'ol setting ol["sync_fields"] db_config to []'
    config.set_db_config('ol', {'sync_fields' : []})
    print 'ol db_config: ', config.get_db_config('ol')


if __name__ == '__main__':
    main()  
