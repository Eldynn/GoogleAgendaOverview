import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QToolButton, QLabel, QHBoxLayout

from main import NAME


class Header(QWidget):
    icon = 'fa5s.window-close'

    parent = None

    def __init__(self, parent):
        super(QWidget, self).__init__()

        self.parent = parent

        css = """
        QWidget {
            height: 20px;
            padding: 5px;
            color: white;
            background-color: #3949AB;
        }
        QToolButton {
            background-color: #3949AB;
            color: white;
        }
        QToolButton:hover {
            background-color: #5C6BC0;
        }
        """
        self.setStyleSheet(css)

        close_button = QToolButton(self)
        close_button.setIcon(qtawesome.icon('fa5s.window-close', color='white'))
        close_button.setMinimumHeight(10)
        close_button.clicked.connect(self.parent.close)

        title_label = QLabel(self)
        title_label.setText(NAME)
        self.parent.setWindowTitle(NAME)
        self.parent.setWindowIcon(qtawesome.icon(self.icon))

        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title_label)
        layout.addWidget(close_button)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent.moving = True
            self.parent.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.parent.moving:
            self.parent.move(event.globalPos() - self.parent.offset)
