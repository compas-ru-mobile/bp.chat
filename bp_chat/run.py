import sys, os


if sys.platform.startswith('win'):
    TST = 'qwertyuiopasdfghjklzxcvbnmйцукенгшщзхъфывапролджэячсмитьбю'
    TST += TST.upper()
    TST += '1234567890 /\\_~!@#$%^&*()_+-=<>?,.\'":;[]{}`'
    for i, a in enumerate(sys.path):
        for key in a:
            if key not in TST:
                sys.path[i] = os.getcwd()
                break
    os.environ['PATH'] = os.getcwd() + ";" + os.environ['PATH']

# if '-debug' not in sys.argv:
#     f = open(os.devnull, 'w')
#     sys.stdout = f

from bp_chat._tune import Tunes

if "update" in sys.argv:
    # from bp_chat.update import do_update
    # main = lambda: do_update(None)
    pass

elif "api" in sys.argv:
    from bp_chat.api import do_api
    main = lambda: do_api(Tunes)

elif "install" in sys.argv:
    from bp_chat.update import do_install
    main = lambda: do_install(None)

elif "uninstall" in sys.argv:
    from bp_chat.update import do_uninstall
    main = lambda: do_uninstall(None)

elif "version" in sys.argv:
    def main():
        print(Tunes.version)

elif "tst" in sys.argv:
    from bp_chat.tst import do_tst
    main = lambda: do_tst(None)

else:
    print('[ starting... ]')
    from bp_chat.gui.app import main