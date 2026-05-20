import sys
import os

# Указываем путь к проекту
INTERP = os.path.expanduser("~/virtualenv/domophone_contracts/bin/python")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

from app import app as application