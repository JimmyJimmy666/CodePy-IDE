from PyQt5.QtCore import QSize, Qt, QTimer, QDate, QDateTime, QTime, QUrl, QEvent, QRectF
from PyQt5.QtGui import QIcon, QFont, QColor, QBrush, QPen, QPainter, QPixmap, QImage, QKeyEvent, QMouseEvent, QLinearGradient
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox, QRadioButton, QDateEdit, QTimeEdit, QDateTimeEdit, QSlider, QProgressBar, QHBoxLayout, QVBoxLayout, QGridLayout, QGroupBox, QTabWidget, QMenuBar, QStatusBar, QToolBar, QFileDialog, QMessageBox

class Button(QPushButton):
    def __init__(self, parent, size=[125, 50], postion=[0, 0], color=["#0067C0", "#1975C5", "#3183CA"], text="", border_radius=9, font=QFont("Arial", 16), clickEvent=None, add=""):
        super().__init__(parent)
        self.setGeometry(postion[0], postion[1], size[0], size[1])
        self.setText(text)
        self.setFont(font)
        if clickEvent is not None:
            self.clicked.connect(clickEvent)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color[0]};
                color: white;
                border-radius: {border_radius}px;
                {add}
            }}
            
            QPushButton:hover {{
                background-color: {color[1]};
            }}
            
            QPushButton:pressed {{
                background-color: {color[2]};
            }}
        """)