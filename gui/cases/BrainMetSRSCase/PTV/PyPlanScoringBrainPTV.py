# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Plan_Competition_Project\gui\PyPlanScoringLungSBRT.ui'
#
# Created: Wed Mar  7 17:49:33 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

# from PySide import QtCore, QtGui
from PySide import QtCore, QtGui
from qt_ui import icons_rc



class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(719, 509)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/app.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.import_button = QtGui.QPushButton(self.centralwidget)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/import1.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.import_button.setIcon(icon1)
        self.import_button.setObjectName("import_button")
        self.gridLayout.addWidget(self.import_button, 5, 0, 1, 1)
        self.lineEdit = QtGui.QLineEdit(self.centralwidget)
        self.lineEdit.setObjectName("lineEdit")
        self.gridLayout.addWidget(self.lineEdit, 2, 0, 1, 1)
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 1)
        self.save_reports_button = QtGui.QPushButton(self.centralwidget)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/export.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.save_reports_button.setIcon(icon2)
        self.save_reports_button.setObjectName("save_reports_button")
        self.gridLayout.addWidget(self.save_reports_button, 7, 0, 1, 1)
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.textBrowser = QtGui.QTextBrowser(self.centralwidget)
        self.textBrowser.setObjectName("textBrowser")
        self.gridLayout.addWidget(self.textBrowser, 9, 0, 1, 1)
        self.complexity_check_box = QtGui.QCheckBox(self.centralwidget)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.complexity_check_box.setFont(font)
        self.complexity_check_box.setObjectName("complexity_check_box")
        self.gridLayout.addWidget(self.complexity_check_box, 6, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 719, 21))
        self.menubar.setObjectName("menubar")
        self.menuAbout = QtGui.QMenu(self.menubar)
        self.menuAbout.setObjectName("menuAbout")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.action_developer = QtGui.QAction(MainWindow)
        self.action_developer.setObjectName("action_developer")
        self.actionDicom_Data = QtGui.QAction(MainWindow)
        self.actionDicom_Data.setObjectName("actionDicom_Data")
        self.menuAbout.addAction(self.action_developer)
        self.menubar.addAction(self.menuAbout.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "PyPlanScoring", None, QtGui.QApplication.UnicodeUTF8))
        self.import_button.setToolTip(QtGui.QApplication.translate("MainWindow", "<html><head/><body><p><span style=\" font-weight:600;\">Import\n"
"                                plan data - set the folder containing RP,RS,RD dicom files</span></p></body></html>\n"
"                            ", None, QtGui.QApplication.UnicodeUTF8))
        self.import_button.setText(QtGui.QApplication.translate("MainWindow", "Import Plan Data", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MainWindow", "<html><head/><body><p align=\"center\"><span style=\" font-weight:600;\">2018 Brain Mets SRS – PTV Based </span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.save_reports_button.setToolTip(QtGui.QApplication.translate("MainWindow", "<html><head/><body><p><span style=\" font-weight:600;\">Save\n"
"                                constrains and evaluated scoring reports on *.xls file</span></p></body></html>\n"
"                            ", None, QtGui.QApplication.UnicodeUTF8))
        self.save_reports_button.setText(QtGui.QApplication.translate("MainWindow", "Save Report", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "<html><head/><body><p align=\"center\"><span\n"
"                                style=\" font-weight:600;\">Output File Name</span></p></body></html>\n"
"                            ", None, QtGui.QApplication.UnicodeUTF8))
        self.complexity_check_box.setText(QtGui.QApplication.translate("MainWindow", "Aperture complexity - linac-based dynamic treatments - (IMRT/VMAT)", None, QtGui.QApplication.UnicodeUTF8))
        self.menuAbout.setTitle(QtGui.QApplication.translate("MainWindow", "About", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("MainWindow", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.action_developer.setText(QtGui.QApplication.translate("MainWindow", "Developer", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDicom_Data.setText(QtGui.QApplication.translate("MainWindow", "Dicom Data", None, QtGui.QApplication.UnicodeUTF8))


