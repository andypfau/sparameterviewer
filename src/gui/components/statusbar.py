from ..helpers.qt_helper import QtHelper
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import logging



class StatusBar(QStatusBar):
        

    clicked = pyqtSignal()


    def __init__(self):
        super().__init__()
        self._ui_icon = QLabel()
        self._ui_text = QLabel()
        self._ui_text.setWordWrap(False)
        self._icon_warning = QtHelper.load_resource_pixmap('status_warning.svg')
        self._icon_error = QtHelper.load_resource_pixmap('status_error.svg')
        self.insertWidget(0, self._ui_icon, 0)
        self.insertWidget(1, self._ui_text, 1)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed))
    

    def setMessage(self, message: str = '', level: int = logging.INFO):
        if not message:
            self.setVisible(False)
            return
        
        if '\n' in message:
            message = message[:message.index('\n')]
        
        if level >= logging.ERROR:
            self._ui_icon.setPixmap(self._icon_error)
            self._ui_icon.setVisible(True)
        elif level >= logging.WARNING:
            self._ui_icon.setPixmap(self._icon_warning)
            self._ui_icon.setVisible(True)
        else:
            self._ui_icon.setVisible(False)
        
        self._ui_text.setText(message)
        self.setVisible(True)


    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)
