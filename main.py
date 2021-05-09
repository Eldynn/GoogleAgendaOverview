from __future__ import print_function

import sys
from os import path, environ, mkdir

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
          'https://www.googleapis.com/auth/calendar.events.readonly']
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
NAME = 'Today Overview'

if sys.platform == 'win32':
    APPDATA = path.join(environ['APPDATA'], NAME)
else:
    APPDATA = path.expanduser(path.join('~', '.' + NAME))

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    from src.ui import Ui
    from src.utilities import except_hook

    sys.excepthook = except_hook

    if not path.exists(APPDATA):
        mkdir(APPDATA)

    app = QApplication(sys.argv)

    ui = Ui()
    ui.show()

    sys.exit(app.exec())
