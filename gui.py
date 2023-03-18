import json
import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

import app
from constants import *


class LazyDialog(QDialog):
    """Main window (view)"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.generalLayout = QVBoxLayout()
        self.subLayout = QHBoxLayout()

        self._createInputField()
        self._addLogging()
        self._createButtons()
        self._createShortcuts()

        self.generalLayout.addLayout(self.subLayout)
        self.setLayout(self.generalLayout)

    def _createInputField(self):
        self.inputField = QTextEdit()
        self.generalLayout.addWidget(self.inputField)

    def _addLogging(self):
        self.logWidget = self.QTextEditLogger()
        self.logWidget.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger().addHandler(self.logWidget)
        logging.getLogger().setLevel(logging.INFO)

        self.subLayout.addWidget(self.logWidget.widget)

    def _createButtons(self):
        self.buttons = {
            "Submit": QPushButton("Submit"),
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
        }

    def clearInput(self):
        """Clear the display."""
        self.inputField.clear()
        self.inputField.setFocus()
        logging.info("cleared")

    def getInput(self):
        return self.inputField.toPlainText()

    class QTextEditLogger(logging.Handler):
        """Logging widget"""

        def __init__(self):
            super().__init__()
            self.widget = QLabel()

        def emit(self, record):
            msg = self.format(record)
            self.widget.setText(msg)


class LazyController:
    """Controller class"""

    def __init__(self, view, model):
        self._view = view
        self._model = model
        self._connectSignalsAndSlots()

    def _connectSignalsAndSlots(self):
        self._view.buttons["Submit"].clicked.connect(self._createNotes)
        self._view.buttons["Clear"].clicked.connect(self._view.clearInput)
		self._view.shortcuts["Ctrl+Return"].activated.connect(self._createNotes)

    def _createNotes(self):
        words = self._view.inputField.toPlainText().split()
        self._model.createNotes(words)
        logging.info("cards created")


class LazyModel:
    """Model class"""

    def __init__(self):
        app.open_anki()
        self._initialize()

    def _initialize(self):
        if MODEL_NAME not in app.invoke("modelNames"):
            app.invoke("createModel", **app.get_model(model_name=MODEL_NAME))
        if DECK_NAME not in app.invoke("deckNames"):
            app.invoke("createDeck", deck=DECK_NAME)

    def createNotes(self, words):
        cache = app.load_cache() if CACHE_ENABLED else {}
        app.invoke("addNotes", notes=app.get_notes(words, cache=cache))
        if CACHE_ENABLED:
            with open(CACHE_PATH, "w", encoding="utf-8") as file:
                json.dump(cache, file, indent=2)


def main():
    app = QApplication([])
    dialog = LazyDialog()
    model = LazyModel()
    controller = LazyController(view=dialog, model=model)

    dialog.show()
    app.exec()


if __name__ == "__main__":
    main()
