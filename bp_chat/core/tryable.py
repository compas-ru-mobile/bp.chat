import traceback, sys

from threading import Thread
from queue import Queue
from time import sleep

from bp_chat.logic.common.log import get_stdout_real


def tryable(func):

    def _new_func(*args, **kwargs):
        return run_in_try(lambda:func(*args, **kwargs))

    return _new_func


def run_in_try(func):
    try:
        return func()
    except BaseException as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        #formatted_lines = traceback.format_exc().splitlines()

        fexc = traceback.format_exception(exc_type, exc_value,
                                        exc_traceback)

        fe_line = ''.join(fexc[2:])
        if not ', line' in fe_line:
            fe_line = ''.join(fexc)

        ConsoleThread.instance().debug(fe_line)


class ConsoleThread:

    RUN_TIMEOUT = 0.1

    __instance = None
    may_work = False
    need_debug = False

    @staticmethod
    def instance(may_work=None, instance_id=0):
        if may_work != None:
            ConsoleThread.may_work = may_work

        if not ConsoleThread.may_work:
            return SimpleConsole

        if not ConsoleThread.__instance:
            ConsoleThread.__instance = ConsoleThread(instance_id)
            ConsoleThread.__instance.start()

        return ConsoleThread.__instance

    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.queue = Queue()
        if '-debug' in sys.argv:
            ConsoleThread.need_debug = True

    def debug(self, message):
        self.queue.put(message)

    def start(self):
        self.thread = Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    @staticmethod
    def stop():
        instance = ConsoleThread.instance()
        ConsoleThread.may_work = False
        ConsoleThread.__instance = None
        return instance

    def join(self):
        self.thread.join()

    def run(self):
        q = self.queue

        while ConsoleThread.may_work:
            while not q.empty():
                message = q.get()
                self._debug(message)
            sleep(ConsoleThread.RUN_TIMEOUT)

        while not q.empty():
            message = q.get()
            self._debug(message)

    def _debug(self, message):
        if ConsoleThread.need_debug:
            _stdout, _stdout_is_changed = get_stdout_real()

            #if _stdout_is_changed:
            message = '[thread-{}] {}'.format(self.instance_id, message)
            _stdout.write(message + "\n")
            _stdout.flush()


class SimpleConsole:

    @staticmethod
    def debug(message):
        pass
