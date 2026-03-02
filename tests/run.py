from os.path import dirname, abspath
from sys import path

HERE = dirname(abspath(__file__))
PROJ_PATH = dirname(HERE)

path.insert(0, PROJ_PATH)

from bp_chat.run import main

main()