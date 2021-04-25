import datetime
import sys
from os import path

from main import APPDATA


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)

        if child.layout():
            clear_layout(child.layout())

        if child.widget():
            child.widget().deleteLater()


def minimum_digits(number, minimum, custom, char):
    string = str(number)
    length = len(string)
    if length < minimum:
        return custom.format(string, char * (minimum - length))
    else:
        return string


def except_hook(cls, exception, traceback):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    message = '[{0}] type: {1}\n[{0}] exception: {2}\n[{0}] traceback: {3}\n'.format(now, cls, exception, traceback)
    print(message)

    with open(path.join(APPDATA, 'crash.log'), 'a') as file:
        file.write(message)

    sys.__excepthook__(cls, exception, traceback)
    sys.exit(1)
