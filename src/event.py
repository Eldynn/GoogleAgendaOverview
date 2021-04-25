import datetime
from webbrowser import open

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton

from main import DATETIME_FORMAT
from src.utilities import clear_widget


class Event(QWidget):
    parent = None
    data = None

    timer = None
    timer_label = None
    start = None
    end = None

    def __init__(self, parent, event):
        super(Event, self).__init__()

        self.parent = parent
        self.data = event

        self.setup_ui()

    # TODO: Use google event data to style the ui (colors, transparency, visibility)
    # TODO: Let user customize which information to show
    # TODO: When printing email or name if it is the current user, display a custom string like "You" instead
    # TODO: Do something with attachments?
    # TODO: Do something with attendees? (How to handle big list? Don't and display ellipsis? How to detect?)
    def setup_ui(self):
        self.setProperty('class', 'event')
        self.setContentsMargins(5, 5, 5, 5)
        self.setAttribute(Qt.WA_StyledBackground, True)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(2)
        shadow.setYOffset(2)
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout()

        self.start = datetime.datetime.strptime(self.data['start']['dateTime'], DATETIME_FORMAT)
        self.end = datetime.datetime.strptime(self.data['end']['dateTime'], DATETIME_FORMAT)
        seconds = (self.end - self.start).total_seconds()
        delta = ''
        if seconds >= 3600:
            hours = int(seconds // 3600)
            seconds -= hours * 3600
            delta = '{0}h'.format(hours)

        if seconds >= 60:
            minutes = int((seconds // 60) % 60)
            delta += '{0}m'.format(minutes)

        duration = QLabel('%s - %s (%s)' % (self.start.strftime("%H:%M"), self.end.strftime("%H:%M"), delta))
        duration.setMinimumWidth(120)
        layout.addWidget(duration)

        self.setup_summary(layout)
        self.setup_conference(layout)

        self.timer_label = QLabel()
        self.timer_label.setAlignment(Qt.AlignRight)
        self.timer_label.setFixedWidth(50)
        self.countdown()
        layout.addWidget(self.timer_label)

        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timeout)
        self.timer.start(1000)

    # TODO: Display pretty date
    def setup_summary(self, layout):
        # TODO: Add to the QLabel an ellipsis when text is too long
        text = self.data['summary']
        summary = QLabel(
            '<a style="color: #3949AB" href="' + self.data['htmlLink'] + '">' + text + '</a>'
        )

        if 'organizer' in self.data:
            text += '\n\nOrganizer:'
            if 'displayName' in self.data['organizer']:
                text += ' "{0}"'.format(self.data['organizer']['displayName'])

            if 'email' in self.data['organizer']:
                text += ' <{0}>'.format(self.data['organizer']['email'])

        if 'location' in self.data:
            text += '\nLocation: ' + self.data['location']

        # TODO: Handle HTML inside description
        if 'description' in self.data:
            text += '\nDescription: ' + self.data['description']

        event_type_text = {
            'default': 'Regular',
            'outOfOffice': 'Out-of-office',
        }
        text += '\n\nEvent type: ' + event_type_text[self.data['eventType']]

        text += '\nCreated at: ' + self.data['created']
        if 'creator' in self.data:
            text += ' By'
            if 'displayName' in self.data['creator']:
                text += ' "{0}"'.format(self.data['creator']['displayName'])

            if 'email' in self.data['creator']:
                text += ' <{0}>'.format(self.data['creator']['email'])
        text += '\nLast modification: ' + self.data['updated']

        summary.setToolTip(text)
        summary.setOpenExternalLinks(True)
        summary.setFixedWidth(200)
        layout.addWidget(summary)

    # TODO: Handle more type of conference (phone, sip, more)
    # TODO: Fix the alignment (When row contain conference and others don't)
    def setup_conference(self, layout):
        if 'conferenceData' not in self.data:
            return

        conference_data = self.data['conferenceData']
        conference_data_solution = conference_data['conferenceSolution']
        for entrypoint in conference_data['entryPoints']:
            if entrypoint['entryPointType'] != 'video':
                continue

            conference = QPushButton()
            conference.setProperty('class', 'video')
            uri = entrypoint['uri']
            conference.clicked.connect(lambda: open(uri))

            icon = self.parent.fetch_icon(conference_data_solution['iconUri'])
            tooltip = conference_data_solution['name']
            label = tooltip
            if 'label' in entrypoint and not uri.endswith(entrypoint['label']):
                label = entrypoint['label']

            text = ''
            if icon:
                conference.setProperty('iconOnly', 'True')
                conference.setIcon(icon)
            else:
                text = label

            conference.setText(text)

            # TODO: Handle HTML in tooltip
            if 'notes' in conference_data:
                tooltip += '\n\nNotes: {0}'.format(conference_data['notes'])
            conference.setToolTip(tooltip)

            layout.addWidget(conference)

    def timeout(self):
        self.countdown()

    # TODO: Add ui effects for countdown close to end (maybe use Google event data reminders)
    # TODO: Start timer inside countdown and update timer trigger duration their
    def countdown(self):
        now = self.start.today()
        now = now.astimezone(datetime.datetime.now().astimezone().tzinfo)

        count_from = self.start
        if now > self.start:
            if now > self.end:
                clear_widget(self)
                self.parent.refresh()
                return
            else:
                count_from = self.end

        seconds = (count_from - now).total_seconds()

        result = ''
        if seconds >= 3600:
            hours = int(seconds // 3600)
            seconds -= hours * 3600
            result = '{0}h'.format(hours)

        if seconds >= 60:
            minutes = int((seconds // 60) % 60)
            seconds -= minutes * 60
            result += '{0}m'.format(minutes)
        else:
            result = '{0}s'.format(int(seconds))

        self.timer_label.setText(result)
