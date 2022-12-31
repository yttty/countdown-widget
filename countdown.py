import sys
import os
import json
import time
import platform
import webbrowser
from datetime import date
from math import floor
from typing import List
from random import randint

from utils.sort import multikeysort
from utils.io import mkdirp

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


######## DATA MODEL LAYER ########
class PathFinder:
    """
    Only work in windows
    """

    @staticmethod
    def userDataPath(relative_path):
        base_path = os.path.join(os.getenv('LOCALAPPDATA'), "Countdown-data")
        mkdirp(base_path)
        mkdirp(os.path.join(base_path, 'local'))
        return os.path.join(base_path, relative_path)

    @staticmethod
    def resourcePath(relative_path):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)


class DatesManager:

    def __init__(self,
                 bgcolors,
                 autoHiddenDays,
                 path=PathFinder.resourcePath(
                     os.path.join("local", "dates.json"))):
        self.path = path
        self.autoHiddenDays = autoHiddenDays
        self.bgcolors = bgcolors
        self.load()

    def __del__(self):
        # TODO: write back to file
        return

    def getDaysList(self) -> List:

        def getDaysLeft(d):
            """
            return How many days remain before the future date.
            """
            year, month, day = d["year"], d["month"], d["day"]
            future = date(year, month, day)
            now = date.today()
            delta = future - now
            return delta.days

        def getLabelText(d) -> str:
            name = d['name']
            daysLeft = getDaysLeft(d)
            weeksLeft, daysLeft = floor(daysLeft / 7), daysLeft % 7
            if weeksLeft == 0:
                return f"<b>{name}</b>: {daysLeft} {'days' if daysLeft > 1 else 'day'}"
            else:
                return f"<b>{name}</b>: {weeksLeft}w{str(daysLeft)+'d' if daysLeft > 0 else ''}"

        def filterDays(d):
            if d['hidden'] == True:
                return False
            daysLeft = getDaysLeft(d)
            if daysLeft < 0:
                return False
            if d['hidden'] == "auto" and daysLeft > self.autoHiddenDays:
                return False
            return True

        def formatDates(d):
            return {
                'text': getLabelText(d),
                'color': d['bgcolor'],
                'tip': f"{d['year']}/{d['month']}/{d['day']}"
            }

        days = map(formatDates, filter(filterDays, self.data))
        # days = multikeysort(days, ["year", "month", "day"])
        return list(days)

    def load(self):
        try:
            with open(self.path, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            with open(
                    PathFinder.resourcePath(os.path.join(
                        "local", "dates.json"))) as default_dates:
                self.data = json.load(default_dates)
                self.save()
        finally:
            for d in self.data:
                if "bgcolor" not in d.keys() or d["bgcolor"].lower(
                ) == 'random':
                    d['bgcolor'] = self.bgcolors[randint(
                        0,
                        len(self.bgcolors) - 1)]

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.data, f)


class ConfigManager:

    def __init__(self,
                 path=PathFinder.userDataPath(
                     os.path.join("local", "config.json"))):
        self.path = path
        self.load()

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        raise NotImplementedError("Do not allow editing config")

    def load(self):
        try:
            with open(self.path, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            with open(
                    PathFinder.resourcePath(
                        os.path.join("local",
                                     "config.json"))) as default_config:
                self.data = json.load(default_config)
                self.save()

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.data, f)


######## VIEW LAYER ########
class SmartQLabel(QLabel):

    def leaveEvent(self, e):  # 鼠标离开label
        """mouse leave label"""
        pass

    def enterEvent(self, e):  # 鼠标进入label
        """mouse enter label"""
        pass


class DatesWatcher(QFileSystemWatcher):

    def __init__(self, parent=None):
        super(DatesWatcher, self).__init__(parent)
        self.addPath(self.parent().dates.path)
        self.fileChanged.connect(self.parent().reloadLabels)


class TrayIcon(QSystemTrayIcon):

    def __init__(self, parent=None):
        super(TrayIcon, self).__init__(parent)
        self.initMenu()
        self.initIcon()
        self.setToolTip("Conference Countdown.\nDouble click to show/hide.")
        self.show()

    def initIcon(self):
        self.icon = QIcon(
            PathFinder.resourcePath(os.path.join("res", "icon.svg")))
        self.setIcon(self.icon)
        self.activated.connect(self.iconClicked)

    def initMenu(self):
        """Tray Icon Menus"""
        self.setVisibilityAction = QAction("Show/Hide",
                                           self,
                                           triggered=self.parent().showhide)
        self.alterAction = QAction("Alter Opacity",
                                   self,
                                   triggered=self.parent().alterOpacity)
        self.tempHideAction = QAction("Hide Temporarily",
                                      self,
                                      triggered=self.parent().hideTemporarily)
        self.editDatesAction = QAction("Edit Dates",
                                       self,
                                       triggered=self.openDates)
        self.settingsAction = QAction("Settings",
                                      self,
                                      triggered=self.openSettings)
        self.aboutAction = QAction("About",
                                   self,
                                   triggered=self.openHomepage)
        self.quitAction = QAction("Quit", self, triggered=self.quit)

        self.menu = QMenu()
        self.menu.addAction(self.setVisibilityAction)
        self.menu.addAction(self.alterAction)
        self.menu.addAction(self.tempHideAction)
        self.menu.addAction(self.editDatesAction)
        self.menu.addAction(self.settingsAction)
        self.menu.addAction(self.aboutAction)
        self.menu.addAction(self.quitAction)

        self.setContextMenu(self.menu)

    def openDates(self):
        self.openFile(self.parent().dates.path)

    def openSettings(self):
        self.openFile(self.parent().config.path)

    def openHomepage(self):
        webbrowser.open("https://github.com/yttty/countdown-widget")

    def openFile(self, path):
        if platform.system() == "Windows":
            # windows specific
            os.startfile(path)
        else:
            pass

    def iconClicked(self, reason):
        if reason == 2:  # left double click or left click
            self.parent().showhide()

    def quit(self):
        """Safe exit"""
        self.setVisible(False)
        self.parent().close()
        sys.exit()


class CountDownWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.dates = DatesManager(self.config['display.bgcolors'],
                                  self.config['days.autoHiddenDays'])
        self.labels = []
        self.initTimer()
        self.refreshLabels()

        self.ti = TrayIcon(self)
        self.watcher = DatesWatcher(self)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                            | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.opacityLevel = self.config['display.opacity.defaultLevel']
        self.setWindowOpacity(
            self.config['display.opacity.levels'][self.opacityLevel])
        self.show()

    def initTimer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refreshLabels)
        self.timer.start(self.config['display.updateInterval'] * 1000)

    def refreshLabels(self):
        for label in self.labels:
            label.deleteLater()
        self.labels = []
        self.days = self.dates.getDaysList()
        if len(self.days) == 0:
            return
        else:
            windowWidth = 0
            windowHeight = 0
            for d in self.days:
                label = SmartQLabel(d['text'], self)
                label.setStyleSheet(f"background-color: {d['color']}")
                label.setToolTip(d['tip'])
                label.setFont(
                    QFont(self.config['display.font.family'],
                          self.config['display.font.size']))
                label.adjustSize()
                label.setToolTipDuration(1500)
                self.labels.append(label)
                # adjust window size
                labelG = label.geometry()
                windowWidth = max(windowWidth, labelG.width())
                windowHeight += labelG.height()
            self.setFixedSize(windowWidth, windowHeight)
            # resize labels and move labels
            currentPosition = 0
            for label in self.labels:
                height = label.geometry().height()
                label.setGeometry(0, currentPosition, windowWidth, height)
                currentPosition += height
                label.show()

            # ag excludes the space for task bar but sg includes it
            ag = QDesktopWidget().availableGeometry()
            # sg = QDesktopWidget().screenGeometry()
            widget = self.geometry()
            x = ag.width() - widget.width()
            y = ag.height() - widget.height()
            self.move(x, y)

    def reloadLabels(self):
        self.dates.load()
        self.refreshLabels()

    def alterOpacity(self):
        self.opacityLevel = (self.opacityLevel + 1) % len(
            self.config['display.opacity.levels'])
        level = self.config['display.opacity.levels'][self.opacityLevel]
        self.setWindowOpacity(level)

    def hideTemporarily(self):
        self.hide()
        time.sleep(self.config["display.tmpHideInterval"])
        self.show()

    def showhide(self):
        if self.isHidden():
            self.show()
        else:
            self.hide()
            self.refreshLabels()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.alterOpacity()
        elif event.button() == Qt.RightButton:
            self.hideTemporarily()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pass
        elif event.button() == Qt.RightButton:
            pass


if __name__ == '__main__':
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    if platform.system() == "Windows":
        app = QApplication(sys.argv)
        widget = CountDownWidget()
        sys.exit(app.exec_())
    else:
        raise NotImplementedError("Unsuppotred OS!")
