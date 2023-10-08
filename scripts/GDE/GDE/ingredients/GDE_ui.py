# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'GDE.ui'
##
## Created by: Qt User Interface Compiler version 5.15.10
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from qtpy.QtCore import *  # type: ignore
from qtpy.QtGui import *  # type: ignore
from qtpy.QtWidgets import *  # type: ignore


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(398, 189)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        icon = QIcon(QIcon.fromTheme(u"help-about"))
        self.actionAbout.setIcon(icon)
        self.actionLoad_group = QAction(MainWindow)
        self.actionLoad_group.setObjectName(u"actionLoad_group")
        icon1 = QIcon(QIcon.fromTheme(u"document-open"))
        self.actionLoad_group.setIcon(icon1)
        self.actionSave_group = QAction(MainWindow)
        self.actionSave_group.setObjectName(u"actionSave_group")
        icon2 = QIcon(QIcon.fromTheme(u"document-save"))
        self.actionSave_group.setIcon(icon2)
        self.actionRemove_group = QAction(MainWindow)
        self.actionRemove_group.setObjectName(u"actionRemove_group")
        icon3 = QIcon(QIcon.fromTheme(u"edit-delete"))
        self.actionRemove_group.setIcon(icon3)
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        icon4 = QIcon(QIcon.fromTheme(u"exit"))
        self.actionExit.setIcon(icon4)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.formLayout = QFormLayout(self.centralwidget)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.formLayout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setRowWrapPolicy(QFormLayout.DontWrapRows)
        self.formLayout.setLabelAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.UrlLE = QLineEdit(self.centralwidget)
        self.UrlLE.setObjectName(u"UrlLE")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.UrlLE.sizePolicy().hasHeightForWidth())
        self.UrlLE.setSizePolicy(sizePolicy1)
        self.UrlLE.setPlaceholderText(u"https://siecportali.pl/realizacje")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.UrlLE)

        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.CssLE = QLineEdit(self.centralwidget)
        self.CssLE.setObjectName(u"CssLE")
        sizePolicy1.setHeightForWidth(self.CssLE.sizePolicy().hasHeightForWidth())
        self.CssLE.setSizePolicy(sizePolicy1)
        self.CssLE.setPlaceholderText(u".portal-logos a")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.CssLE)

        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.label_3)

        self.SepCB = QComboBox(self.centralwidget)
        self.SepCB.addItem("")
        self.SepCB.addItem("")
        self.SepCB.setObjectName(u"SepCB")
        sizePolicy1.setHeightForWidth(self.SepCB.sizePolicy().hasHeightForWidth())
        self.SepCB.setSizePolicy(sizePolicy1)
        self.SepCB.setEditable(False)

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.SepCB)

        self.extractDomainsPB = QPushButton(self.centralwidget)
        self.extractDomainsPB.setObjectName(u"extractDomainsPB")
        sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.extractDomainsPB.sizePolicy().hasHeightForWidth())
        self.extractDomainsPB.setSizePolicy(sizePolicy2)
        self.extractDomainsPB.setLayoutDirection(Qt.LeftToRight)

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.extractDomainsPB)

        self.GroupNameLE = QLineEdit(self.centralwidget)
        self.GroupNameLE.setObjectName(u"GroupNameLE")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.GroupNameLE)

        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.label_4)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 398, 22))
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuHelp.addAction(self.actionAbout)
        self.menuFile.addAction(self.actionRemove_group)
        self.menuFile.addAction(self.actionLoad_group)
        self.menuFile.addAction(self.actionSave_group)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

        self.retranslateUi(MainWindow)

        self.SepCB.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(translateGDE(u"Groups Domains Extractor"))
        self.actionAbout.setText(translateGDE(u"&About GDE"))
        self.actionLoad_group.setText(translateGDE(u"&Load group"))
#if QT_CONFIG(shortcut)
        self.actionLoad_group.setShortcut(translateGDE(u"Ctrl+O"))
#endif // QT_CONFIG(shortcut)
        self.actionSave_group.setText(translateGDE(u"&Save group"))
#if QT_CONFIG(shortcut)
        self.actionSave_group.setShortcut(translateGDE(u"Ctrl+S"))
#endif // QT_CONFIG(shortcut)
        self.actionRemove_group.setText(translateGDE(u"&Remove group"))
#if QT_CONFIG(shortcut)
        self.actionRemove_group.setShortcut(translateGDE(u"Ctrl+R"))
#endif // QT_CONFIG(shortcut)
        self.actionExit.setText(translateGDE(u"&Exit"))
#if QT_CONFIG(shortcut)
        self.actionExit.setShortcut(translateGDE(u"Ctrl+Q"))
#endif // QT_CONFIG(shortcut)
        self.label.setText(translateGDE(u"Site address:"))
        self.label_2.setText(translateGDE(u"CSS path:"))
        self.label_3.setText(translateGDE(u"Separator:"))
        self.SepCB.setItemText(0, translateGDE(u"comma"))
        self.SepCB.setItemText(1, translateGDE(u"pipe"))

        self.SepCB.setCurrentText(translateGDE(u"comma"))
        self.extractDomainsPB.setText(translateGDE(u"Extract domains"))
        self.label_4.setText(translateGDE(u"Group\u2019s name:"))
        self.menuHelp.setTitle(translateGDE(u"&Help"))
        self.menuFile.setTitle(translateGDE(u"&File"))
    # retranslateUi

