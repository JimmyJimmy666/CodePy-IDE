try:
    import sys
    import threading
    import importlib.util
    from PyQt5 import QtCore
    from PyQt5.QtCore import QSize, Qt, QTimer, QDate, QDateTime, QTime, QUrl, QEvent, QRectF, QRegularExpression, QTimer, QRect
    from PyQt5.QtGui import QIcon, QFont, QColor, QBrush, QPen, QPainter, QPixmap, QImage, QKeyEvent, QMouseEvent, QLinearGradient, QSyntaxHighlighter, QTextCharFormat, QTextCursor
    from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox, QRadioButton, QDateEdit, QTimeEdit, QDateTimeEdit, QSlider, QProgressBar, QHBoxLayout, QVBoxLayout, QGridLayout, QGroupBox, QTabWidget, QMenuBar, QStatusBar, QToolBar, QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem, QHeaderView, QPlainTextEdit
    import pathlib
    import os
    from PIL import ImageColor
    import json
    import win32clipboard

    class Create(QWidget):
        def __init__(self, topmenucss="", backgroundcolor="#1F1F1F", font="Microsoft YaHei"):
            super().__init__()

            self.backgroundcolor = backgroundcolor
            self.font = font

            self.folder = pathlib.Path(__file__).parent.resolve()
            self.resize(550, 750)
            self.setWindowIcon(QIcon(os.path.join(self.folder, "image", "icon.ico")))
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setFont(QFont(self.font, 16))

            self.initUi()

        def initUi(self):
            self.topMenu = QWidget(self)
            self.topMenu.setGeometry(0, 0, self.width(), 50)
            self.topMenu.setObjectName("topMenu")
            self.topMenu.setStyleSheet("#topMenu {background-color: #181818;border-top-left-radius: 10px;border-top-right-radius: 10px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;border-bottom: 1.2px solid #454545;}")

            self.closeButton = QPushButton(self.topMenu)
            self.closeButton.setText("✕")
            self.closeButton.setGeometry(self.width() - 65, 0, 65, 49)
            self.closeButton.setFont(QFont(self.font, 15))
            self.closeButton.clicked.connect(self.close)
            self.closeButton.setStyleSheet("QWidget {border-top-left-radius: 0px;border-top-right-radius: 10px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}")

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            rect = QRectF(0, 0, self.width(), self.height())
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0, QColor(*ImageColor.getcolor(self.backgroundcolor, "RGBA")))
            gradient.setColorAt(1, QColor(*ImageColor.getcolor(self.backgroundcolor, "RGBA")))
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

    class LineNumberArea(QWidget):
        def __init__(self, text_edit, color="#969696"):
            super().__init__(text_edit)
            self.text_edit = text_edit
            self.font = self.text_edit.font()
            self.font.setPointSize(11)
            self.setFont(self.font)

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
            self.pairs = {
                '(': ')',
                '[': ']',
                '{': '}',
                '"': '"',
                "'": "'",
                '`': '`'
            }
            
            self.line_number_area = LineNumberArea(self, color)
            self.updateLineNumberAreaWidth()
            self.setLineWrapMode(False)

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
        
        def keyPressEvent(self, event):
            key = event.key()
            text = event.text()
            
            if text in self.pairs:
                cursor = self.textCursor()
                position = cursor.position()
                
                self.insertPlainText(text + self.pairs[text])

                cursor.setPosition(position + 1)
                self.setTextCursor(cursor)
                return

            if key == Qt.Key_Backspace:
                cursor = self.textCursor()
                position = cursor.position()

                if cursor.hasSelection():
                    super().keyPressEvent(event)
                    return

                if position > 0:
                    cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, 1)
                    prev_char = cursor.selectedText()
                    cursor.clearSelection()
                else:
                    prev_char = ""

                if position < len(self.toPlainText()):
                    cursor.setPosition(position)
                    cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)
                    next_char = cursor.selectedText()
                    cursor.clearSelection()
                else:
                    next_char = ""

                if prev_char in self.pairs and next_char == self.pairs[prev_char]:
                    cursor.beginEditBlock()
                    cursor.setPosition(position - 1)
                    cursor.deleteChar()
                    cursor.deleteChar()
                    cursor.endEditBlock()
                    return
            
            super().keyPressEvent(event)

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

        def __init__(self, document, color):
            super().__init__(document)
            self.color = color
            self.initFormats()
            self.initRules()
        
        def initFormats(self):
            self.formats = {
                'keyword': self.createFormat(self.color[0]),
                'bracket': self.createFormat(self.color[1]),
                'string': self.createFormat(self.color[2]),
                'comment': self.createFormat(self.color[3]),
                'true' : self.createFormat(self.color[4]),
                'false' : self.createFormat(self.color[5])
            }

        def createFormat(self, color):
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
            
            true = ['True']
            self.rules += [(QRegularExpression(rf'\b{t}\b'), self.formats['true']) 
                        for t in true]
            
            false = ['False']
            self.rules += [(QRegularExpression(rf'\b{fs}\b'), self.formats['false']) 
                        for fs in false]

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

    class PluginManager(QtCore.QObject):
        plugin_loaded = QtCore.pyqtSignal(str)
        plugin_unloaded = QtCore.pyqtSignal(str)
        plugin_error = QtCore.pyqtSignal(str, str)
        stopRequested = QtCore.pyqtSignal()
        windowStyle = QtCore.pyqtSignal(dict)
        
        def __init__(self, plugin_dir):
            super().__init__()
            self.plugin_dir = plugin_dir
            self.plugins = {}
            self.running = False
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.lock = threading.Lock()
            
        def start(self):
            if not self.running:
                self.running = True
                self.thread.start()
                
        def stop(self):
            self.running = False
            if self.thread.is_alive():
                self.thread.join(timeout=2.0)
                
        def run(self):
            while self.running:
                self.scan_plugins()
                with self.lock:
                    for plugin in self.plugins.values():
                        if hasattr(plugin, 'update'):
                            plugin.update()
                            
        def scan_plugins(self):
            if not os.path.exists(self.plugin_dir):
                os.makedirs(self.plugin_dir, exist_ok=True)
                return
                
            plugin_files = [f for f in os.listdir(self.plugin_dir) 
                        if f.endswith('.py') and not f.startswith('__')]
            
            for file in plugin_files:
                plugin_name = os.path.splitext(file)[0]
                if plugin_name not in self.plugins:
                    self.load_plugin(plugin_name)
                        
        def load_plugin(self, plugin_name):
            plugin_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            plugin_instance = module.Plugin(self)
            with self.lock:
                self.plugins[plugin_name] = plugin_instance
            self.plugin_loaded.emit(plugin_name)
                    
        def exit(self):
            self.stopRequested.emit()

        def setMainWindowStyle(self, arg):
            self.windowStyle.emit(arg)

    class MainWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.configPath = os.path.join(os.path.expanduser("~"), "CodePy")
            self.configG = os.path.join(self.configPath, "config")
            self.configJson = os.path.join(self.configG, "style_config.json")
            self.configSave = os.path.join(self.configG, "path_config.json")
            self.configPlugins = os.path.join(self.configPath, "plugins")
            self.folder_path = ""
            if not os.path.exists(self.configPath):
                os.makedirs(self.configPath, exist_ok=True)
            if not os.path.exists(self.configG):
                os.makedirs(self.configG, exist_ok=True)
            if not os.path.exists(self.configJson):
                self.config = {
                    "MainWindow-Color" : "#1F1F1F",
                    "MainWindow-TextEdit-FontColor" : ["#C586C0", "#179FFF", "#CE9178", "#4EC9B0", "#81B872", "#E94956"],
                    "MainWindow-BorderRadius" : 10,
                    "MainWindow-CommonFont" : "Microsoft YaHei",
                    "MainWindow-FileTree" : "QTreeWidget {background-color: #181818;border: 1.2px solid #181818;border-right: 1.2px solid #454545;outline: 0px;color: white;}QTreeWidget::item {height: 28px;color: white;padding-left: 0px;border-radius: 6px;}QTreeWidget::item:hover {background-color: #2A2D2E;border-radius: 6px;outline: none;padding-left: 0px;color: white;}QTreeWidget::item:selected {border: 1.2px solid #0078D4;background-color: #04395E;color: white;border-radius: 6px;outline: none;padding-left: 0px;}QScrollBar:vertical {background-color: #181818;width: 12px;margin: 10px 0;}QScrollBar::handle:vertical {background-color: #3E3E3E;min-height: 35px;width: 12px;border-radius: 0px;}QScrollBar::handle:vertical:hover {background-color: #4A4A4A;}QScrollBar::handle:vertical:pressed {background-color: #5A5A5A;}QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {background: transparent;}QScrollBar::sub-line:vertical,QScrollBar::add-line:vertical {height: 0px;width: 0px;}QTreeWidget::branch {color: white;}",
                    "MainWindow-TopMenu-CloseButton" : "QWidget {border-top-left-radius: 0px;border-top-right-radius: 10px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;border-top: 1.2px solid #454545;border-right: 1.2px solid #454545;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}",
                    "MainWindow-TopMenu-MaximizeButton" : "QWidget {border-radius: 0px; border-top: 1.2px solid #454545;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}",
                    "MainWindow-TopMenu-MaximizeButton-Maximized" : "QWidget {border-radius: 0px;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}",
                    "MainWindow-TopMenu-MinimizeButton" : "QWidget {border-radius: 0px; border-top: 1.2px solid #454545;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}",
                    "MainWindow-TopMenu-MinimizeButton-Maximized" : "QWidget {border-radius: 0px;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}",
                    "MainWindow-TopMenu-FileButton" : "QWidget {border-radius: 8px;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}",
                    "MainWindow-TopMenu-FileButtonMenu" : "#ButtonMenu { border: 1.2px solid #454545; background-color: #1F1F1F; border-radius: 6px;}",
                    "MainWindow-TopMenu-FileButtonMenu-OpenProject" : "QWidget {border-radius: 6px;}QPushButton {background-color: #1F1F1F;color: #EBEBEB;text-align: left; padding-left: 35px;}QPushButton:hover {background-color: #0377D7;}QPushButton:pressed {background-color: #0377D7;}",
                    "MainWindow-TopMenu-FileButtonMenu-Exit" : "QWidget {border-radius: 6px;}QPushButton {background-color: #1F1F1F;color: #EBEBEB;text-align: left; padding-left: 35px;}QPushButton:hover {background-color: #0377D7;}QPushButton:pressed {background-color: #0377D7;}",
                    "MainWindow-TopMenu-FileButtonMenu-ImportThemeConfig" : "QWidget {border-radius: 6px;}QPushButton {background-color: #1F1F1F;color: #EBEBEB;text-align: left; padding-left: 35px;}QPushButton:hover {background-color: #0377D7;}QPushButton:pressed {background-color: #0377D7;}",
                    "MainWindow-TextEdit": "QPlainTextEdit {background-color: #1F1F1F; border-radius: 0px; color: #B2C4E0; border-right: 1.2px solid #454545;} QScrollBar:horizontal {background-color: transparent; height: 12px; margin: 0 10px;} QScrollBar::handle:horizontal {background-color: #3E3E3E; min-width: 35px; height: 12px; border-radius: 0px;} QScrollBar::handle:horizontal:hover {background-color: #4A4A4A;} QScrollBar::handle:horizontal:pressed {background-color: #5A5A5A;} QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {background: transparent;} QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {width: 0px; height: 0px;} QScrollBar:vertical {background-color: #1F1F1F; width: 12px; margin: 10px 0;} QScrollBar::handle:vertical {background-color: #3E3E3E; min-height: 35px; width: 12px; border-radius: 0px;} QScrollBar::handle:vertical:hover {background-color: #4A4A4A;} QScrollBar::handle:vertical:pressed {background-color: #5A5A5A;} QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {background: transparent;} QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {height: 0px; width: 0px;}",
                    "MainWindow-TextEdit-Maximized": "QPlainTextEdit {background-color: #1F1F1F; border-radius: 0px; color: #B2C4E0;} QScrollBar:horizontal {background-color: transparent; height: 12px; margin: 0 10px;} QScrollBar::handle:horizontal {background-color: #3E3E3E; min-width: 35px; height: 12px; border-radius: 0px;} QScrollBar::handle:horizontal:hover {background-color: #4A4A4A;} QScrollBar::handle:horizontal:pressed {background-color: #5A5A5A;} QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {background: transparent;} QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {width: 0px; height: 0px;} QScrollBar:vertical {background-color: #1F1F1F; width: 12px; margin: 10px 0;} QScrollBar::handle:vertical {background-color: #3E3E3E; min-height: 35px; width: 12px; border-radius: 0px;} QScrollBar::handle:vertical:hover {background-color: #4A4A4A;} QScrollBar::handle:vertical:pressed {background-color: #5A5A5A;} QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {background: transparent;} QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {height: 0px; width: 0px;}",
                    "MainWindow-TopMenu" : "#topMenu {background-color: #181818;border-radius: 10px;border-top-right-radius: 10px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;border: 1.2px solid #454545;}",
                    "MainWindow-TopMenu-Maximized" : "#topMenu {background-color: #181818;border-radius: 0px;border-bottom: 1.2px solid #454545;}",
                    "MainWindow-LeftMenu" : "#leftMenu {background-color: #181818;border-radius: 0px;border-right: 1.2px solid #454545;border-left: 1.2px solid #454545;}",
                    "MainWindow-LeftMenu-Maximized" : "#leftMenu {background-color: #181818;border-radius: 0px;border-right: 1.2px solid #454545;}",
                    "MainWindow-BottomMenu" : "#bottomMenu {background-color: #181818;border-top-left-radius: 0px;border-top-right-radius: 0px;border-bottom-left-radius: 10px;border-bottom-right-radius: 10px;border-top: 1.2px solid #454545;border-right: 1.2px solid #454545;border-left: 1.2px solid #454545;border-bottom: 1.2px solid #454545;}",
                    "MainWindow-BottomMenu-Maximized" : "#bottomMenu {background-color: #181818;border-radius: 0px;border-top: 1.2px solid #454545;}",
                    "MainWindow-TopMenu-CloseButton-Maximized" : "QWidget {border-radius: 0px;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}",
                    "MainWindow-TopMenu-RunButton" : "QWidget {border-radius: 8px;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}",
                    "MainWindow-TopMenu-RunButtonMenu" : "#RunButtonMenu { border: 1.2px solid #454545; background-color: #1F1F1F; border-radius: 6px;}",
                    "MainWindow-TopMenu-RunButtonMenu-RunFile" : "QWidget {border-radius: 6px;}QPushButton {background-color: #1F1F1F;color: #EBEBEB;text-align: left; padding-left: 35px;}QPushButton:hover {background-color: #0377D7;}QPushButton:pressed {background-color: #0377D7;}",
                    "MainWindow-TopMenu-FileButtonMenu-CreateFile" : "QWidget {border-radius: 6px;}QPushButton {background-color: #1F1F1F;color: #EBEBEB;text-align: left; padding-left: 35px;}QPushButton:hover {background-color: #0377D7;}QPushButton:pressed {background-color: #0377D7;}",
                    "MainWindow-TextEdit-FastRunButton" : "QWidget {border-radius: 0px; border-radius: 8px;border-top-right-radius: 0px;border: 1.2px solid #454545;border-top: 0px solid #454545;}QPushButton {background-color: #181818;color: #EBEBEB;}QPushButton:hover {background-color: #262626;}QPushButton:pressed {background-color: #303030;}",
                    "MainWindow-TopMenu-RunButtonMenu-ChoosePyPath" : "QWidget {border-radius: 6px;}QPushButton {background-color: #1F1F1F;color: #EBEBEB;text-align: left; padding-left: 35px;}QPushButton:hover {background-color: #0377D7;}QPushButton:pressed {background-color: #0377D7;}",
                    "MainWindow-TopMenu-ChoosePyPathWidget" : "#ChoosePyPathWidget { border: 1.2px solid #454545; background-color: #1F1F1F; border-radius: 6px;}",
                    "MainWindow-TopMenu-ChoosePyPathWidget-Button" : "QWidget {border-radius: 6px;}QPushButton {background-color: #1F1F1F;color: #EBEBEB;text-align: left; padding-left: 8px;}QPushButton:hover {background-color: #0377D7;}QPushButton:pressed {background-color: #0377D7;}"
                }
                with open(self.configJson, "w", encoding="UTF-8") as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
            else:
                with open(self.configJson, "r", encoding="UTF-8") as f:
                    self.config = json.load(f)
            if not os.path.exists(self.configPlugins):
                os.makedirs(self.configPlugins, exist_ok=True)

            self.isMaximized = False
            self.folder = pathlib.Path(__file__).parent.resolve()
            self.resize(1600, 800)
            self.setWindowIcon(QIcon(os.path.join(self.folder, "image", "icon.ico")))
            self.setWindowFlags(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setFont(self.getFont(16))
            self.initUi()

            self.plugin_manager = PluginManager(self.configPlugins)
            
            self.plugin_manager.stopRequested.connect(self.forceExit)
            self.plugin_manager.windowStyle.connect(self.CssStyle)
            
            self.plugin_manager.start()

            self.auto_save_timer = QTimer(self)
            self.auto_save_timer.timeout.connect(self.auto_save)
            self.auto_save_timer.start(100)

        def auto_save(self):
            if os.path.isfile(self.file_path):
                    with open(self.file_path, "w", encoding="utf-8") as f:
                        f.write(self.textEdit.toPlainText())

        def CssStyle(self, arg):
            self.config = arg
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

            self.tree.setStyleSheet(f"QTreeWidget::branch {{image: none !important;border-image: none !important;background: none;}}QTreeWidget::branch:closed:has-children {{image: url({os.path.join(self.folder, "svg", "branch_closed.svg").replace("\\", "/")});}}QTreeWidget::branch:open:has-children {{image: url({os.path.join(self.folder, "svg", "branch_open.svg").replace("\\", "/")});}}" + self.config["MainWindow-FileTree"])
            self.textEdit.setStyleSheet(self.config["MainWindow-TextEdit"])
            self.fileButton.setStyleSheet(self.config["MainWindow-TopMenu-FileButton"])
            self.fileButtonMenu.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu"])
            self.fileButtonMenuButtonOpenProject.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-OpenProject"])
            self.fileButtonMenuButtonImportThemeConfig.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-ImportThemeConfig"])
            self.minimizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MinimizeButton"])
            self.maximizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MaximizeButton"])
            self.runButton.setStyleSheet(self.config["MainWindow-TopMenu-RunButton"])
            self.runButtonMenu.setStyleSheet(self.config["MainWindow-TopMenu-RunButtonMenu"])
            self.runButtonMenuButtonRunFile.setStyleSheet(self.config["MainWindow-TopMenu-RunButtonMenu-RunFile"])
            self.fastRunButton.setStyleSheet(self.config["MainWindow-TextEdit-FastRunButton"])
            self.ChoosePyPathWidget.setStyleSheet(self.config["MainWindow-TopMenu-ChoosePyPathWidget"])
            self.fileButtonMenuButtonCreateFile.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-CreateFile"])
            self.fileButtonMenuButtonExit.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-Exit"])
            self.runButtonMenuButtonChoosePyPath.setStyleSheet(self.config["MainWindow-TopMenu-RunButtonMenu-ChoosePyPath"])
            for i in range(len(self.pythonList)-1):
                self.buttonList[i].setStyleSheet(self.config["MainWindow-TopMenu-ChoosePyPathWidget-Button"])

            self.setFont(self.getFont(16))
            self.closeButton.setFont(self.getFont(15))
            self.maximizeButton.setFont(self.getFont(25))
            self.minimizeButton.setFont(self.getFont(15))
            self.fileButton.setFont(self.getFont(12))
            self.runButton.setFont(self.getFont(12))
            self.fileButtonMenuButtonOpenProject.setFont(self.getFont(11))
            self.fileButtonMenuButtonImportThemeConfig.setFont(self.getFont(11))
            self.fileButtonMenuButtonCreateFile.setFont(self.getFont(11))
            self.runButtonMenuButtonRunFile.setFont(self.getFont(11))
            self.runButtonMenuButtonChoosePyPath.setFont(self.getFont(11))
            self.textEdit.setFont(self.getFont(11))
            self.pathLabel.setFont(QFont(self.config["MainWindow-CommonFont"], 10))
            self.tree.setFont(QFont(self.config["MainWindow-CommonFont"], 9))
            self.pyPathLabel.setFont(QFont(self.config["MainWindow-CommonFont"], 10))
            self.fastRunButton.setFont(self.getFont(20, True))
            for i in range(len(self.pythonList)-1):
                self.buttonList[i].setFont(QFont(self.config["MainWindow-CommonFont"], 10))

            self.highlighter = PythonHighlighter(self.textEdit.document(), self.config["MainWindow-TextEdit-FontColor"])

        def forceExit(self):
            sys.exit(0)

        def closeEvent(self, event):
            self.plugin_manager.stop()
            super().closeEvent(event)

        def initUi(self):
            self.file_path = ''
            self.topMenu = QWidget(self)
            self.topMenu.setObjectName("topMenu")
            self.leftMenu = QWidget(self)
            self.leftMenu.setObjectName("leftMenu")
            self.bottomMenu = QWidget(self)
            self.bottomMenu.setGeometry(0, self.height()-27, self.width(), 27)
            self.bottomMenu.setObjectName("bottomMenu")
            self.updateTopMenuStyle()

            self.closeButton = QPushButton(self.topMenu)
            self.closeButton.setText("✕")
            self.closeButton.setGeometry(self.width() - 65, 0, 65, 49)
            self.closeButton.setFont(self.getFont(15))
            self.closeButton.clicked.connect(self.cclose)
            self.closeButton.setStyleSheet(self.config["MainWindow-TopMenu-CloseButton"])

            self.maximizeButton = QPushButton(self.topMenu)
            self.maximizeButton.setText("▢")
            self.maximizeButton.setGeometry(self.width() - 65 * 2, 0, 65, 49)
            self.maximizeButton.setFont(self.getFont(25))
            self.maximizeButton.clicked.connect(self.toggleMaximize)
            self.maximizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MaximizeButton"])

            self.minimizeButton = QPushButton(self.topMenu)
            self.minimizeButton.setText("─")
            self.minimizeButton.setGeometry(self.width() - 65 * 3, 0, 65, 49)
            self.minimizeButton.setFont(self.getFont(15))
            self.minimizeButton.clicked.connect(self.min)
            self.minimizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MinimizeButton"])

            self.fileButton = QPushButton(self.topMenu)
            self.fileButton.setText("文件")
            self.fileButton.setGeometry(50, 7, 75, 35)
            self.fileButton.setFont(self.getFont(12))
            self.fileButton.clicked.connect(self.fileButtonMenuOc)
            self.fileButton.setStyleSheet(self.config["MainWindow-TopMenu-FileButton"])

            self.runButton = QPushButton(self.topMenu)
            self.runButton.setText("运行")
            self.runButton.setGeometry(135, 7, 75, 35)
            self.runButton.setFont(self.getFont(12))
            self.runButton.clicked.connect(self.runButtonMenuOc)
            self.runButton.setStyleSheet(self.config["MainWindow-TopMenu-RunButton"])

            self.icon = QLabel(self.topMenu)
            self.icon.setPixmap(QPixmap(os.path.join(self.folder, "image", "icon.png")).scaled(QSize(30,30), Qt.KeepAspectRatio,Qt.SmoothTransformation))
            self.icon.setFixedSize(QSize(30,30))
            self.icon.move(10, 10)

            self.fileButtonMenu = QWidget(self)
            self.fileButtonMenu.setGeometry(self.fileButton.x(), 43, 300, 10+35*4)
            self.fileButtonMenu.setObjectName("ButtonMenu")
            self.fileButtonMenu.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu"])

            self.runButtonMenu = QWidget(self)
            self.runButtonMenu.setGeometry(self.runButton.x(), 43, 300, 10+35*2)
            self.runButtonMenu.setObjectName("RunButtonMenu")
            self.runButtonMenu.setStyleSheet(self.config["MainWindow-TopMenu-RunButtonMenu"])


            self.fileButtonMenuButtonOpenProject  = QPushButton(self.fileButtonMenu)
            self.fileButtonMenuButtonOpenProject.setText("打开项目文件夹")
            self.fileButtonMenuButtonOpenProject.setGeometry(5, 5, 290, 35)
            self.fileButtonMenuButtonOpenProject.setFont(self.getFont(11))
            self.fileButtonMenuButtonOpenProject.clicked.connect(self.openProject)
            self.fileButtonMenuButtonOpenProject.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-OpenProject"])

            self.fileButtonMenuButtonImportThemeConfig  = QPushButton(self.fileButtonMenu)
            self.fileButtonMenuButtonImportThemeConfig.setText("导入主题配置")
            self.fileButtonMenuButtonImportThemeConfig.setGeometry(5, 40, 290, 35)
            self.fileButtonMenuButtonImportThemeConfig.setFont(self.getFont(11))
            self.fileButtonMenuButtonImportThemeConfig.clicked.connect(self.importThemeConfig)
            self.fileButtonMenuButtonImportThemeConfig.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-ImportThemeConfig"])

            self.fileButtonMenuButtonCreateFile  = QPushButton(self.fileButtonMenu)
            self.fileButtonMenuButtonCreateFile.setText("创建新文件")
            self.fileButtonMenuButtonCreateFile.setGeometry(5, 75, 290, 35)
            self.fileButtonMenuButtonCreateFile.setFont(self.getFont(11))
            self.fileButtonMenuButtonCreateFile.clicked.connect(self.createNewFile)
            self.fileButtonMenuButtonCreateFile.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-CreateFile"])

            self.fileButtonMenuButtonExit  = QPushButton(self.fileButtonMenu)
            self.fileButtonMenuButtonExit.setText("退出")
            self.fileButtonMenuButtonExit.setGeometry(5, 110, 290, 35)
            self.fileButtonMenuButtonExit.setFont(self.getFont(11))
            self.fileButtonMenuButtonExit.clicked.connect(self.cclose)
            self.fileButtonMenuButtonExit.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-Exit"])


            self.runButtonMenuButtonRunFile  = QPushButton(self.runButtonMenu)
            self.runButtonMenuButtonRunFile.setText("直接运行此文件")
            self.runButtonMenuButtonRunFile.setGeometry(5, 5, 290, 35)
            self.runButtonMenuButtonRunFile.setFont(self.getFont(11))
            self.runButtonMenuButtonRunFile.clicked.connect(self.runPyFile)
            self.runButtonMenuButtonRunFile.setStyleSheet(self.config["MainWindow-TopMenu-RunButtonMenu-RunFile"])

            self.runButtonMenuButtonChoosePyPath  = QPushButton(self.runButtonMenu)
            self.runButtonMenuButtonChoosePyPath.setText("选择Python路径")
            self.runButtonMenuButtonChoosePyPath.setGeometry(5, 40, 290, 35)
            self.runButtonMenuButtonChoosePyPath.setFont(self.getFont(11))
            self.runButtonMenuButtonChoosePyPath.clicked.connect(self.choosePyPath)
            self.runButtonMenuButtonChoosePyPath.setStyleSheet(self.config["MainWindow-TopMenu-RunButtonMenu-ChoosePyPath"])



            self.textEdit = IgnoreTextEdit(self)
            self.textEdit.setGeometry(440, 50, self.width()-445, self.height()-77)
            self.textEdit.setFont(self.getFont(11))
            self.textEdit.setStyleSheet(self.config["MainWindow-TextEdit"])

            self.pathLabel = QLabel(self.bottomMenu)
            self.pathLabel.setStyleSheet("color:white;")
            self.pathLabel.setFont(self.getFont(10))
            self.pathLabel.setGeometry(10, 0, self.width()//2-25, 25)

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

            if not os.path.exists(self.configSave):
                self.configS = {
                    "workAreaPath" : "",
                    "pythonPath" : ""
                }
                with open(self.configSave, "w", encoding="UTF-8") as f:
                    json.dump(self.configS, f, indent=4, ensure_ascii=False)
            else:
                with open(self.configSave, "r", encoding="UTF-8") as f:
                    self.configS = json.load(f)
                    if self.configS["workAreaPath"] != "":
                        self.loadRootDirectory(self.configS["workAreaPath"])

            self.newFileWin = Create()
            self.newFileWin.resize(550, 750)

            self.pyPathLabel = QLabel(self.bottomMenu)
            self.pyPathLabel.setStyleSheet("color:white;")
            self.pyPathLabel.setFont(self.getFont(10))
            self.pyPathLabel.setGeometry(self.width()-(self.width()//2-25), 0, self.width()//2-25, 25)
            self.pyPathLabel.setAlignment(Qt.AlignRight)
            self.pythonList = os.popen("where python.exe").read().split("\n")
            if len(self.pythonList)-1 > 0:
                if self.configS["pythonPath"] != "":
                    self.pyPathLabel.setText("Python路径: " + self.configS["pythonPath"] + "  ")
                else:
                    self.pyPathLabel.setText("Python路径: " + self.pythonList[0].replace("\\", "/") + "  ")
            
            self.textEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

            self.fastRunButton = QPushButton(self.textEdit)
            self.fastRunButton.setText("▷")
            self.fastRunButton.setGeometry(self.textEdit.width()-80, 0, 65, 35)
            self.fastRunButton.setFont(self.getFont(20, True))
            self.fastRunButton.clicked.connect(self.runPyFile)
            self.fastRunButton.setStyleSheet(self.config["MainWindow-TextEdit-FastRunButton"])

            self.ChoosePyPathWidget = QWidget(self)
            self.ChoosePyPathWidget.setGeometry((self.width()-1200)//2, 43, 1200, 10+35*(len(self.pythonList)-1))
            self.ChoosePyPathWidget.setObjectName("ChoosePyPathWidget")
            self.ChoosePyPathWidget.setStyleSheet(self.config["MainWindow-TopMenu-ChoosePyPathWidget"])
            self.buttonList = []
            self.btny = 5
            if len(self.pythonList)-1 > 0:
                for i in range(len(self.pythonList)-1):
                    self.btn = QPushButton(self.ChoosePyPathWidget)
                    self.btn.setGeometry(5, self.btny, self.ChoosePyPathWidget.width()-10 , 35)
                    self.btn.setStyleSheet(self.config["MainWindow-TopMenu-ChoosePyPathWidget-Button"])
                    self.btn.setFont(self.getFont(10))
                    self.btn.setText(self.pythonList[i].replace("\\", "/"))
                    self.btny += 35
                    self.btn.clicked.connect(lambda checked, idx=i: self.setPyPathText(idx))
                    self.buttonList.append(self.btn)
                    self.btn.hide()

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
            self.runButtonMenu.hide()
            self.runButtonMenu.raise_()
            self.fileButtonMenu.raise_()
            self.highlighter = PythonHighlighter(self.textEdit.document(), self.config["MainWindow-TextEdit-FontColor"])
            self.pathLabel.show()
            self.pyPathLabel.show()
            self.newFileWin.hide()
            self.fastRunButton.raise_()
            self.fastRunButton.show()
            self.ChoosePyPathWidget.hide()
            self.ChoosePyPathWidget.raise_()
            for i in range(len(self.pythonList)-1):
                self.buttonList[i].show()

            self.setFont(self.getFont(16))
            self.closeButton.setFont(self.getFont(15))
            self.maximizeButton.setFont(self.getFont(25))
            self.minimizeButton.setFont(self.getFont(15))
            self.fileButton.setFont(self.getFont(12))
            self.runButton.setFont(self.getFont(12))
            self.fileButtonMenuButtonOpenProject.setFont(self.getFont(11))
            self.fileButtonMenuButtonImportThemeConfig.setFont(self.getFont(11))
            self.fileButtonMenuButtonCreateFile.setFont(self.getFont(11))
            self.runButtonMenuButtonRunFile.setFont(self.getFont(11))
            self.runButtonMenuButtonChoosePyPath.setFont(self.getFont(11))
            self.textEdit.setFont(self.getFont(11))
            self.pathLabel.setFont(QFont(self.config["MainWindow-CommonFont"], 10))
            self.tree.setFont(QFont(self.config["MainWindow-CommonFont"], 9))
            self.pyPathLabel.setFont(QFont(self.config["MainWindow-CommonFont"], 10))
            self.fastRunButton.setFont(self.getFont(20, True))
            for i in range(len(self.pythonList)-1):
                self.buttonList[i].setFont(QFont(self.config["MainWindow-CommonFont"], 10))

        def getFont(self, size, Bold=False):
            if Bold == False:
                font = QFont()
                font.setFamilies(["Consolas", self.config["MainWindow-CommonFont"], "sans-serif"])
                font.setPointSize(size)
                return font
            else:
                font = QFont()
                font.setBold(True)
                font.setFamilies(["Consolas", self.config["MainWindow-CommonFont"], "sans-serif"])
                font.setPointSize(size)
                return font

        def choosePyPath(self):
            if len(self.pythonList)-1 > 0:
                self.ChoosePyPathWidget.show()
            self.runButtonMenu.hide()

        def cclose(self):
            self.close()
            self.newFileWin.close()

        def runPyFile(self):
            self.runButtonMenu.hide()
            if "." + self.file_path.split(".")[-1] == '.py':
                with open(self.file_path, "w", encoding="UTF-8") as f:
                    f.write(self.textEdit.toPlainText())
                os.system(f"{self.pyPathLabel.text().replace("Python路径:", "")} {self.pathLabel.text().replace("路径:", "")}")

        def min(self):
            self.showMinimized()
            self.fileButtonMenu.hide()
            self.runButtonMenu.hide()
            self.ChoosePyPathWidget.hide()

        def createNewFile(self):
            self.fileButtonMenu.hide()
            self.newFileWin.show()
            self.runButtonMenu.hide()
            self.ChoosePyPathWidget.hide()

        def onTreeItemClicked(self, item, column):
            filePath = item.data(0, Qt.UserRole)
            if not filePath:
                return
            textExtensions = ['.txt', '.py', '.c', '.cpp', '.h', '.java', '.html', '.css', '.js', '.json', '.xml', ".ini", ".log", ".text", ".svg", ".mtl", ".obj"]
            if os.path.isfile(filePath):
                self.file_path = filePath
                if os.path.splitext(filePath)[1].lower() in textExtensions:
                    try:
                        with open(filePath, 'r', encoding='UTF-8') as f:
                            self.folder_path = os.path.dirname(filePath)
                            content = f.read()
                            self.textEdit.setPlainText(content)
                    except Exception as e:
                        self.textEdit.setPlainText(f"Error reading file: {str(e)}")
                else:
                    self.textEdit.setPlainText(f"未知文件: {os.path.basename(filePath)}")

                self.pathLabel.setText("路径:  " + self.file_path.replace("\\", "/"))
            elif os.path.isdir(filePath):
                self.folder_path = filePath

        def importThemeConfig(self):
            self.fileButtonMenu.hide()
            self.runButtonMenu.hide()
            self.ChoosePyPathWidget.hide()
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

            self.tree.setStyleSheet(f"QTreeWidget::branch {{image: none !important;border-image: none !important;background: none;}}QTreeWidget::branch:closed:has-children {{image: url({os.path.join(self.folder, "svg", "branch_closed.svg").replace("\\", "/")});}}QTreeWidget::branch:open:has-children {{image: url({os.path.join(self.folder, "svg", "branch_open.svg").replace("\\", "/")});}}" + self.config["MainWindow-FileTree"])
            self.textEdit.setStyleSheet(self.config["MainWindow-TextEdit"])
            self.fileButton.setStyleSheet(self.config["MainWindow-TopMenu-FileButton"])
            self.fileButtonMenu.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu"])
            self.fileButtonMenuButtonOpenProject.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-OpenProject"])
            self.fileButtonMenuButtonImportThemeConfig.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-ImportThemeConfig"])
            self.minimizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MinimizeButton"])
            self.maximizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MaximizeButton"])
            self.runButton.setStyleSheet(self.config["MainWindow-TopMenu-RunButton"])
            self.runButtonMenu.setStyleSheet(self.config["MainWindow-TopMenu-RunButtonMenu"])
            self.runButtonMenuButtonRunFile.setStyleSheet(self.config["MainWindow-TopMenu-RunButtonMenu-RunFile"])
            self.fastRunButton.setStyleSheet(self.config["MainWindow-TextEdit-FastRunButton"])
            self.ChoosePyPathWidget.setStyleSheet(self.config["MainWindow-TopMenu-ChoosePyPathWidget"])
            self.fileButtonMenuButtonCreateFile.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-CreateFile"])
            self.fileButtonMenuButtonExit.setStyleSheet(self.config["MainWindow-TopMenu-FileButtonMenu-Exit"])
            self.runButtonMenuButtonChoosePyPath.setStyleSheet(self.config["MainWindow-TopMenu-RunButtonMenu-ChoosePyPath"])
            for i in range(len(self.pythonList)-1):
                self.buttonList[i].setStyleSheet(self.config["MainWindow-TopMenu-ChoosePyPathWidget-Button"])

            self.setFont(self.getFont(16))
            self.closeButton.setFont(self.getFont(15))
            self.maximizeButton.setFont(self.getFont(25))
            self.minimizeButton.setFont(self.getFont(15))
            self.fileButton.setFont(self.getFont(12))
            self.runButton.setFont(self.getFont(12))
            self.fileButtonMenuButtonOpenProject.setFont(self.getFont(11))
            self.fileButtonMenuButtonImportThemeConfig.setFont(self.getFont(11))
            self.fileButtonMenuButtonCreateFile.setFont(self.getFont(11))
            self.runButtonMenuButtonRunFile.setFont(self.getFont(11))
            self.runButtonMenuButtonChoosePyPath.setFont(self.getFont(11))
            self.textEdit.setFont(self.getFont(11))
            self.pathLabel.setFont(QFont(self.config["MainWindow-CommonFont"], 10))
            self.tree.setFont(QFont(self.config["MainWindow-CommonFont"], 9))
            self.pyPathLabel.setFont(QFont(self.config["MainWindow-CommonFont"], 10))
            self.fastRunButton.setFont(self.getFont(20, True))
            for i in range(len(self.pythonList)-1):
                self.buttonList[i].setFont(QFont(self.config["MainWindow-CommonFont"], 10))

            self.highlighter = PythonHighlighter(self.textEdit.document(), self.config["MainWindow-TextEdit-FontColor"])

        def setPyPathText(self, num):
            self.ChoosePyPathWidget.hide()
            self.pyPathLabel.setText("Python路径: " + self.pythonList[num].replace("\\", "/") + "  ")
            self.configS["pythonPath"] = self.pythonList[num].replace("\\", "/")
            with open(self.configSave, "w", encoding="UTF-8") as f:
                json.dump(self.configS, f, indent=4, ensure_ascii=False)

        def openProject(self):
            self.fileButtonMenu.hide()
            self.runButtonMenu.hide()
            self.ChoosePyPathWidget.hide()
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
            self.folder_path = path.split("\\")[-1]
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
                self.runButtonMenu.hide()
                self.ChoosePyPathWidget.hide()

        def runButtonMenuOc(self):
            if self.runButtonMenu.isVisible():
                self.runButtonMenu.hide()
            else:
                self.runButtonMenu.show()
                self.fileButtonMenu.hide()
                self.ChoosePyPathWidget.hide()
        
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
                self.maximizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MaximizeButton"])
                self.minimizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MinimizeButton"])
                self.textEdit.setStyleSheet(self.config["MainWindow-TextEdit"])
                self.ChoosePyPathWidget.hide()
                self.runButtonMenu.hide()
            else:
                self.showMaximized()
                self.isMaximized = True
                self.closeButton.setStyleSheet(self.config["MainWindow-TopMenu-CloseButton-Maximized"])
                self.maximizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MaximizeButton-Maximized"])
                self.minimizeButton.setStyleSheet(self.config["MainWindow-TopMenu-MinimizeButton-Maximized"])
                self.textEdit.setStyleSheet(self.config["MainWindow-TextEdit-Maximized"])
                self.ChoosePyPathWidget.hide()
                self.runButtonMenu.hide()
            self.updateTopMenuStyle()
            self.update()
        
        def resizeEvent(self, event):
            self.topMenu.setGeometry(0, 0, self.width(), 50)
            self.leftMenu.setGeometry(0, 50, 60, self.height()-77)
            self.bottomMenu.setGeometry(0, self.height()-27, self.width(), 27)
            self.textEdit.setGeometry(440, 50, self.width()-440, self.height()-77)
            self.win.setGeometry(50, 40, 400, self.height()-57)
            self.closeButton.move(self.width() - 65, 0)
            self.maximizeButton.move(self.width() - 65 * 2, 0)
            self.minimizeButton.move(self.width() - 65 * 3, 0)
            self.fileButtonMenu.hide()
            self.pathLabel.setGeometry(10, 0, self.width()//2-25, 25)
            self.pyPathLabel.setGeometry(self.width()-(self.width()//2-25), 0, self.width()//2-25, 25)
            self.fastRunButton.setGeometry(self.textEdit.width()-80, 0, 65, 35)
            self.ChoosePyPathWidget.setGeometry((self.width()-1200)//2, 43, 1200, 10+35*(len(self.pythonList)-1))
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
            if self.runButtonMenu.isVisible():
                if not self.runButtonMenu.geometry().contains(event.pos()):
                    self.runButtonMenu.hide()
            if self.ChoosePyPathWidget.isVisible():
                if not self.ChoosePyPathWidget.geometry().contains(event.pos()):
                    self.ChoosePyPathWidget.hide()

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