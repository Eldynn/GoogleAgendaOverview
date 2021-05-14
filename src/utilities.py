import datetime
import sys
from os import path

from main import APPDATA


def clear_layout(layout):
    while layout.count():
        clear_widget(layout.takeAt(0))


def clear_widget(item):
    if hasattr(item, 'timer'):
        item.timer.stop()

    if item.layout():
        clear_layout(item.layout())

    if hasattr(item, 'widget') and item.widget():
        item.widget().deleteLater()


def handle_error(message):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    with open(path.join(APPDATA, 'errors.log'), 'a') as file:
        file.write('[{0}] {1}\n'.format(now, message))


def except_hook(cls, exception, traceback):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    message = '[{0}] type: {1}\n[{0}] exception: {2}\n[{0}] traceback: {3}\n'.format(now, cls, exception, traceback)
    print(message)

    with open(path.join(APPDATA, 'crash.log'), 'a') as file:
        file.write(message)

    sys.__excepthook__(cls, exception, traceback)
    sys.exit(1)
