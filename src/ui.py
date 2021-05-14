import datetime
import os.path
from os import path
from urllib.error import URLError, HTTPError, ContentTooShortError
from urllib.request import urlopen

from PyQt5.QtCore import Qt, QMetaObject, QSettings
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLayout
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from main import APPDATA, SCOPES, NAME
from src.event import Event
from src.header import Header
from src.utilities import clear_layout, handle_error


class Ui(QFrame):
    flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    settings = None

    header = None
    body = None

    mouse_down = False
    old_position = None

    header_layout = None
    column_layout = None
    events_layout = None

    token_path = path.join(APPDATA, 'token.json')
    credentials = None
    service = None

    calendars = []
    events = []
    icons = {}

    def __init__(self):
        super(Ui, self).__init__(None, self.flags)

        self.authorize()

        self.settings = QSettings(NAME, NAME)

        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)

        self.setFrameShape(QFrame.StyledPanel)

        # TODO: QPushButton[iconOnly="True"] should be circle button
        css = """
        QFrame {
            background-color: white;
            border: 1px solid #3949AB;
        }
        QPushButton {
            background-color: #3949AB;
            color: white;
            border-radius: 5px;
            padding: 10px 20px;
            min-width: 50px;
        }
        QPushButton[iconOnly="True"] {
            padding: 10px;
            min-width: unset;
        }
        QPushButton:hover {
            background-color: #5C6BC0;
        }
        """
        self.setStyleSheet(css)
        self.setMouseTracking(True)

        self.header = Header(self)
        self.body = QWidget(self)

        css = """
        QWidget {
            border: 0;
        }
        QWidget[class~="event"] {
            background-color: #7986CB;
            border-radius: 5px;
        }
        QWidget[class~="event"] QLabel {
            background-color: #7986CB;
            color: white;
        }
        QWidget[class~="needsAction"] {
            border-bottom: 5px Solid #304FFE;
            border-bottom-left-radius: 0;
            border-bottom-right-radius: 0;
        }
        QWidget[class~="event"] QLabelClickable {
            color: #3949AB;
            font-weight: bold;
            text-decoration: underline;
        }
        """
        self.body.setStyleSheet(css)

        self.header_layout = QVBoxLayout(self)
        self.header_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(0)
        self.header_layout.addWidget(self.header)

        body_layout = QVBoxLayout()
        body_layout.addWidget(self.body)
        body_layout.setContentsMargins(5, 5, 5, 5)
        body_layout.setSpacing(0)

        self.header_layout.addLayout(body_layout)

        self.setup_ui()

    def closeEvent(self, event):
        self.settings.setValue('geometry', self.saveGeometry())

    def mousePressEvent(self, event):
        self.old_position = event.pos()
        self.mouse_down = event.button() == Qt.LeftButton

    def mouseReleaseEvent(self, event):
        self.mouse_down = False

    def authorize(self):
        if os.path.exists(self.token_path):
            self.credentials = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                try:
                    self.credentials.refresh(Request())
                except RefreshError:
                    os.remove(self.token_path)
                    self.credentials = None
                    return self.authorize()
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

    # TODO: Make events layout scrollable
    def setup_ui(self):
        self.column_layout = QVBoxLayout(self.body)
        self.column_layout.setSpacing(15)

        menu_layout = QHBoxLayout()
        self.column_layout.addLayout(menu_layout)

        self.events_layout = QVBoxLayout()
        self.events_layout.setSpacing(15)
        self.column_layout.addLayout(self.events_layout)

        logout_button = QPushButton('Logout')
        logout_button.clicked.connect(self.logout)
        menu_layout.addWidget(logout_button)

        refresh_button = QPushButton('Refresh')
        refresh_button.clicked.connect(self.refresh)
        menu_layout.addWidget(refresh_button)

        QMetaObject.connectSlotsByName(self)

        self.refresh()

    # TODO: Subscribe to changes or poll each 15m
    # TODO: Store when the last refresh happened to prevent unnecessary refresh when event end and send a refresh
    def refresh(self):
        self.calendars = []
        self.paged_query(self.refresh_calendars)

        self.events = []
        now = datetime.datetime.utcnow()  # TODO: Do we need to use a specific timezone?
        time_min = now.isoformat() + 'Z'
        time_max = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
        for calendar in self.calendars:
            self.paged_query(self.refresh_events, calendar, time_min, time_max)

        clear_layout(self.events_layout)

        for event in self.events:
            self.events_layout.addWidget(Event(self, event))

        self.refresh_size()

    def refresh_size(self):
        size = self.header_layout.sizeHint()
        available_size = self.screen().availableSize()
        size.setWidth(min(size.width(), available_size.width()))
        size.setHeight(min(size.height(), available_size.height()))

        self.setFixedSize(size)

    # TODO: If fail to fetch an uri for X times, find a way to limit future try or stop trying
    # TODO: Store & restore on drive
    def fetch_icon(self, uri):
        if uri in self.icons:
            return self.icons[uri]
        else:
            try:
                data = urlopen(uri).read()  # TODO: Investigate on .read() raised exceptions
            except (URLError, HTTPError, ContentTooShortError) as exception:
                handle_error(exception)
                return None

            pixmap = QPixmap()
            pixmap.loadFromData(data)

            icon = QIcon(pixmap)
            self.icons[uri] = icon

            return icon

    @staticmethod
    def paged_query(func, *args, **kwargs):
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
            maxAttendees=1,
            showDeleted=False
        ).execute()

        def remove_declined_event(event):
            if 'attendees' in event and event['attendees'][0]:
                if event['attendees'][0]['responseStatus'] == 'declined':
                    return False

            return True

        self.events += filter(remove_declined_event, events['items'])

        return events.get('nextPageToken')

    # TODO: Let user choose which calendar the want to fetch events from
    def refresh_calendars(self, page_token):
        calendar_list = self.service.calendarList().list(
            pageToken=page_token,
            minAccessRole='owner'
        ).execute()

        self.calendars += calendar_list['items']

        return calendar_list.get('nextPageToken')
