import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect, QHBoxLayout, QLabel

from main import DATETIME_FORMAT
from src.utilities import minimum_digits


class Event(QWidget):
    parent = None
    data = None

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

        start = datetime.datetime.strptime(self.data['start']['dateTime'], DATETIME_FORMAT)
        end = datetime.datetime.strptime(self.data['end']['dateTime'], DATETIME_FORMAT)

        seconds = (end - start).total_seconds()
        delta = '%sm' % (int(seconds / 60))
        if seconds >= 3600:
            hours = int(seconds // 3600)
            minutes = int((seconds / 60) % 60)
            if hours and minutes:
                delta = '%s:%s' % (minimum_digits(hours, 2, '{1}{0}', '0'), minimum_digits(minutes, 2, '{1}{0}', '0'))
            elif hours:
                delta = '%sh' % hours

        duration = QLabel('%s - %s (%s)' % (start.strftime("%H:%M"), end.strftime("%H:%M"), delta))
        duration.setMinimumWidth(120)
        layout.addWidget(duration)

        summary = QLabel(
            '<a style="color: #3949AB" href="' + self.data['htmlLink'] + '">' + self.data['summary'] + '</a>')
        summary.setOpenExternalLinks(True)
        layout.addWidget(summary)

        self.setLayout(layout)
