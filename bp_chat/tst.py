
def do_tst(tunes):
    import sys, os
    #print('--- tst ---')
    #print('PATH: {}'.format(sys.path))
    #print('SYS PATH: {}'.format(os.getenv('PATH')))
    try:
        #print('[ tst ] 1')
        from win32com.client import Dispatch
        #print('[ tst ] 2')
    except BaseException as e:
        #print('ERROR: cant import Dispatch: {}'.format(e))
        pass
    #print('[ tst ] 3')
    import shutil
    #print('[ tst ] 4')
    #print('[ tst ] 5', Dispatch, shutil)
