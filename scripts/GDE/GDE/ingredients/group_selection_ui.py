# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'group_selection.ui'
##
## Created by: Qt User Interface Compiler version 5.15.10
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore


class Ui_GroupSelectionDialog(object):
    def setupUi(self, GroupSelectionDialog):
        if not GroupSelectionDialog.objectName():
            GroupSelectionDialog.setObjectName(u"GroupSelectionDialog")
        GroupSelectionDialog.resize(444, 116)
        self.gridLayout_2 = QGridLayout(GroupSelectionDialog)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label = QLabel(GroupSelectionDialog)
        self.label.setObjectName(u"label")

        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)

        self.groupCB = QComboBox(GroupSelectionDialog)
        self.groupCB.setObjectName(u"groupCB")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupCB.sizePolicy().hasHeightForWidth())
        self.groupCB.setSizePolicy(sizePolicy)

        self.gridLayout_2.addWidget(self.groupCB, 0, 1, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.loadPB = QPushButton(GroupSelectionDialog)
        self.loadPB.setObjectName(u"loadPB")
        self.loadPB.setEnabled(True)
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.loadPB.sizePolicy().hasHeightForWidth())
        self.loadPB.setSizePolicy(sizePolicy1)
        icon = QIcon()
        iconThemeName = u"document-open"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.loadPB.setIcon(icon)

        self.horizontalLayout.addWidget(self.loadPB)

        self.removePB = QPushButton(GroupSelectionDialog)
        self.removePB.setObjectName(u"removePB")
        sizePolicy1.setHeightForWidth(self.removePB.sizePolicy().hasHeightForWidth())
        self.removePB.setSizePolicy(sizePolicy1)
        icon1 = QIcon()
        iconThemeName = u"edit-delete"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.removePB.setIcon(icon1)

        self.horizontalLayout.addWidget(self.removePB)

        self.cancelPB = QPushButton(GroupSelectionDialog)
        self.cancelPB.setObjectName(u"cancelPB")
        icon2 = QIcon()
        iconThemeName = u"window-close"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.cancelPB.setIcon(icon2)

        self.horizontalLayout.addWidget(self.cancelPB)


        self.gridLayout_2.addLayout(self.horizontalLayout, 1, 1, 1, 1)


        self.retranslateUi(GroupSelectionDialog)

        QMetaObject.connectSlotsByName(GroupSelectionDialog)
    # setupUi

    def retranslateUi(self, GroupSelectionDialog):
        GroupSelectionDialog.setWindowTitle(translateGDE(u"Group selection"))
        self.label.setText(translateGDE(u"Group\u2019s configuration:"))
        self.loadPB.setText(translateGDE(u"Load"))
        self.removePB.setText(translateGDE(u"Remove"))
        self.cancelPB.setText(translateGDE(u"Cancel"))
    # retranslateUi

