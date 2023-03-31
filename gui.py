import functools
import json
import logging
import shutil
from pathlib import Path

import yaml
from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import app
from constants import *

modelName = MODEL_NAME
deckName = DECK_NAME
cacheEnabled = CACHE_ENABLED
cachePath = CACHE_PATH


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
        self.setWindowIcon(QIcon("assets/logo.jpg"))

        generalLayout = QVBoxLayout()
        tabs = QTabWidget()
        self.setLayout(generalLayout)

        generalLayout.addWidget(tabs)

        tabs.addTab(self._createWordsTab(), "General")
        tabs.addTab(self._createSettingsTab(), "Settings")
        tabs.addTab(self._createAdvancedTab(), "Advanced")

        self._createShortcuts()

    def _createWordsTab(self):
        wordsLayout = QVBoxLayout()
        subLayout = QHBoxLayout()

        wordsLayout.addWidget(self._createInputField())
        wordsLayout.addLayout(subLayout)

        subLayout.addWidget(self._createLogWidget())
        subLayout.addLayout(self._createButtonsLayout())

        widget = QWidget()
        widget.setLayout(wordsLayout)
        return widget

    def _createSettingsTab(self):
        settingsLayout = QVBoxLayout()
        settingsSubLayout = QHBoxLayout()
        self.settingsLabel = QLabel()

        settingsLayout.addLayout(self._createSettingsFormLayout())
        settingsLayout.addLayout(self._createSettingsDictionariesLayout())
        settingsLayout.addLayout(settingsSubLayout)

        settingsSubLayout.addWidget(self.settingsLabel)
        settingsSubLayout.addLayout(self._createSettingsButtonsLayout())

        widget = QWidget()
        widget.setLayout(settingsLayout)
        return widget

    def _createAdvancedTab(self):
        advancedLayout = QVBoxLayout()

        advancedLayout.addLayout(self._createAdvancedButtonsLayout())

        widget = QWidget()
        widget.setLayout(advancedLayout)
        return widget

    def _createShortcuts(self):
        self.shortcuts = {
            "Ctrl+Return": QShortcut(QKeySequence("Ctrl+Return"), self),
            "Ctrl+O": QShortcut(QKeySequence("Ctrl+O"), self),
        }

    ## words tab

    def _createInputField(self):
        self.inputField = QTextEdit()
        self.inputField.setPlaceholderText("Write your words (one per line)")
        return self.inputField

    def _createLogWidget(self):
        logWidget = self.QTextEditLogger()
        logWidget.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger().addHandler(logWidget)
        logging.getLogger().setLevel(logging.INFO)
        return logWidget.widget

    def _createButtonsLayout(self):
        buttonsLayout = QHBoxLayout()
        buttonsLayout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.buttons = {
            "Submit": QPushButton("Submit"),
            "Upload": QPushButton("Upload"),
            "Clear": QPushButton("Clear"),
        }
        for button in self.buttons.values():
            buttonsLayout.addWidget(button)

        return buttonsLayout

    ## settings tab

    def _createSettingsFormLayout(self):
        formLayout = QFormLayout()

        self.config = {
            "modelName": QLineEdit(modelName),
            "deckName": QLineEdit(deckName),
            "cacheEnabled": QCheckBox(),
            "cachePath": QLineEdit(cachePath),
        }
        formLayout.addRow("Name of anki model:", self.config["modelName"])
        formLayout.addRow("Name of anki deck:", self.config["deckName"])
        formLayout.addRow("Cache enabled:", self.config["cacheEnabled"])
        formLayout.addRow("Cache path:", self.config["cachePath"])
        self.config["cacheEnabled"].setChecked(cacheEnabled)

        return formLayout

    def _createSettingsDictionariesLayout(self):
        dictionariesLayout = QVBoxLayout()
        gridLayout = QGridLayout()
        label = QLabel("Dictionaries:")

        dictionariesLayout.addWidget(label)
        dictionariesLayout.addLayout(gridLayout)

        self.dictionaries = {
            "Oxford": QCheckBox("Oxford"),
            "Cambridge": QCheckBox("Cambridge"),
            "Macmillan": QCheckBox("Macmillan"),
            "Urban Dictionary": QCheckBox("Urban Dictionary"),
            "Cambridge (ru)": QCheckBox("Cambridge (ru)"),
        }
        row, column = 0, 0
        for widget in self.dictionaries.values():  # add 2 widgets per line
            if column >= 2:
                column = 0
                row += 1
            gridLayout.addWidget(widget, row, column)
            column += 1

        # set defaults
        for dic, value in DICTIONARIES.items():
            self.dictionaries[dic].setChecked(value)

        # set from config
        if configExists():
            with open(CONFIG_PATH, "r") as file:
                config = yaml.safe_load(file)
                if "dictionaries" in config:
                    for dic, value in config["dictionaries"].items():
                        self.dictionaries[dic].setChecked(value)

        return dictionariesLayout

    def _createSettingsButtonsLayout(self):
        settingsButtonsLayout = QHBoxLayout()
        settingsButtonsLayout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.settingsButtons = {
            "Save": QPushButton("Save"),
            "Set defaults": QPushButton("Set defaults"),
        }
        for button in self.settingsButtons.values():
            settingsButtonsLayout.addWidget(button)

        return settingsButtonsLayout

    ## advanced tab

    def _createAdvancedButtonsLayout(self):
        advancedButtonsLayout = QHBoxLayout()
        advancedButtonsLayout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        self.advancedButtons = {
            "Clear data": QPushButton("Clear data"),
        }
        for button in self.advancedButtons.values():
            advancedButtonsLayout.addWidget(button)

        return advancedButtonsLayout

    def _runWarningDialog(self):
        warning = LazyDialog.WarningDialog()
        confirmation = warning.exec()

        return confirmation == QMessageBox.StandardButton.Ok

    ## methods

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
        self.inputField.setTextCursor(cursor)  # set cursor at the end

    class QTextEditLogger(logging.Handler):
        """Logging widget"""

        def __init__(self):
            super().__init__()
            self.widget = QLabel()

        def emit(self, record):
            msg = self.format(record)
            self.widget.setText(msg)

    class WarningDialog(QMessageBox):
        def __init__(self):
            super().__init__()
            self.setIcon(QMessageBox.Icon.Warning)
            self.setText("Are you sure you want to clear all data?")
            self.setInformativeText(
                "This will delete all decks and models created by this application, as well as the settings you have set."
            )
            self.setWindowTitle("Warning")
            self.setStandardButtons(
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
            )


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
        self._model = LazyModel()

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

        self._view.settingsButtons["Save"].clicked.connect(self.saveConfig)
        self._view.settingsButtons["Save"].clicked.connect(
            lambda checked: self._view.settingsLabel.setText("Please restart the app")
        )
        self._view.settingsButtons["Set defaults"].clicked.connect(self.setDefaults)
        self._view.settingsButtons["Set defaults"].clicked.connect(
            lambda checked: self._view.settingsLabel.setText("Please restart the app")
        )

        self._view.advancedButtons["Clear data"].clicked.connect(
            lambda checked: self.clearData()
        )

        self._view.shortcuts["Ctrl+Return"].activated.connect(self.createNotes)
        self._view.shortcuts["Ctrl+O"].activated.connect(self.uploadFile)

        self.worker.started.connect(
            lambda: self._view.buttons["Submit"].setDisabled(True)
        )
        self.worker.finished.connect(
            lambda: self._view.buttons["Submit"].setDisabled(False)
        )

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

    def saveConfig(self):
        prevData = self._model.config

        with open(CONFIG_PATH, "w") as file:
            constants = [MODEL_NAME, DECK_NAME, CACHE_ENABLED, CACHE_PATH]
            for const, (key, field) in zip(constants, self._view.config.items()):
                value = field.text() if key != "cacheEnabled" else field.isChecked()
                if const != value:
                    yaml.safe_dump({key: value}, file)

            dictionaries = {}
            for const, (key, checkbox) in zip(
                DICTIONARIES.values(), self._view.dictionaries.items()
            ):
                value = checkbox.isChecked()
                if const != value:
                    dictionaries[key] = value
            if dictionaries:
                yaml.safe_dump({"dictionaries": dictionaries}, file)

        with open(CONFIG_PATH, "r") as file:
            currData = yaml.safe_load(file)
        with open(CREATED_PATH, "r+") as file:
            data = json.load(file)
        with open(CREATED_PATH, "w") as file:
            if prevData != currData:
                data["Config changed"] = True
            else:
                data["Config changed"] = False
            json.dump(data, file, indent=2)

    def setDefaults(self):
        Path(CONFIG_PATH).unlink(missing_ok=True)  # delete config
        self._view.config["modelName"].setText(MODEL_NAME)
        self._view.config["deckName"].setText(DECK_NAME)
        self._view.config["cacheEnabled"].setChecked(CACHE_ENABLED)
        self._view.config["cachePath"].setText(CACHE_PATH)
        for key, value in DICTIONARIES.items():
            self._view.dictionaries[key].setChecked(value)

    def clearData(self):
        confirmed = self._view._runWarningDialog()
        if confirmed:
            with open(CREATED_PATH, "r") as file:
                data = json.load(file)
                app.invoke("deleteDecks", decks=data["Created decks"], cardsToo=True)
            Path(CONFIG_PATH).unlink(missing_ok=True)
            shutil.rmtree(".cache")


class LazyModel:
    """Model class"""

    def __init__(self):
        with open(CONFIG_PATH, "r") as file:
            self.config = yaml.safe_load(file)

    @staticmethod
    def _initialize():
        logging.info("Initialization...")
        app.open_anki()
        dic = {}
        if configExists():
            with open(CONFIG_PATH, "r") as file:
                config = yaml.safe_load(file)
                dic = config.get("dictionaries", {})
        with open(CREATED_PATH, "r+") as file:
            configChanged = json.load(file)["Config changed"]
        if configChanged:
            if modelName not in app.invoke("modelNames"):
                app.invoke(
                    "createModel", **app.get_model(model_name=modelName, links=dic)
                )
            if deckName not in app.invoke("deckNames"):
                app.invoke("createDeck", deck=deckName)
            LazyModel.logCreatedJson(modelName, deckName)
        logging.info("Ready to use")

    @staticmethod
    def _createNotes(words):
        logging.info("Creating cards...")
        cache = app.load_cache() if cacheEnabled else {}
        app.invoke(
            "addNotes",
            notes=app.get_notes(
                words, cache=cache, model_name=modelName, deck_name=deckName
            ),
        )
        if cacheEnabled:
            with open(cachePath, "w", encoding="utf-8") as file:
                json.dump(cache, file, indent=2)
        logging.info("Сards created")

    @staticmethod
    def logCreatedJson(modelName, deckName):
        Path(CREATED_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(CREATED_PATH).touch(exist_ok=True)
        if Path(CREATED_PATH).stat().st_size == 0:
            with open(CREATED_PATH, "w") as file:
                currentData = {
                    "Created models": [modelName],
                    "Created decks": [deckName],
                }
                json.dump(currentData, file, indent=2)
        else:
            with open(CREATED_PATH, "r+") as file:
                data = json.load(file)
                file.seek(0)
                if modelName not in data["Created models"]:
                    data["Created models"].append(modelName)
                if deckName not in data["Created decks"]:
                    data["Created decks"].append(deckName)
                json.dump(data, file, indent=2)


def loadConfig():
    if Path(CONFIG_PATH).is_file():
        with open(CONFIG_PATH, "r") as file:
            config = yaml.safe_load(file)
            if config:
                globals().update(config)


def configExists():
    config = Path(CONFIG_PATH)
    return config.is_file() and config.stat().st_size != 0


def main():
    loadConfig()
    app = QApplication([])
    dialog = LazyDialog()
    controller = LazyController(view=dialog, model=LazyModel)

    dialog.show()
    app.exec()


if __name__ == "__main__":
    main()
