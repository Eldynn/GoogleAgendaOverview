from __future__ import print_function

import datetime
import os.path
import sys
from os import path, environ

import qtawesome
from PyQt5.QtCore import Qt, QMetaObject
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QMainWindow, QApplication
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

NAME = 'Today Overview'
if sys.platform == 'win32':
    appdata = path.join(environ['APPDATA'], NAME)
else:
    appdata = path.expanduser(path.join('~', '.' + NAME))


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)

        if child.layout():
            clear_layout(child.layout())

        if child.widget():
            child.widget().deleteLater()


def minimum_digits(number, minimum, format, char):
    string = str(number)
    length = len(string)
    if length < minimum:
        return format.format(string, char * (minimum - length))
    else:
        return string


class Ui(QMainWindow):
    flags = Qt.Window | Qt.WindowStaysOnTopHint

    title = NAME
    icon = 'fa5s.calendar-day'

    central_widget = None
    column_layout = None
    events_layout = None

    token_path = path.join(appdata, 'token.json')
    credentials = None
    service = None

    calendars = []
    events = []

    def __init__(self):
        super(Ui, self).__init__(None, self.flags)

        self.authorize()
        self.setup_ui()

    def authorize(self):
        if os.path.exists(self.token_path):
            self.credentials = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                self.credentials = flow.run_local_server(port=0)

            with open(self.token_path, 'w') as token:
                token.write(self.credentials.to_json())

        self.service = build('calendar', 'v3', credentials=self.credentials)

    def logout(self):
        if os.path.exists(self.token_path):
            os.remove(self.token_path)
            self.credentials = None

            self.authorize()
            self.refresh()

    def setup_ui(self):
        self.setWindowTitle(self.title)
        self.setWindowIcon(qtawesome.icon(self.icon))

        self.central_widget = QWidget(self)

        self.column_layout = QVBoxLayout()
        self.central_widget.setLayout(self.column_layout)

        menu_layout = QHBoxLayout()
        self.column_layout.addLayout(menu_layout)
        self.events_layout = QVBoxLayout()
        self.column_layout.addLayout(self.events_layout)

        logout_button = QPushButton('Logout', self.central_widget)
        logout_button.clicked.connect(self.logout)
        menu_layout.addWidget(logout_button)

        refresh_button = QPushButton('Refresh', self.central_widget)
        refresh_button.clicked.connect(self.refresh)
        menu_layout.addWidget(refresh_button)

        self.setCentralWidget(self.central_widget)

        QMetaObject.connectSlotsByName(self)

        self.refresh()

    def build_event(self, event):
        layout = QHBoxLayout()

        datetime_format = '%Y-%m-%dT%H:%M:%S%z'
        start = datetime.datetime.strptime(event['start']['dateTime'], datetime_format)
        end = datetime.datetime.strptime(event['end']['dateTime'], datetime_format)

        seconds = (end - start).total_seconds()
        delta = '%smin' % (int(seconds / 60))
        if seconds >= 3600:
            hours = int(seconds // 3600)
            minutes = int((seconds / 60) % 60)
            if hours and minutes:
                delta = '%s:%s' % (minimum_digits(hours, 2, '{1}{0}', '0'), minimum_digits(minutes, 2, '{1}{0}', '0'))
            elif hours:
                delta = '%sh' % hours

        duration = QLabel('%s - %s (%s)' % (start.strftime("%H:%M"), end.strftime("%H:%M"), delta))
        layout.addWidget(duration)

        summary = QLabel('<a href="' + event['htmlLink'] + '">' + event['summary'] + ' /</a>')
        summary.setOpenExternalLinks(True)
        layout.addWidget(summary)

        self.events_layout.addLayout(layout)

    def refresh(self):
        self.calendars = []
        self.paged_query(self.refresh_calendars)

        self.events = []
        now = datetime.datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
        for calendar in self.calendars:
            self.paged_query(self.refresh_events, calendar, time_min, time_max)

        clear_layout(self.events_layout)

        for event in self.events:
            self.build_event(event)

        size = self.column_layout.sizeHint()
        available_size = self.screen().availableSize()
        size.setWidth(min(size.width(), available_size.width()))
        size.setHeight(min(size.height(), available_size.height()))

        self.setFixedSize(size)

    def paged_query(self, func, *args, **kwargs):
        page_token = None
        while True:
            page_token = func(page_token, *args, **kwargs)

            if not page_token:
                break

    def refresh_events(self, page_token, calendar, time_min, time_max):
        events = self.service.events().list(
            calendarId=calendar['id'],
            singleEvents=True,
            timeMin=time_min,
            timeMax=time_max,
            orderBy='startTime',
            pageToken=page_token,
            maxAttendees=1
        ).execute()

        self.events += events['items']

        return events.get('nextPageToken')

    def refresh_calendars(self, page_token):
        calendar_list = self.service.calendarList().list(
            pageToken=page_token,
            minAccessRole='owner'
        ).execute()

        self.calendars += calendar_list['items']

        return calendar_list.get('nextPageToken')


if __name__ == '__main__':
    if not os.path.exists(appdata):
        os.mkdir(appdata)

    app = QApplication(sys.argv)

    ui = Ui()
    ui.show()

    sys.exit(app.exec())
