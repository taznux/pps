# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\vgalves\Dropbox\Plan_Competition_Project\pyplanscoring\PyPlanScoring.ui'
#
# Created: Thu Mar  9 14:09:42 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui


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
        self.lineEdit = QtGui.QLineEdit(self.centralwidget)
        self.lineEdit.setObjectName("lineEdit")
        self.gridLayout.addWidget(self.lineEdit, 2, 0, 1, 1)
        self.save_reports_button = QtGui.QPushButton(self.centralwidget)
        self.save_reports_button.setObjectName("save_reports_button")
        self.gridLayout.addWidget(self.save_reports_button, 4, 0, 1, 1)
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.import_button = QtGui.QPushButton(self.centralwidget)
        self.import_button.setObjectName("import_button")
        self.gridLayout.addWidget(self.import_button, 3, 0, 1, 1)
        self.listWidget = QtGui.QListWidget(self.centralwidget)
        self.listWidget.setObjectName("listWidget")
        self.gridLayout.addWidget(self.listWidget, 5, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 719, 20))
        self.menubar.setObjectName("menubar")
        self.menuAbout = QtGui.QMenu(self.menubar)
        self.menuAbout.setObjectName("menuAbout")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.action_developer = QtGui.QAction(MainWindow)
        self.action_developer.setObjectName("action_developer")
        self.actionDicom_Data = QtGui.QAction(MainWindow)
        self.actionDicom_Data.setObjectName("actionDicom_Data")
        self.menuAbout.addAction(self.action_developer)
        self.menubar.addAction(self.menuAbout.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QtGui.QApplication.translate("MainWindow", "PyPlanScoring", None, QtGui.QApplication.UnicodeUTF8))
        self.save_reports_button.setToolTip(
            QtGui.QApplication.translate("MainWindow", "<html><head/><body><p><span style=\" font-weight:600;\">Save\n"
                                                       "                                constrains and evaluated scoring reports on *.xls file</span></p></body></html>",
                                         None, QtGui.QApplication.UnicodeUTF8))
        self.save_reports_button.setText(
            QtGui.QApplication.translate("MainWindow", "Save Reports", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "<html><head/><body><p align=\"center\"><span\n"
                                                                      "                                style=\" font-weight:600;\">Participant\'s name</span></p></body></html>",
                                                        None, QtGui.QApplication.UnicodeUTF8))
        self.import_button.setToolTip(QtGui.QApplication.translate("MainWindow",
                                                                   "<html><head/><body><p><span style=\" font-weight:600;\">Import\n"
                                                                   "                                plan data - set the folder containing RP,RS,RD dicom files</span></p></body></html>",
                                                                   None, QtGui.QApplication.UnicodeUTF8))
        self.import_button.setText(
            QtGui.QApplication.translate("MainWindow", "Import Plan Data", None, QtGui.QApplication.UnicodeUTF8))
        self.listWidget.setToolTip(QtGui.QApplication.translate("MainWindow",
                                                                "<html><head/><body><p><span style=\" font-weight:600;\">Import\n"
                                                                "                                plan data - set the folder containing RP,RS,RD dicom files</span></p></body></html>",
                                                                None, QtGui.QApplication.UnicodeUTF8))
        self.menuAbout.setTitle(
            QtGui.QApplication.translate("MainWindow", "About", None, QtGui.QApplication.UnicodeUTF8))
        self.action_developer.setText(
            QtGui.QApplication.translate("MainWindow", "Developer", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDicom_Data.setText(
            QtGui.QApplication.translate("MainWindow", "Dicom Data", None, QtGui.QApplication.UnicodeUTF8))
