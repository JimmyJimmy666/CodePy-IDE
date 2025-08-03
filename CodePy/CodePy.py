import sys
from PyQt5 import QtCore
from PyQt5.QtCore import QSize, Qt, QTimer, QDate, QDateTime, QTime, QUrl, QEvent, QRectF, QRegularExpression
from PyQt5.QtGui import QIcon, QFont, QColor, QBrush, QPen, QPainter, QPixmap, QImage, QKeyEvent, QMouseEvent, QLinearGradient, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox, QRadioButton, QDateEdit, QTimeEdit, QDateTimeEdit, QSlider, QProgressBar, QHBoxLayout, QVBoxLayout, QGridLayout, QGroupBox, QTabWidget, QMenuBar, QStatusBar, QToolBar, QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem, QHeaderView
import pathlib
import os
from PIL import ImageColor
import json

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

class IgnoreTextEdit(QTextEdit):
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        event.ignore()

class IgnoreTreeWidget(QTreeWidget):
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        event.ignore()

class PythonHighlighter(QSyntaxHighlighter):
    STATE_NORMAL = 0
    STATE_TRIPLE_SINGLE = 1
    STATE_TRIPLE_DOUBLE = 2

    def __init__(self, document, color=['#C586C0', '#179FFF', '#CE9178', '#4EC9B0']):
        super().__init__(document)
        self.color = color
        self.initFormats()
        self.initRules()
    
    def initFormats(self):
        self.formats = {
            'keyword': self.createFormat(self.color[0]),
            'bracket': self.createFormat(self.color[1]),
            'string': self.createFormat(self.color[2]),
            'comment': self.createFormat(self.color[3])
        }

    def createFormat(self, color, style=''):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        return fmt

    def initRules(self):
        self.rules = []
        commentPattern = r'#.*$'
        self.rules.append(
            (QRegularExpression(commentPattern), self.formats['comment'])
        )
        keywords = ['import', 'from', 'as']
        self.rules += [(QRegularExpression(rf'\b{kw}\b'), self.formats['keyword']) 
                      for kw in keywords]
        brackets = ['\\(', '\\)', '\\{', '\\}', '\\[', '\\]']
        self.rules += [(QRegularExpression(b), self.formats['bracket']) 
                      for b in brackets]
        self.rules.append((QRegularExpression(r'""".*?"""'), self.formats['string']))
        self.rules.append((QRegularExpression(r"'''.*?'''"), self.formats['string']))
        self.rules.append((QRegularExpression(r'".*?"'), self.formats['string']))
        self.rules.append((QRegularExpression(r"'.*?'"), self.formats['string']))

    def highlightBlock(self, text):
        prevState = self.previousBlockState()
        textLength = len(text)
        startIndex = 0
        if prevState in (self.STATE_TRIPLE_SINGLE, self.STATE_TRIPLE_DOUBLE):
            endIndex = -1
            if prevState == self.STATE_TRIPLE_SINGLE:
                endIndex = text.find("'''")
            else:
                endIndex = text.find('"""')
            if endIndex == -1:
                self.setFormat(0, textLength, self.formats['string'])
                self.setCurrentBlockState(prevState)
                return
            else:
                self.setFormat(0, endIndex + 3, self.formats['string'])
                self.setCurrentBlockState(self.STATE_NORMAL)
                startIndex = endIndex + 3
        while startIndex < textLength:
            startTripleSingle = text.find("'''", startIndex)
            startTripleDouble = text.find('"""', startIndex)
            startQuote = min(
                startTripleSingle if startTripleSingle != -1 else float('inf'),
                startTripleDouble if startTripleDouble != -1 else float('inf')
            )
            if startQuote == float('inf'): 
                break
            if startQuote == startTripleSingle:
                endStr = "'''"
                state = self.STATE_TRIPLE_SINGLE
            else:
                endStr = '"""'
                state = self.STATE_TRIPLE_DOUBLE
            endQuote = text.find(endStr, startQuote + 3)
            if endQuote == -1:
                self.setFormat(startQuote, textLength - startQuote, self.formats['string'])
                self.setCurrentBlockState(state)
                return
            else:
                self.setFormat(startQuote, endQuote - startQuote + 3, self.formats['string'])
                startIndex = endQuote + 3
        for pattern, fmt in self.rules:
            matchIterator = pattern.globalMatch(text, startIndex)
            while matchIterator.hasNext():
                match = matchIterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                if start < startIndex:
                    continue
                self.setFormat(start, length, fmt)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.configPath = os.path.join(os.path.expanduser("~"), "CodePy")
        self.configJson = os.path.join(self.configPath, "config.json")
        self.configSave = os.path.join(self.configPath, "config_save.json")
        self.mainWindowColor = "#1F1F1F"
        self.mainWindowBorderRadius = 15
        self.mainWindowMainMenuColor = "#181818"
        self.mainWindowTopMenuButtonColor = ["#181818", "#262626", "#303030"]
        self.mainWindowButtonMenuButtonColor = ["#1F1F1F", "#0178D5", "#0178D5"]
        self.mainWindowTreeWidgetButtonColor = ["#2A2D2E", "#0078D4", "#04395E", "#181818", "#3E3E3E", "#5A5A5A"]
        self.mainWindowFont = "Microsoft YaHei"
        self.mainWindowTextEditFontcolor = ['#C586C0', '#179FFF', '#CE9178', '#4EC9B0', '#B2C4E0']
        if not os.path.exists(self.configPath):
            self.config = {
                "mainWindowBorderRadius" : 15,
                "mainWindowColor" : "#1F1F1F",
                "mainWindowFont" : "Microsoft YaHei",
                "mainWindowMainMenuColor" : "#181818",
                "mainWindowTopMenuButtonColor" : ["#181818", "#262626", "#303030"],
                "mainWindowButtonMenuButtonColor" : ["#1F1F1F", "#0178D5", "#0178D5"],
                "mainWindowTreeWidgetButtonColor" : ["#2A2D2E", "#0078D4", "#04395E", "#181818", "#3E3E3E", "#5A5A5A"],
                "mainWindowTextEditFontcolor" : ['#C586C0', '#179FFF', '#CE9178', '#4EC9B0', '#B2C4E0']
            }
            os.makedirs(self.configPath, exist_ok=True)
            with open(self.configJson, "w", encoding="UTF-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        else:
            with open(self.configJson, "r", encoding="UTF-8") as f:
                self.config = json.load(f)
            for k, v in self.config.items():
                if k == "mainWindowBorderRadius": self.mainWindowBorderRadius = v
                if k == "mainWindowColor": self.mainWindowColor = v
                if k == "mainWindowFont": self.mainWindowFont = v
                if k == "mainWindowMainMenuColor": self.mainWindowMainMenuColor = v
                if k == "mainWindowTopMenuButtonColor": self.mainWindowTopMenuButtonColor = v
                if k == "mainWindowButtonMenuButtonColor": self.mainWindowButtonMenuButtonColor = v
                if k == "mainWindowTreeWidgetButtonColor" : self.mainWindowTreeWidgetButtonColor = v
                if k == "mainWindowTextEditFontcolor" : self.mainWindowTextEditFontcolor = v
        self.isMaximized = False
        self.folder = pathlib.Path(__file__).parent.resolve()
        self.resize(1600, 800)
        self.setWindowIcon(QIcon(os.path.join(self.folder, "image", "icon.ico")))
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFont(QFont(self.mainWindowFont, 16))
        self.initUi()
        if not os.path.exists(self.configSave):
            self.configS = {
                "workAreaPath" : ""
            }
            with open(self.configSave, "w", encoding="UTF-8") as f:
                json.dump(self.configS, f, indent=4, ensure_ascii=False)
        else:
            with open(self.configSave, "r", encoding="UTF-8") as f:
                self.configS = json.load(f)
                if self.configS["workAreaPath"] != "":
                    self.loadRootDirectory(self.configS["workAreaPath"])

    def initUi(self):
        self.topMenu = QWidget(self)
        self.topMenu.setGeometry(0, 0, self.width(), 50)
        self.topMenu.setObjectName("topMenu")
        self.leftMenu = QWidget(self)
        self.leftMenu.setGeometry(0, 50, 60, self.height()-77)
        self.leftMenu.setObjectName("leftMenu")
        self.bottomMenu = QWidget(self)
        self.bottomMenu.setGeometry(0, self.height()-27, self.width(), 27)
        self.bottomMenu.setObjectName("bottomMenu")
        self.updateTopMenuStyle()
        self.tree = IgnoreTreeWidget(self)
        self.tree.setColumnCount(1)
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet(f"""
            QTreeWidget::branch {{
                image: none !important;
                border-image: none !important;
                background: none;
            }}
            QTreeWidget::branch:closed:has-children {{
                image: url({os.path.join(self.folder, "svg", "branch_closed.svg").replace("\\", "/")});
            }}
            QTreeWidget::branch:open:has-children {{
                image: url({os.path.join(self.folder, "svg", "branch_open.svg").replace("\\", "/")});
            }}
            QTreeWidget {{
                background-color: {self.mainWindowMainMenuColor};
                border: 1.2px solid {self.mainWindowMainMenuColor};
                border-right: 1.2px solid #454545;
                font-family: {self.mainWindowFont};
                font-size: 16px;
                outline: 0px;
                color: white;
            }}
            QTreeWidget::item {{
                height: 28px;
                color: white;
                padding-left: 0px;
            }}
            QTreeWidget::item:hover {{
                background-color: {self.mainWindowTreeWidgetButtonColor[0]};
                border-radius: 0px;
                outline: none;
                padding-left: 0px;
                color: white;
            }}
            QTreeWidget::item:selected {{
                border: 1.2px solid {self.mainWindowTreeWidgetButtonColor[1]};
                background-color: {self.mainWindowTreeWidgetButtonColor[2]};
                color: white;
                border-radius: 0px;
                outline: none;
                padding-left: 0px;
            }}
            QScrollBar:vertical {{
                background-color: {self.mainWindowTreeWidgetButtonColor[3]};
                width: 12px;
                margin: 10px 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.mainWindowTreeWidgetButtonColor[3]};
                min-height: 35px;
                width: 12px;
                border-radius: 0px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.mainWindowTreeWidgetButtonColor[4]};
            }}
            QScrollBar::handle:vertical:pressed {{
                background-color: {self.mainWindowTreeWidgetButtonColor[5]};
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            QScrollBar::sub-line:vertical,
            QScrollBar::add-line:vertical {{
                height: 0px;
                width: 0px;
            }}
            QTreeWidget::branch {{
                color: white;
            }}
        """)
        self.tree.itemExpanded.connect(self.onItemExpanded)
        self.tree.itemCollapsed.connect(self.onItemCollapsed)
        self.tree.itemClicked.connect(self.onTreeItemClicked)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.addWidget(self.tree)
        self.win = QWidget(self)
        self.win.setLayout(self.layout)
        self.win.setGeometry(50, 40, 300, self.height()-57)
        self.closeButton = Button(self.topMenu, text="✕", size=[65, 49], font=QFont(self.mainWindowFont, 15), postion=[self.width() - 65, 0], clickEvent=self.close)
        self.closeButton.setStyleSheet(f"""
            QWidget {{
                border-top-left-radius: 0px;
                border-top-right-radius: {self.mainWindowBorderRadius}px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
            QPushButton {{
                background-color: {self.mainWindowTopMenuButtonColor[0]};
                color: #EBEBEB;
            }}
            QPushButton:hover {{
                background-color: {self.mainWindowTopMenuButtonColor[1]};
            }}
            QPushButton:pressed {{
                background-color: {self.mainWindowTopMenuButtonColor[2]};
            }}
        """)
        self.maximizeButton = Button(self.topMenu, text="▢", size=[65, 49], font=QFont(self.mainWindowFont, 25), postion=[self.width() - 65 * 2, 0], border_radius=0, color=self.mainWindowTopMenuButtonColor, clickEvent=self.toggleMaximize)
        self.minimizeButton = Button(self.topMenu, text="─", size=[65, 49], font=QFont(self.mainWindowFont, 15), postion=[self.width() - 65 * 3, 0], border_radius=0, color=self.mainWindowTopMenuButtonColor, clickEvent=self.min)
        self.fileButton = Button(self.topMenu, text="文件", size=[75, 35], font=QFont(self.mainWindowFont, 12), postion=[50, 7], border_radius=8, color=self.mainWindowTopMenuButtonColor, clickEvent=self.fileButtonMenuOc)
        self.icon = QLabel(self.topMenu)
        self.icon.setPixmap(QPixmap(os.path.join(self.folder, "image", "icon.png")).scaled(QSize(30,30), Qt.KeepAspectRatio,Qt.SmoothTransformation))
        self.icon.setFixedSize(QSize(30,30))
        self.icon.move(10, 10)
        self.fileButtonMenu = QWidget(self)
        self.fileButtonMenu.setGeometry(50, 43, 300, 700)
        self.fileButtonMenu.setObjectName("ButtonMenu")
        self.fileButtonMenu.setStyleSheet(f"#ButtonMenu {{ border: 1.2px solid #454545; background-color: rgba({ImageColor.getcolor(self.mainWindowColor, "RGBA")[0]}, {ImageColor.getcolor(self.mainWindowColor, "RGBA")[1]}, {ImageColor.getcolor(self.mainWindowColor, "RGBA")[2]}, {ImageColor.getcolor(self.mainWindowColor, "RGBA")[3]}); border-radius: 6px; }}")
        self.fileButtonMenuButtonOpenProject  = Button(self.fileButtonMenu, text="打开项目文件夹", size=[290, 35], font=QFont(self.mainWindowFont, 11), postion=[5, 5], border_radius=6, color=self.mainWindowButtonMenuButtonColor, add="text-align: left; padding-left: 35px;", clickEvent=self.openProject)
        self.fileButtonMenuButtonImportThemeConfig = Button(self.fileButtonMenu, text="导入主题配置", size=[290, 35], font=QFont(self.mainWindowFont, 11), postion=[5, 40], border_radius=6, color=self.mainWindowButtonMenuButtonColor, add="text-align: left; padding-left: 35px;", clickEvent=self.importThemeConfig)
        self.textEdit = IgnoreTextEdit(self)
        self.textEdit.setGeometry(440, 50, self.width()-445, self.height()-77)
        self.textEdit.setFont(QFont(self.mainWindowFont, 11))
        self.textEdit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.mainWindowColor};
                border-radius: 0px;
                color: {self.mainWindowTextEditFontcolor[4]};
            }}
            QScrollBar:vertical {{
                background-color: {self.mainWindowColor};
                width: 12px;
                margin: 10px 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.mainWindowColor};
                min-height: 35px;
                width: 12px;
                border-radius: 0px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.mainWindowTreeWidgetButtonColor[4]};
            }}
            QScrollBar::handle:vertical:pressed {{
                background-color: {self.mainWindowTreeWidgetButtonColor[5]};
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            QScrollBar::sub-line:vertical,
            QScrollBar::add-line:vertical {{
                height: 0px;
                width: 0px;
            }}
        """
        )

        self.topMenu.show()
        self.leftMenu.show()
        self.bottomMenu.show()
        self.closeButton.show()
        self.maximizeButton.show()
        self.minimizeButton.show()
        self.icon.show()
        self.fileButtonMenuButtonOpenProject.show()
        self.fileButtonMenuButtonImportThemeConfig.show()
        self.textEdit.show()
        self.fileButtonMenu.hide()
        self.highlighter = PythonHighlighter(self.textEdit.document(), self.mainWindowTextEditFontcolor)

    def min(self):
        self.showMinimized()
        self.fileButtonMenu.hide()

    def onTreeItemClicked(self, item, column):
        filePath = item.data(0, Qt.UserRole)
        if not filePath or not os.path.isfile(filePath):
            return
        textExtensions = ['.txt', '.py', '.c', '.cpp', '.h', '.java', '.html', '.css', '.js', '.json', '.xml', ".ini", ".log", ".text", ".svg", ".mtl", ".obj"]
        if os.path.splitext(filePath)[1].lower() in textExtensions:
            try:
                with open(filePath, 'r', encoding='UTF-8') as f:
                    content = f.read()
                    self.textEdit.setPlainText(content)
            except Exception as e:
                self.textEdit.setPlainText(f"Error reading file: {str(e)}")
        else:
            self.textEdit.setPlainText(f"未知文件: {os.path.basename(filePath)}")

    def importThemeConfig(self):
        self.fileButtonMenu.hide()
        filePath, _ = QFileDialog.getOpenFileName(
            parent=None,
            caption="选择样式配置文件",
            directory="",
            filter="json配置文件 (*.json);;所有文件 (*)"
        )
        if not filePath:
            return
        with open(filePath, "r", encoding="UTF-8") as f:
            self.config = json.load(f)
        with open(filePath, "r", encoding="UTF-8") as f:
            open(self.configJson, "w", encoding="UTF-8").write(f.read())
            for k, v in self.config.items():
                if k == "mainWindowBorderRadius": self.mainWindowBorderRadius = v
                if k == "mainWindowColor": self.mainWindowColor = v
                if k == "mainWindowFont": self.mainWindowFont = v
                if k == "mainWindowMainMenuColor": self.mainWindowMainMenuColor = v
                if k == "mainWindowTopMenuButtonColor": self.mainWindowTopMenuButtonColor = v
                if k == "mainWindowButtonMenuButtonColor": self.mainWindowButtonMenuButtonColor = v
                if k == "mainWindowTreeWidgetButtonColor" : self.mainWindowTreeWidgetButtonColor = v
                if k == "mainWindowTextEditFontcolor" : self.mainWindowTextEditFontcolor = v
            self.tree.setStyleSheet(f"""
                QTreeWidget {{
                    background-color: {self.mainWindowMainMenuColor};
                    border: 1.2px solid {self.mainWindowMainMenuColor};
                    border-right: 1.2px solid #454545;
                    font-family: {self.mainWindowFont};
                    font-size: 14px;
                    outline: 0px;
                    color: white;
                }}
                QTreeWidget::item {{
                    height: 28px;
                    color: white;
                    padding-left: 0px;
                }}
                QTreeWidget::item:hover {{
                    background-color: {self.mainWindowTreeWidgetButtonColor[0]};
                    border-radius: 0px;
                    outline: none;
                    padding-left: 0px;
                    color: white;
                }}
                QTreeWidget::item:selected {{
                    border: 1.2px solid {self.mainWindowTreeWidgetButtonColor[1]};
                    background-color: {self.mainWindowTreeWidgetButtonColor[2]};
                    color: white;
                    border-radius: 0px;
                    outline: none;
                    padding-left: 0px;
                }}
                QScrollBar:vertical {{
                    background-color: {self.mainWindowTreeWidgetButtonColor[3]};
                    width: 12px;
                    margin: 10px 0;
                }}
                QScrollBar::handle:vertical {{
                    background-color: {self.mainWindowTreeWidgetButtonColor[3]};
                    min-height: 35px;
                    width: 12px;
                    border-radius: 0px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background-color: {self.mainWindowTreeWidgetButtonColor[4]};
                }}
                QScrollBar::handle:vertical:pressed {{
                    background-color: {self.mainWindowTreeWidgetButtonColor[5]};
                }}
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {{
                    background: transparent;
                }}
                QScrollBar::sub-line:vertical,
                QScrollBar::add-line:vertical {{
                    height: 0px;
                    width: 0px;
                }}
            """)
            topLeftRadius = 0 if self.isMaximized else self.mainWindowBorderRadius
            topRightRadius = 0 if self.isMaximized else self.mainWindowBorderRadius
            bottomLeftRadius = 0 if self.isMaximized else self.mainWindowBorderRadius
            bottomRightRadius = 0 if self.isMaximized else self.mainWindowBorderRadius
            self.topMenu.setStyleSheet(f"""
                #topMenu {{
                    background-color: {self.mainWindowMainMenuColor};
                    border-top-left-radius: {topLeftRadius}px;
                    border-top-right-radius: {topRightRadius}px;
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                    border-bottom: 1.2px solid #454545;
                }}
            """)
            self.leftMenu.setStyleSheet(f"""
                #leftMenu {{
                    background-color: {self.mainWindowMainMenuColor};
                    border-top-left-radius: 0px;
                    border-top-right-radius: 0px;
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                    border-right: 1.2px solid #454545;
                }}
            """)
            self.bottomMenu.setStyleSheet(f"""
                #bottomMenu {{
                    background-color: {self.mainWindowMainMenuColor};
                    border-top-left-radius: 0px;
                    border-top-right-radius: 0px;
                    border-bottom-left-radius: {bottomLeftRadius}px;
                    border-bottom-right-radius: {bottomRightRadius}px;
                    border-top: 1.2px solid #454545;
                }}
            """)
            if self.isMaximized == False:
                self.closeButton.setStyleSheet(f"""
                    QWidget {{
                        border-top-left-radius: 0px;
                        border-top-right-radius: {self.mainWindowBorderRadius}px;
                        border-bottom-left-radius: 0px;
                        border-bottom-right-radius: 0px;
                    }}
                    QPushButton {{
                        background-color: #181818;
                        color: #EBEBEB;
                    }}
                    QPushButton:hover {{
                        background-color: #262626;
                    }}
                    QPushButton:pressed {{
                        background-color: #303030;
                    }}
                """)
            else:
                self.closeButton.setStyleSheet(f"""
                    QWidget {{
                        border-top-left-radius: 0px;
                        border-top-right-radius: 0px;
                        border-bottom-left-radius: 0px;
                        border-bottom-right-radius: 0px;
                    }}
                    QPushButton {{
                        background-color: #181818;
                        color: #EBEBEB;
                    }}
                    QPushButton:hover {{
                        background-color: #262626;
                    }}
                    QPushButton:pressed {{
                        background-color: #303030;
                    }}
                """)
            self.textEdit.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {self.mainWindowColor};
                    border-radius: 0px;
                    color: {self.mainWindowTextEditFontcolor[4]};
                }}
                QScrollBar:vertical {{
                    background-color: {self.mainWindowColor};
                    width: 12px;
                    margin: 10px 0;
                }}
                QScrollBar::handle:vertical {{
                    background-color: {self.mainWindowColor};
                    min-height: 35px;
                    width: 12px;
                    border-radius: 0px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background-color: {self.mainWindowTreeWidgetButtonColor[4]};
                }}
                QScrollBar::handle:vertical:pressed {{
                    background-color: {self.mainWindowTreeWidgetButtonColor[5]};
                }}
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {{
                    background: transparent;
                }}
                QScrollBar::sub-line:vertical,
                QScrollBar::add-line:vertical {{
                    height: 0px;
                    width: 0px;
                }}
            """
            )
            self.highlighter = PythonHighlighter(self.textEdit.document(), self.mainWindowTextEditFontcolor)


    def openProject(self):
        self.fileButtonMenu.hide()
        folderPath = QFileDialog.getExistingDirectory(
            None, 
            "选择项目文件夹", 
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        if not folderPath:
            return
        self.loadRootDirectory(folderPath)
        self.configS["workAreaPath"] = folderPath
        with open(self.configSave, "w", encoding="UTF-8") as f:
            json.dump(self.configS, f, indent=4, ensure_ascii=False)

    def loadRootDirectory(self, path):
        self.tree.clear()
        rootItem = QTreeWidgetItem(self.tree, [path.split("\\")[-1]])
        rootItem.setData(0, Qt.UserRole, path)
        rootItem.setIcon(0, QIcon.fromTheme("folder"))
        self.addDirectoryChildren(rootItem, path)

    def addDirectoryChildren(self, parentItem, parentPath):
        try:
            self.clearChildren(parentItem, keepPlaceholder=False)
            placeholder = QTreeWidgetItem(parentItem, ["加载中..."])
            placeholder.setData(0, Qt.UserRole, "__placeholder__")
            entries = os.listdir(parentPath)
            for entry in entries[:100]:
                fullPath = os.path.join(parentPath, entry)
                if os.path.isdir(fullPath):
                    child = QTreeWidgetItem(parentItem, [entry])
                    child.setData(0, Qt.UserRole, fullPath)
                    child.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
                    child.setIcon(0, QIcon.fromTheme("folder"))
                    subPlaceholder = QTreeWidgetItem(child, ["加载中..."])
                    subPlaceholder.setData(0, Qt.UserRole, "__placeholder__")
                else:
                    filename, ext = os.path.splitext(entry)
                    if ext:
                        displayName = f"{filename}{ext}"
                    else:
                        displayName = entry
                    fileItem = QTreeWidgetItem(parentItem, [displayName])
                    fileItem.setData(0, Qt.UserRole, fullPath)
                    fileItem.setIcon(0, QIcon.fromTheme("text-x-generic"))
        except PermissionError:
            pass
        finally:
            self.removePlaceholders(parentItem)

    def removePlaceholders(self, parentItem):
        for i in range(parentItem.childCount()-1, -1, -1):
            item = parentItem.child(i)
            if item.data(0, Qt.UserRole) == "__placeholder__":
                parentItem.removeChild(item)

    def clearChildren(self, parentItem, keepPlaceholder=False):
        for i in range(parentItem.childCount()-1, -1, -1):
            item = parentItem.child(i)
            if keepPlaceholder and item.data(0, Qt.UserRole) == "__placeholder__":
                continue
            parentItem.removeChild(item)

    def onItemExpanded(self, item):
        path = item.data(0, Qt.UserRole)
        if path and os.path.isdir(path):
            self.clearChildren(item, keepPlaceholder=False)
            self.addDirectoryChildren(item, path)

    def onItemCollapsed(self, item):
        self.clearChildren(item, keepPlaceholder=True)
        if item.childCount() == 0:
            placeholder = QTreeWidgetItem(item, ["加载中..."])
            placeholder.setData(0, Qt.UserRole, "__placeholder__")

    def fileButtonMenuOc(self):
        if self.fileButtonMenu.isVisible():
            self.fileButtonMenu.hide()
        else:
            self.fileButtonMenu.show()
    
    def updateTopMenuStyle(self):
        topLeftRadius = 0 if self.isMaximized else self.mainWindowBorderRadius
        topRightRadius = 0 if self.isMaximized else self.mainWindowBorderRadius
        bottomLeftRadius = 0 if self.isMaximized else self.mainWindowBorderRadius
        bottomRightRadius = 0 if self.isMaximized else self.mainWindowBorderRadius
        self.topMenu.setStyleSheet(f"""
            #topMenu {{
                background-color: {self.mainWindowMainMenuColor};
                border-top-left-radius: {topLeftRadius}px;
                border-top-right-radius: {topRightRadius}px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                border-bottom: 1.2px solid #454545;
            }}
        """)
        self.leftMenu.setStyleSheet(f"""
            #leftMenu {{
                background-color: {self.mainWindowMainMenuColor};
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                border-right: 1.2px solid #454545;
            }}
        """)
        self.bottomMenu.setStyleSheet(f"""
            #bottomMenu {{
                background-color: {self.mainWindowMainMenuColor};
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: {bottomLeftRadius}px;
                border-bottom-right-radius: {bottomRightRadius}px;
                border-top: 1.2px solid #454545;
            }}
        """)
    
    def toggleMaximize(self):
        if self.isMaximized:
            self.showNormal()
            self.isMaximized = False
            self.closeButton.setStyleSheet(f"""
                QWidget {{
                    border-top-left-radius: 0px;
                    border-top-right-radius: {self.mainWindowBorderRadius}px;
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                }}
                QPushButton {{
                    background-color: #181818;
                    color: #EBEBEB;
                }}
                QPushButton:hover {{
                    background-color: #262626;
                }}
                QPushButton:pressed {{
                    background-color: #303030;
                }}
            """)
        else:
            self.showMaximized()
            self.isMaximized = True
            self.closeButton.setStyleSheet(f"""
                QWidget {{
                    border-top-left-radius: 0px;
                    border-top-right-radius: 0px;
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                }}
                QPushButton {{
                    background-color: #181818;
                    color: #EBEBEB;
                }}
                QPushButton:hover {{
                    background-color: #262626;
                }}
                QPushButton:pressed {{
                    background-color: #303030;
                }}
            """)
        self.updateTopMenuStyle()
        self.update()
    
    def resizeEvent(self, event):
        self.topMenu.setGeometry(0, 0, self.width(), 50)
        self.leftMenu.setGeometry(0, 50, 60, self.height()-77)
        self.bottomMenu.setGeometry(0, self.height()-27, self.width(), 27)
        self.textEdit.setGeometry(440, 50, self.width()-445, self.height()-77)
        self.win.setGeometry(50, 40, 400, self.height()-57)
        self.closeButton.move(self.width() - 65, 0)
        self.maximizeButton.move(self.width() - 65 * 2, 0)
        self.minimizeButton.move(self.width() - 65 * 3, 0)
        self.fileButtonMenu.hide()
        self.updateTopMenuStyle()
        super().resizeEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height())
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor(*ImageColor.getcolor(self.mainWindowColor, "RGBA")))
        gradient.setColorAt(1, QColor(*ImageColor.getcolor(self.mainWindowColor, "RGBA")))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        if self.isMaximized == False:
            painter.drawRoundedRect(rect, self.mainWindowBorderRadius, self.mainWindowBorderRadius)
        else:
            painter.drawRoundedRect(rect, 0, 0)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if event.pos().y() < 50:
                self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
            else:
                super().mousePressEvent(event)

        if self.fileButtonMenu.isVisible():
            if not self.fileButtonMenu.geometry().contains(event.pos()):
                self.fileButtonMenu.hide()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_start_position') and event.buttons() == Qt.LeftButton:
            if event.pos().y() < 50:
                self.move(event.globalPos() - self.drag_start_position)
                event.accept()
        else:
            super().mouseMoveEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())