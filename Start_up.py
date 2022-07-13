from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer, Qt, QThreadPool, QRunnable
from PyQt5.QtWidgets import QFileDialog, QLabel, QVBoxLayout, QWidget, QDesktopWidget

class startup_window(QWidget):
    def __init__(self):
        super().__init__()
        pixmap = QtGui.QPixmap('startup.png')
        pixmap = pixmap.scaled(600,600)
        self.label = QLabel()
        self.label.setPixmap(pixmap)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.setGeometry(0,0,600,600)
        qtrect = self.frameGeometry()
        qtrect.moveCenter(QDesktopWidget().availableGeometry().center())
        self.move(qtrect.topLeft())
        self.setWindowTitle('flow software loading...')
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowIcon(QtGui.QIcon('cells.png'))
        return
