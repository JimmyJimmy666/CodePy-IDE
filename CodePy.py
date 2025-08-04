try:
    import sys
    from PyQt5 import QtCore
    from PyQt5.QtCore import QSize, Qt, QTimer, QDate, QDateTime, QTime, QUrl, QEvent, QRectF, QRegularExpression, QTimer, QRect
    from PyQt5.QtGui import QIcon, QFont, QColor, QBrush, QPen, QPainter, QPixmap, QImage, QKeyEvent, QMouseEvent, QLinearGradient, QSyntaxHighlighter, QTextCharFormat
    from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox, QRadioButton, QDateEdit, QTimeEdit, QDateTimeEdit, QSlider, QProgressBar, QHBoxLayout, QVBoxLayout, QGridLayout, QGroupBox, QTabWidget, QMenuBar, QStatusBar, QToolBar, QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem, QHeaderView, QPlainTextEdit
    import pathlib
    import os
    from PIL import ImageColor
    import json
    import win32clipboard

    class LineNumberArea(QWidget):
        def __init__(self, text_edit, color="#969696"):
            super().__init__(text_edit)
            self.text_edit = text_edit

        def sizeHint(self):
            return QSize(90, 0)

        def paintEvent(self, event):
            painter = QPainter(self)
            
            block = self.text_edit.firstVisibleBlock()
            block_number = block.blockNumber()
            top = self.text_edit.blockBoundingGeometry(block).translated(self.text_edit.contentOffset()).top()
            bottom = top + self.text_edit.blockBoundingRect(block).height()

            font_metrics = self.text_edit.fontMetrics()
            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    number = str(block_number + 1)
                    painter.setPen(QColor("#969696"))
                    painter.drawText(0, int(top), self.width() // 2 + 10, font_metrics.height(), Qt.AlignRight, number)
                
                block = block.next()
                top = bottom
                bottom = top + self.text_edit.blockBoundingRect(block).height()
                block_number += 1

    class IgnoreTextEdit(QPlainTextEdit):
        def __init__(self, parent=None, color="#969696"):
            super().__init__(parent)
            self.line_number_area = LineNumberArea(self, color)
            self.updateLineNumberAreaWidth()

            self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
            self.updateRequest.connect(self.updateLineNumberArea)

        def updateLineNumberAreaWidth(self):
            self.setViewportMargins(self.line_number_area.sizeHint().width(), 0, 0, 0)

        def updateLineNumberArea(self, rect, dy):
            if dy:
                self.line_number_area.scroll(0, dy)
            else:
                self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
            
            if rect.contains(self.viewport().rect()):
                self.updateLineNumberAreaWidth()

        def resizeEvent(self, event):
            super().resizeEvent(event)
            cr = self.contentsRect()
            self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area.sizeHint().width(), cr.height()))

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
            if not os.path.exists(self.configPath):
                self.config = {
                    "MainWindow-Color" : "#1F1F1F",
                    "MainWindow-TextEdit-FontColor" : ["#C586C0", "#179FFF", "#CE9178", "#4EC9B0"],
                    "MainWindow-BorderRadius" : 10,
                    "MainWindow-CommonFont" : "Microsoft YaHei",
                    "MainWindow-FileTree" : "QTreeWidget {background-color: #181818;border: 1.2px solid #181818;border-right: 1.2px solid #454545;outline: 0px;color: white;}QTreeWidget::item {height: 28px;color: white;padding-left: 0px;}QTreeWidget::item:hover {background-color: #2A2D2E;border-radius: 0px;outline: none;padding-left: 0px;color: white;}QTreeWidget::item:selected {border: 1.2px solid #0078D4;background-color: #04395E;color: white;border-radius: 0px;outline: none;padding-left: 0px;}QScrollBar:vertical {background-color: #181818;width: 12px;margin: 10px 0;}QScrollBar::handle:vertical {background-color: #181818;min-height: 35px;width: 12px;border-radius: 0px;}QScrollBar::handle:vertical:hover {background-color: #3E3E3E;}QScrollBar::handle:vertical:pressed {background-color: #5A5A5A;}QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {background: transparent;}QScrollBar::sub-line:vertical,QScrollBar::add-line:vertical {height: 0px;width: 0px;}QTreeWidget::branch {color: white;}",
                    "MainWindow-TopMenu-CloseButton" : "QWidget {border-top-left-radius: 0px;border-top-right-radius: 10px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}",
                    "MainWindow-TopMenu-MaximizeButton" : "QWidget {border-radius: 0px;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}",
                    "MainWindow-TopMenu-MinimizeButton" : "QWidget {border-radius: 0px;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}",
                    "MainWindow-TopMenu-FileButton" : "QWidget {border-radius: 8px;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}",
                    "MainWindow-TopMenu-FileButtonMenu" : "#ButtonMenu { border: 1.2px solid #454545; background-color: #1F1F1F; border-radius: 6px;}",
                    "MainWindow-TopMenu-FileButtonMenu-OpenProject" : "QWidget {border-radius: 6px;}QPushButton {background-color: #1F1F1F;color: #EBEBEB;text-align: left; padding-left: 35px;}QPushButton:hover {background-color: #0377D7;}QPushButton:pressed {background-color: #0377D7;}",
                    "MainWindow-TopMenu-FileButtonMenu-ImportThemeConfig" : "QWidget {border-radius: 6px;}QPushButton {background-color: #1F1F1F;color: #EBEBEB;text-align: left; padding-left: 35px;}QPushButton:hover {background-color: #0377D7;}QPushButton:pressed {background-color: #0377D7;}",
                    "MainWindow-TextEdit" : "QPlainTextEdit {background-color: #1F1F1F;border-radius: 0px;color: #B2C4E0;}QScrollBar:vertical {background-color: #1F1F1F;width: 12px;margin: 10px 0;}QScrollBar::handle:vertical {background-color: #1F1F1F;min-height: 35px;width: 12px;border-radius: 0px;}QScrollBar::handle:vertical:hover {background-color: #3E3E3E;}QScrollBar::handle:vertical:pressed {background-color: #5A5A5A;}QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {background: transparent;}QScrollBar::sub-line:vertical,QScrollBar::add-line:vertical {height: 0px;width: 0px;}",
                    "MainWindow-TopMenu" : "#topMenu {background-color: #181818;border-top-left-radius: 10px;border-top-right-radius: 10px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;border-bottom: 1.2px solid #454545;}",
                    "MainWindow-TopMenu-Maximized" : "#topMenu {background-color: #181818;border-radius: 0px;border-bottom: 1.2px solid #454545;}",
                    "MainWindow-LeftMenu" : "#leftMenu {background-color: #181818;border-radius: 0px;border-right: 1.2px solid #454545;}",
                    "MainWindow-LeftMenu-Maximized" : "#leftMenu {background-color: #181818;border-radius: 0px;border-right: 1.2px solid #454545;}",
                    "MainWindow-BottomMenu" : "#bottomMenu {background-color: #181818;border-top-left-radius: 0px;border-top-right-radius: 0px;border-bottom-left-radius: 10px;border-bottom-right-radius: 10px;border-top: 1.2px solid #454545;}",
                    "MainWindow-BottomMenu-Maximized" : "#bottomMenu {background-color: #181818;border-radius: 0px;border-top: 1.2px solid #454545;}",
                    "MainWindow-TopMenu-CloseButton-Maximized" : "QWidget {border-radius: 0px;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}"
                }
                os.makedirs(self.configPath, exist_ok=True)
                with open(self.configJson, "w", encoding="UTF-8") as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
            else:
                with open(self.configJson, "r", encoding="UTF-8") as f:
                    self.config = json.load(f)

            self.isMaximized = False
            self.folder = pathlib.Path(__file__).parent.resolve()
            self.resize(1600, 800)
            self.setWindowIcon(QIcon(os.path.join(self.folder, "image", "icon.ico")))
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setFont(QFont(self.config["MainWindow-CommonFont"], 16))
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

            self.autoSaveInterval = 1

            self.autoSaveTimer = QTimer(self)
            self.autoSaveTimer.timeout.connect(self.autoSaveIfModified)
            self.autoSaveTimer.start(self.autoSaveInterval * 1000)

        def autoSaveIfModified(self):
            if self.file_path:
                with open(self.file_path, "w", encoding="UTF-8") as f:
                    f.write(self.textEdit.toPlainText())

        def initUi(self):
            self.file_path = ''
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
            self.tree.setStyleSheet(f"QTreeWidget::branch {{image: none !important;border-image: none !important;background: none;}}QTreeWidget::branch:closed:has-children {{image: url({os.path.join(self.folder, "svg", "branch_closed.svg").replace("\\", "/")});}}QTreeWidget::branch:open:has-children {{image: url({os.path.join(self.folder, "svg", "branch_open.svg").replace("\\", "/")});}}" + self.config["MainWindow-FileTree"])
            self.tree.setFont(QFont(self.config["MainWindow-CommonFont"], 9))

            self.tree.itemExpanded.connect(self.onItemExpanded)
            self.tree.itemCollapsed.connect(self.onItemCollapsed)
            self.tree.itemClicked.connect(self.onTreeItemClicked)
            self.layout = QVBoxLayout(self)
            self.layout.setContentsMargins(10, 10, 10, 10)
            self.layout.addWidget(self.tree)
            self.win = QWidget(self)
            self.win.setLayout(self.layout)
            self.win.setGeometry(50, 40, 300, self.height()-57)

            self.closeButton = QPushButton(self.topMenu)
            self.closeButton.setText("✕")
            self.closeButton.setGeometry(self.width() - 65, 0, 65, 49)
            self.closeButton.setFont(QFont(self.config["MainWindow-CommonFont"], 15))
            self.closeButton.clicked.connect(self.close)
            self.closeButton.setStyleSheet(self.config["MainWindow-TopMenu-CloseButton"])

            self.maximizeButton = QPushButton(self.topMenu)
            self.maximizeButton.setText("▢")
            self.maximizeButton.setGeometry(self.width() - 65 * 2, 0, 65, 49)
            self.maximizeButton.setFont(QFont(self.config["MainWindow-CommonFont"], 25))
            self.maximizeButton.clicked.connect(self.toggleMaximize)
            self.maximizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MaximizeButton"])

            self.minimizeButton = QPushButton(self.topMenu)
            self.minimizeButton.setText("─")
            self.minimizeButton.setGeometry(self.width() - 65 * 3, 0, 65, 49)
            self.minimizeButton.setFont(QFont(self.config["MainWindow-CommonFont"], 15))
            self.minimizeButton.clicked.connect(self.min)
            self.minimizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MinimizeButton"])

            self.fileButton = QPushButton(self.topMenu)
            self.fileButton.setText("文件")
            self.fileButton.setGeometry(50, 7, 75, 35)
            self.fileButton.setFont(QFont(self.config["MainWindow-CommonFont"], 12))
            self.fileButton.clicked.connect(self.fileButtonMenuOc)
            self.fileButton.setStyleSheet(self.config["MainWindow-TopMenu-FileButton"])

            self.icon = QLabel(self.topMenu)
            self.icon.setPixmap(QPixmap(os.path.join(self.folder, "image", "icon.png")).scaled(QSize(30,30), Qt.KeepAspectRatio,Qt.SmoothTransformation))
            self.icon.setFixedSize(QSize(30,30))
            self.icon.move(10, 10)
            self.fileButtonMenu = QWidget(self)
            self.fileButtonMenu.setGeometry(50, 43, 300, 700)
            self.fileButtonMenu.setObjectName("ButtonMenu")
            self.fileButtonMenu.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu"])

            self.fileButtonMenuButtonOpenProject  = QPushButton(self.fileButtonMenu)
            self.fileButtonMenuButtonOpenProject.setText("打开项目文件夹")
            self.fileButtonMenuButtonOpenProject.setGeometry(5, 5, 290, 35)
            self.fileButtonMenuButtonOpenProject.setFont(QFont(self.config["MainWindow-CommonFont"], 11))
            self.fileButtonMenuButtonOpenProject.clicked.connect(self.openProject)
            self.fileButtonMenuButtonOpenProject.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-OpenProject"])

            self.fileButtonMenuButtonImportThemeConfig  = QPushButton(self.fileButtonMenu)
            self.fileButtonMenuButtonImportThemeConfig.setText("导入主题配置")
            self.fileButtonMenuButtonImportThemeConfig.setGeometry(5, 40, 290, 35)
            self.fileButtonMenuButtonImportThemeConfig.setFont(QFont(self.config["MainWindow-CommonFont"], 11))
            self.fileButtonMenuButtonImportThemeConfig.clicked.connect(self.importThemeConfig)
            self.fileButtonMenuButtonImportThemeConfig.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-ImportThemeConfig"])

            self.textEdit = IgnoreTextEdit(self)
            self.textEdit.setGeometry(440, 50, self.width()-445, self.height()-77)
            self.textEdit.setFont(QFont(self.config["MainWindow-CommonFont"], 11))
            self.textEdit.setStyleSheet(self.config["MainWindow-TextEdit"])

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
            self.highlighter = PythonHighlighter(self.textEdit.document(), self.config["MainWindow-TextEdit-FontColor"])

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
                        self.file_path = filePath
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

                if self.isMaximized:
                    self.topMenu.setStyleSheet(self.config["MainWindow-TopMenu-Maximized"])
                    self.leftMenu.setStyleSheet(self.config["MainWindow-LeftMenu-Maximized"])
                    self.bottomMenu.setStyleSheet(self.config["MainWindow-BottomMenu-Maximized"])
                    self.closeButton.setStyleSheet(self.config["MainWindow-TopMenu-CloseButton-Maximized"])
                else:
                    self.topMenu.setStyleSheet(self.config["MainWindow-TopMenu"])
                    self.leftMenu.setStyleSheet(self.config["MainWindow-LeftMenu"])
                    self.bottomMenu.setStyleSheet(self.config["MainWindow-BottomMenu"])
                    self.closeButton.setStyleSheet(self.config["MainWindow-TopMenu-CloseButton"])

                self.tree.setStyleSheet(self.config["MainWindow-FileTree"])
                self.textEdit.setStyleSheet(self.config["MainWindow-TextEdit"])
                self.fileButton.setStyleSheet(self.config["MainWindow-TopMenu-FileButton"])
                self.fileButtonMenu.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu"])
                self.fileButtonMenuButtonOpenProject.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-OpenProject"])
                self.fileButtonMenuButtonImportThemeConfig.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-ImportThemeConfig"])
                self.minimizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MinimizeButton"])
                self.maximizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MaximizeButton"])

                self.highlighter = PythonHighlighter(self.textEdit.document(), self.config["MainWindow-TextEdit-FontColor"])


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
            if self.isMaximized:
                self.topMenu.setStyleSheet(self.config["MainWindow-TopMenu-Maximized"])
                self.leftMenu.setStyleSheet(self.config["MainWindow-LeftMenu-Maximized"])
                self.bottomMenu.setStyleSheet(self.config["MainWindow-BottomMenu-Maximized"])
            else:
                self.topMenu.setStyleSheet(self.config["MainWindow-TopMenu"])
                self.leftMenu.setStyleSheet(self.config["MainWindow-LeftMenu"])
                self.bottomMenu.setStyleSheet(self.config["MainWindow-BottomMenu"])
        
        def toggleMaximize(self):
            if self.isMaximized:
                self.showNormal()
                self.isMaximized = False
                self.closeButton.setStyleSheet(self.config["MainWindow-TopMenu-CloseButton"])
            else:
                self.showMaximized()
                self.isMaximized = True
                self.closeButton.setStyleSheet(self.config["MainWindow-TopMenu-CloseButton-Maximized"])
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
            gradient.setColorAt(0, QColor(*ImageColor.getcolor(self.config["MainWindow-Color"], "RGBA")))
            gradient.setColorAt(1, QColor(*ImageColor.getcolor(self.config["MainWindow-Color"], "RGBA")))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            if self.isMaximized == False:
                painter.drawRoundedRect(rect, self.config["MainWindow-BorderRadius"], self.config["MainWindow-BorderRadius"])
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

except Exception as e:
    class ErrorWindow(QWidget):
        def __init__(self):
            super().__init__()

            self.folder = pathlib.Path(__file__).parent.resolve()
            self.resize(550, 750)
            self.setWindowIcon(QIcon(os.path.join(self.folder, "image", "icon.ico")))
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setFont(QFont("Arial", 16))

            self.initUi()

        def initUi(self):
            self.topMenu = QWidget(self)
            self.topMenu.setGeometry(0, 0, self.width(), 50)
            self.topMenu.setObjectName("topMenu")
            self.topMenu.setStyleSheet("#topMenu {background-color: #181818;border-top-left-radius: 10px;border-top-right-radius: 10px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;border-bottom: 1.2px solid #454545;}")

            self.closeButton = QPushButton(self.topMenu)
            self.closeButton.setText("✕")
            self.closeButton.setGeometry(self.width() - 65, 0, 65, 49)
            self.closeButton.setFont(QFont("Microsoft YaHei", 15))
            self.closeButton.clicked.connect(self.close)
            self.closeButton.setStyleSheet("QWidget {border-top-left-radius: 0px;border-top-right-radius: 10px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}")

            self.errorLabel = QLabel(self)
            self.errorLabel.setGeometry(10, 60, 530, 680)
            self.errorLabel.setFont(QFont("Microsoft YaHei", 15))
            self.errorLabel.setWordWrap(True)
            self.errorLabel.setStyleSheet("color:white;")
            self.errorLabel.setText(f"出现问题，具体报错：\n{e}")
            self.errorLabel.setAlignment(Qt.AlignLeft | Qt.AlignTop)

            self.copyButton = QPushButton(self)
            self.copyButton.setText("复制")
            self.copyButton.setGeometry(10, 7, 75, 35)
            self.copyButton.setFont(QFont("Microsoft YaHei", 12))
            self.copyButton.clicked.connect(self.copyError)
            self.copyButton.setStyleSheet("QWidget {border-radius: 6px;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}")

        def copyError(self):
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(str(e))
            win32clipboard.CloseClipboard()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            rect = QRectF(0, 0, self.width(), self.height())
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0, QColor(*ImageColor.getcolor("#1F1F1F", "RGBA")))
            gradient.setColorAt(1, QColor(*ImageColor.getcolor("#1F1F1F", "RGBA")))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            
            painter.drawRoundedRect(rect, 10, 10)

        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                if event.pos().y() < 50:
                    self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
                    event.accept()
                else:
                    super().mousePressEvent(event)

        def mouseMoveEvent(self, event):
            if hasattr(self, 'drag_start_position') and event.buttons() == Qt.LeftButton:
                if event.pos().y() < 50:
                    self.move(event.globalPos() - self.drag_start_position)
                    event.accept()
            else:
                super().mouseMoveEvent(event)

    if __name__ == '__main__':
        window = ErrorWindow()
        window.show()
        sys.exit(app.exec_())