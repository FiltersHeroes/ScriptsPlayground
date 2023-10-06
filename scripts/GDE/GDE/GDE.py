#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=consider-using-f-string
"""MIT License

Copyright (c) 2023 Filters Heroes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
import os
import sys
import importlib
import configparser
from PySide2.QtWidgets import (QApplication, QDialog,
                               QMainWindow, QMessageBox, QToolTip)
from PySide2.QtGui import QIcon, QCursor
from platformdirs import user_config_dir
import requests
import tldextract
from bs4 import BeautifulSoup

APP_NAME = "GroupsDomainsExtractor"
APP_VERSION = "1.3.0"

script_path = os.path.dirname(os.path.realpath(__file__))
cfilepath = os.path.join(user_config_dir(), APP_NAME, 'groups.ini')
pj = os.path.join


def import_from_file(file_path):
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Import submodules
ingredients_dir = pj(script_path, "ingredients")
i18n = import_from_file(pj(ingredients_dir, "i18n.py"))
GDE_ui = import_from_file(pj(ingredients_dir, "GDE_ui.py"))
Ui_MainWindow = GDE_ui.Ui_MainWindow
about_ui = import_from_file(pj(ingredients_dir, "about_ui.py"))
Ui_AboutDialog = about_ui.Ui_AboutDialog
group_selection_ui = import_from_file(
    pj(ingredients_dir, "group_selection_ui.py"))
Ui_GroupSelectionDialog = group_selection_ui.Ui_GroupSelectionDialog


def version():
    return APP_VERSION


def read_config():
    config = configparser.ConfigParser()
    config.read(cfilepath)
    return config


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.connect_signals_slots()

    def connect_signals_slots(self):
        self.actionAbout.triggered.connect(self.about)
        self.extractDomainsPB.clicked.connect(self.extract_domains)
        self.actionRemove_group.triggered.connect(self.remove_group_menu)
        self.actionLoad_group.triggered.connect(self.load_group_menu)
        self.actionSave_group.triggered.connect(self.save_group)
        self.actionExit.triggered.connect(self.close)

    def about(self):
        dialog = AboutDialog()
        dialog.exec()

    def extract_domains(self):
        # specify the url
        quote_page = self.UrlLE.text()

        css_path = self.CssLE.text()

        if not quote_page or not css_path:
            QMessageBox.critical(self, translateGDE("Error"), translateGDE(
                "Tell me what to extract, cuz unfortunately my glass ball broke."))
            return

        # query the website and return the html to the variable ‘page’
        page = requests.get(quote_page, timeout=100).text

        # parse the html using Beautiful Soup and store in variable `soup`
        soup = BeautifulSoup(page, "html.parser")

        data = soup.select(css_path)

        final_links = []

        for tag in data:
            tag['href'] = tldextract.extract(tag['href']).registered_domain
            final_links.append(tag['href'])

        final_links = sorted(set(final_links))

        separator_combo_value = self.SepCB.currentText()
        if separator_combo_value == translateGDE('comma'):
            separator = ","
        elif separator_combo_value == translateGDE('pipe'):
            separator = "|"

        msg_box = QMessageBox()
        if final_links:
            final_links_with_sep = separator.join(final_links)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle(translateGDE("Done"))
            msg_box.setText(translateGDE(
                'Domains have been found \U0001F600.'))
            msg_box.setDetailedText(final_links_with_sep)
            copy_btn = msg_box.addButton(translateGDE(
                "Copy to clipboard"), QMessageBox.ActionRole)
            copy_btn.clicked.disconnect()
            copy_btn.clicked.connect(
                lambda: clipboard.setText(final_links_with_sep))
            copy_btn.setIcon(QIcon.fromTheme("edit-copy"))
            msg_box.setStandardButtons(QMessageBox.Close)
            msg_box.exec_()
        else:
            QMessageBox.critical(self, translateGDE("Error"), translateGDE(
                "Domains not found. Check the entered data and try again!"))

    def load_group_list(self):
        config = read_config()
        sections = []
        for each_section in config.sections():
            sections.append(each_section)
        if not sections:
            sections = [""]
        return sections

    def remove_group_menu(self):
        dialog = GroupSelectionDialog()
        dialog.loadPB.hide()
        dialog.groupCB.addItems([*self.load_group_list()])
        dialog.exec()

    def load_group_menu(self):
        dialog = GroupSelectionDialog()
        dialog.removePB.hide()
        dialog.groupCB.addItems([*self.load_group_list()])
        dialog.exec()

    def save_group(self):
        if not os.path.exists(os.path.join(user_config_dir(), APP_NAME)):
            os.mkdir(os.path.join(user_config_dir(), APP_NAME))
        config = read_config()
        group_name = self.GroupNameLE.text()
        if not group_name:
            QMessageBox.critical(self, translateGDE("Error"), translateGDE(
                "Not so fast, cowboy, enter group's name!"))
        else:
            if config.has_section(group_name):
                config.remove_section(group_name)
            separator_combo_value = self.SepCB.currentText()
            if separator_combo_value == translateGDE('comma'):
                separator = "comma"
            elif separator_combo_value == translateGDE('pipe'):
                separator = "pipe"
            config[group_name] = {'url': self.UrlLE.text(
            ), 'css': self.CssLE.text(), 'separator': separator}
            with open(cfilepath, 'w', encoding="utf-8") as configfile:
                config.write(configfile)
            QMessageBox.information(self, translateGDE("Done"), translateGDE(
                '{group_name} group has been saved to file: "{file_path}".').format(group_name=group_name, file_path=cfilepath))


class AboutDialog(QDialog, Ui_AboutDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.versionLbl.setText(APP_VERSION)
        self.connect_signals_slots()

    def connect_signals_slots(self):
        self.dependsLbl.linkHovered.connect(self.url_hover)

    def url_hover(self, url):
        if url:
            QToolTip.showText(QCursor.pos(), url.replace("https://", ""))
        else:
            QToolTip.hideText()


class GroupSelectionDialog(QDialog, Ui_GroupSelectionDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.connect_signals_slots()

    def connect_signals_slots(self):
        self.loadPB.clicked.connect(self.load_group)
        self.cancelPB.clicked.connect(self.close)
        self.removePB.clicked.connect(self.remove_group)

    def load_group(self):
        config = read_config()
        selected_group = self.groupCB.currentText()
        if not selected_group:
            QMessageBox.critical(self, translateGDE("Error"), translateGDE(
                "Tell me what to load, cuz unfortunately my glass ball broke."))
        else:
            main_window.UrlLE.setText(config[selected_group]['url'])
            main_window.CssLE.setText(config[selected_group]['css'])
            main_window.SepCB.setCurrentText(
                translateGDE(config[selected_group]['separator']))
            main_window.GroupNameLE.setText(selected_group)
            self.close()

    def remove_group(self):
        config = read_config()
        selected_group = self.groupCB.currentText()
        if config.has_section(selected_group):
            reply = QMessageBox.question(self, translateGDE('Confirmation'), translateGDE(
                "Are you sure you want to remove configuration of {selected_group} group?").format(selected_group=selected_group), QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                config.remove_section(selected_group)
                with open(cfilepath, 'w', encoding="utf-8") as configfile:
                    config.write(configfile)
                self.groupCB.removeItem(self.groupCB.currentIndex())
                QMessageBox.information(self, translateGDE("Done"), translateGDE(
                    '{selected_group} group has been deleted.').format(selected_group=selected_group))

def main():
    if sys.platform == "win32":
        import qdarktheme
        qdarktheme.enable_hi_dpi()
    i18n.install()
    if sys.platform == "win32":
        theme = qdarktheme._style_loader._detect_system_theme('light')
        if theme == "dark":
            os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"
    app = QApplication(sys.argv)
    if sys.platform == "win32":
        if theme == "dark":
            qdarktheme.setup_theme("dark", additional_qss="QToolTip { border: 0px; }")
            app.setStyle("Fusion")
    app.setApplicationDisplayName(translateGDE('Groups Domains Extractor'))
    clipboard = app.clipboard()
    main_window = MainWindow()
    main_window.show()
    app.exec_()

if __name__ == '__main__':
    main()
