# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *


class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        if not AboutDialog.objectName():
            AboutDialog.setObjectName(u"AboutDialog")
        AboutDialog.resize(397, 327)
        self.gridLayout = QGridLayout(AboutDialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tabWidget = QTabWidget(AboutDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setAutoFillBackground(True)
        self.tabWidget.setStyleSheet(u"")
        self.aboutTab = QWidget()
        self.aboutTab.setObjectName(u"aboutTab")
        self.gridLayout_3 = QGridLayout(self.aboutTab)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.plainTextEdit = QPlainTextEdit(self.aboutTab)
        self.plainTextEdit.setObjectName(u"plainTextEdit")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plainTextEdit.sizePolicy().hasHeightForWidth())
        self.plainTextEdit.setSizePolicy(sizePolicy)
        self.plainTextEdit.setStyleSheet(u"QPlainTextEdit {background-color: transparent;}")
        self.plainTextEdit.setFrameShape(QFrame.NoFrame)
        self.plainTextEdit.setFrameShadow(QFrame.Sunken)
        self.plainTextEdit.setReadOnly(True)
        self.plainTextEdit.setBackgroundVisible(False)

        self.gridLayout_3.addWidget(self.plainTextEdit, 1, 0, 1, 1)

        self.tabWidget.addTab(self.aboutTab, "")
        self.licenseTab = QWidget()
        self.licenseTab.setObjectName(u"licenseTab")
        self.gridLayout_2 = QGridLayout(self.licenseTab)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.plainTextEdit_2 = QPlainTextEdit(self.licenseTab)
        self.plainTextEdit_2.setObjectName(u"plainTextEdit_2")
        sizePolicy.setHeightForWidth(self.plainTextEdit_2.sizePolicy().hasHeightForWidth())
        self.plainTextEdit_2.setSizePolicy(sizePolicy)
        self.plainTextEdit_2.setAutoFillBackground(False)
        self.plainTextEdit_2.setStyleSheet(u"QPlainTextEdit {background-color: transparent;}")
        self.plainTextEdit_2.setFrameShape(QFrame.NoFrame)
        self.plainTextEdit_2.setReadOnly(True)
        self.plainTextEdit_2.setPlainText(u"Copyright (c) 2023 Filters Heroes\n"
"\n"
"This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or\n"
"(at your option) any later version.\n"
"\n"
"This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.\n"
"\n"
"You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.")

        self.gridLayout_2.addWidget(self.plainTextEdit_2, 0, 0, 1, 1)

        self.tabWidget.addTab(self.licenseTab, "")
        self.creditsTab = QWidget()
        self.creditsTab.setObjectName(u"creditsTab")
        self.gridLayout_4 = QGridLayout(self.creditsTab)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.dependsLbl = QLabel(self.creditsTab)
        self.dependsLbl.setObjectName(u"dependsLbl")
        sizePolicy.setHeightForWidth(self.dependsLbl.sizePolicy().hasHeightForWidth())
        self.dependsLbl.setSizePolicy(sizePolicy)
        self.dependsLbl.setLineWidth(0)
        self.dependsLbl.setText(u"* [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/)\n"
"* [tldextract](https://github.com/john-kurkowski/tldextract)\n"
"* [platformdirs](https://github.com/platformdirs/platformdirs)\n"
"* [QtPy](https://github.com/spyder-ide/qtpy)\n"
"* [API](API_URL)\n"
"* [Qt](https://www.qt.io)")
        self.dependsLbl.setTextFormat(Qt.MarkdownText)
        self.dependsLbl.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.dependsLbl.setWordWrap(True)
        self.dependsLbl.setIndent(0)
        self.dependsLbl.setOpenExternalLinks(True)
        self.dependsLbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout_4.addWidget(self.dependsLbl, 0, 0, 1, 1)

        self.tabWidget.addTab(self.creditsTab, "")

        self.gridLayout.addWidget(self.tabWidget, 2, 0, 1, 1)

        self.versionLbl = QLabel(AboutDialog)
        self.versionLbl.setObjectName(u"versionLbl")
        self.versionLbl.setEnabled(False)
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.versionLbl.sizePolicy().hasHeightForWidth())
        self.versionLbl.setSizePolicy(sizePolicy1)
        font = QFont()
        font.setPointSize(14)
        font.setBold(False)
        self.versionLbl.setFont(font)
        self.versionLbl.setText(u"version")

        self.gridLayout.addWidget(self.versionLbl, 1, 0, 1, 1)

        self.line = QFrame(AboutDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line, 3, 0, 1, 1)

        self.buttonBox = QDialogButtonBox(AboutDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)
        self.buttonBox.setCenterButtons(False)

        self.gridLayout.addWidget(self.buttonBox, 4, 0, 1, 1)

        self.appnameLbl = QLabel(AboutDialog)
        self.appnameLbl.setObjectName(u"appnameLbl")
        font1 = QFont()
        font1.setPointSize(20)
        font1.setBold(True)
        font1.setItalic(True)
        self.appnameLbl.setFont(font1)

        self.gridLayout.addWidget(self.appnameLbl, 0, 0, 1, 1)


        self.retranslateUi(AboutDialog)
        self.buttonBox.rejected.connect(AboutDialog.close)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AboutDialog)
    # setupUi

    def retranslateUi(self, AboutDialog):
        AboutDialog.setWindowTitle(translateGDE(u"About GDE"))
        self.plainTextEdit.setPlainText(translateGDE(u"Groups Domains Extractor helps in finding all domains of specific group and copies it to clipboard.\n"
"It also has the ability to save configuration of group to file and load it."))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.aboutTab), translateGDE(u"About"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.licenseTab), translateGDE(u"License"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.creditsTab), translateGDE(u"Dependencies"))
        self.appnameLbl.setText(translateGDE(u"Groups Domains Extractor"))
    # retranslateUi

