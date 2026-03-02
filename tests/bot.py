from time import sleep
import sys, os

sys.path.insert(0, os.getcwd())

from bp_chat.bot import ChatBot, checkable


class MyBot(ChatBot):

    def do_test(self, chat_id, args):
        print('[ test ] {} : {}'.format(chat_id, args))

    @checkable
    def do_test2(self, chat_id, args):
        print('[ test2 ] {} : {}'.format(chat_id, args))


if __name__=='__main__':

    tst_uuid = input("Input uuid:\n\t")

    cb = MyBot(uuid=tst_uuid, server_address='127.0.0.1')
    cb.connect()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        pass

    print('-' * 10 + "fin")