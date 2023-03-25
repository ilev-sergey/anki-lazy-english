import functools
import json
import logging

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import app
from constants import *


class Worker(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._task = None

    def setTask(self, task):
        self._task = task

    def run(self):
        if self._task:
            self.started.emit()
            self._task()
            self.finished.emit()


class LazyDialog(QDialog):
    """Main window (view)"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.generalLayout = QVBoxLayout()
        self.subLayout = QHBoxLayout()

        tabs = QTabWidget()
        self.generalLayout.addWidget(tabs)
        tabs.addTab(self._createWordsTab(), "General")

        self._createShortcuts()

        self.setLayout(self.generalLayout)

    def _createWordsTab(self):
        self.wordsLayout = QVBoxLayout()

        self._createInputField()
        self._addLogging()
        self._createButtons()

        self.wordsLayout.addLayout(self.subLayout)

        widget = QWidget()
        widget.setLayout(self.wordsLayout)
        return widget

    def _createInputField(self):
        self.inputField = QTextEdit()
        self.inputField.setPlaceholderText("Write your words (one per line)")
        self.wordsLayout.addWidget(self.inputField)

    def _addLogging(self):
        self.logWidget = self.QTextEditLogger()
        self.logWidget.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger().addHandler(self.logWidget)
        logging.getLogger().setLevel(logging.INFO)

        self.subLayout.addWidget(self.logWidget.widget)

    def _createButtons(self):
        self.buttons = {
            "Submit": QPushButton("Submit"),
            "Upload": QPushButton("Upload"),
            "Clear": QPushButton("Clear"),
        }

        buttonLayout = QHBoxLayout()
        buttonLayout.setAlignment(Qt.AlignmentFlag.AlignRight)

        for button in self.buttons.values():
            buttonLayout.addWidget(button)

        self.subLayout.addLayout(buttonLayout)

    def _createShortcuts(self):
        self.shortcuts = {
            "Ctrl+Return": QShortcut(QKeySequence("Ctrl+Return"), self),
            "Ctrl+O": QShortcut(QKeySequence("Ctrl+O"), self),
        }

    def clearInput(self):
        self.inputField.clear()
        self.setFocusOnInput()
        logging.info("Cleared")

    def getInput(self):
        return self.inputField.toPlainText()

    def setInput(self, text):
        self.inputField.setText(text)
        self.setFocusOnInput()

    def setFocusOnInput(self):
        self.inputField.setFocus()

        cursor = self.inputField.textCursor()
        cursor.setPosition(len(self.inputField.toPlainText()))
        self.inputField.setTextCursor(cursor)

    def disableSubmit(self):
        self.buttons["Submit"].setDisabled(True)

    def enableSubmit(self):
        self.buttons["Submit"].setDisabled(False)

    class QTextEditLogger(logging.Handler):
        """Logging widget"""

        def __init__(self):
            super().__init__()
            self.widget = QLabel()

        def emit(self, record):
            msg = self.format(record)
            self.widget.setText(msg)


def threading(func):
    def wrapper(self, *args, **kwargs):
        funcWithArgs = functools.partial(func, self, *args, **kwargs)
        self.worker.setTask(funcWithArgs)
        self.thread.start()

    return wrapper


class LazyController:
    """Controller class"""

    def __init__(self, view, model):
        self._view = view

        self._initializeThread()
        self._connectSignalsAndSlots()
        self._initializeModel()

    def _initializeThread(self):
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)

    def _connectSignalsAndSlots(self):
        self._view.buttons["Submit"].clicked.connect(
            lambda checked: self.createNotes()  # not to pass checked
        )
        self._view.buttons["Upload"].clicked.connect(self.uploadFile)
        self._view.buttons["Clear"].clicked.connect(self._view.clearInput)

        self._view.shortcuts["Ctrl+Return"].activated.connect(self.createNotes)
        self._view.shortcuts["Ctrl+O"].activated.connect(self.uploadFile)

        self.worker.started.connect(self._view.disableSubmit)
        self.worker.finished.connect(self._view.enableSubmit)

    @threading
    def _initializeModel(self):
        LazyModel._initialize()

    @threading
    def createNotes(self):
        words = self._view.inputField.toPlainText().split()
        LazyModel._createNotes(words)

    def uploadFile(self):
        filename = QFileDialog.getOpenFileName()[0]
        if filename:
            with open(filename) as file:
                words = file.read()
                self._view.setInput(words)


class LazyModel:
    """Model class"""

    @staticmethod
    def _initialize():
        logging.info("Initialization...")
        app.open_anki()
        if MODEL_NAME not in app.invoke("modelNames"):
            app.invoke("createModel", **app.get_model(model_name=MODEL_NAME))
        if DECK_NAME not in app.invoke("deckNames"):
            app.invoke("createDeck", deck=DECK_NAME)
        logging.info("Ready to use")

    @staticmethod
    def _createNotes(words):
        logging.info("Creating cards...")
        cache = app.load_cache() if CACHE_ENABLED else {}
        app.invoke("addNotes", notes=app.get_notes(words, cache=cache))
        if CACHE_ENABLED:
            with open(CACHE_PATH, "w", encoding="utf-8") as file:
                json.dump(cache, file, indent=2)
        logging.info("Сards created")


def main():
    app = QApplication([])
    dialog = LazyDialog()
    controller = LazyController(view=dialog, model=LazyModel)

    dialog.show()
    app.exec()


if __name__ == "__main__":
    main()
