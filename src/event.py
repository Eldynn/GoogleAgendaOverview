import datetime

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect, QHBoxLayout, QLabel

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

        # TODO: Add to the QLabel an ellipsis when text is too long
        summary_text = self.data['summary']
        summary = QLabel(
            '<a style="color: #3949AB" href="' + self.data['htmlLink'] + '">' + summary_text + '</a>'
        )
        summary.setToolTip(summary_text)
        summary.setOpenExternalLinks(True)
        summary.setFixedWidth(200)
        layout.addWidget(summary)

        # TODO: Add icon link to conference

        self.timer_label = QLabel()
        self.timer_label.setAlignment(Qt.AlignRight)
        self.timer_label.setFixedWidth(50)
        self.countdown()
        layout.addWidget(self.timer_label)

        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timeout)
        self.timer.start(1000)

    def timeout(self):
        self.countdown()

    # TODO: Add ui effects for countdown close to end
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
