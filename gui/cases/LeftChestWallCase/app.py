import os
import platform
import sys

from PySide import QtGui, QtCore

from gui.api.backend import DoseAccumulationBackEnd
from gui.cases.LeftChestWallCase import PyPlanScoringLCWC

__version__ = '0.3.0'
__author__ = 'Dr. Victor Gabriel Leandro Alves, D.Sc.'
__copyright__ = "Copyright (C) 2018 Victor Gabriel Leandro Alves"
__license__ = "Licenced for educational purposes."


def _sys_getenc_wrapper():
    return 'UTF-8'


sys.getfilesystemencoding = _sys_getenc_wrapper

# static variables
# app_folder = os.getcwd()
app_folder = os.path.dirname(os.path.realpath(__file__))
rs_dvh = os.path.join(app_folder, 'RS.dcm')
criteria_file = os.path.join(app_folder, 'Scoring_criteria.xlsx')
ini_file_path = os.path.join(app_folder, 'PyPlanScoring.ini')


class MainDialog(QtGui.QMainWindow, PyPlanScoringLCWC.Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainDialog, self).__init__(parent=parent)
        self.setupUi(self)
        self.folder_root = None
        self.result = None
        self.case_name = 'Photons'
        # calculation kernel
        self.calc_kernel = DoseAccumulationBackEnd()
        # Redirect STD out to
        stdout = OutputWrapper(self, True)
        stdout.outputWritten.connect(self.handle_output)
        stderr = OutputWrapper(self, False)
        stderr.outputWritten.connect(self.handle_output)

        self.worker = Worker()
        # connect Signal and Slots
        self.set_conections()
        self.save_reports_button.setEnabled(False)
        self.textBrowser.setOpenExternalLinks(True)

    def handle_output(self, text, stdout):
        # self.listWidget.addItem(text)
        self.textBrowser.insertPlainText(str(text))

    def set_conections(self):
        self.action_developer.triggered.connect(self.about)
        self.import_button.clicked.connect(self.on_import)
        self.save_reports_button.clicked.connect(self.on_save)
        self.worker.worker_finished.connect(self.worker_done)
        # combo box
        self.plan_type_combo.activated[str].connect(self.on_activated)

    def on_activated(self, val):
        self.case_name = val

    def worker_done(self, obj):
        self.calc_kernel = obj
        self.calc_kernel.save_dvh_data(self.name)
        self.calc_kernel.save_report_data(self.name)

        total_score = self.calc_kernel.total_score
        self.textBrowser.insertPlainText('Total score: %1.2f \n' % total_score)
        self.textBrowser.insertPlainText('---------- Metrics -------------\n')

        # Pretty print
        print(self.calc_kernel.report)

    def setup_case(self, file_path, case_name, ini_file_path, rs_dvh=''):
        if not rs_dvh:
            rs_dvh = self.calc_kernel.dcm_files['rtss']  # TODO add folder DVH file
        self.calc_kernel.setup_case(rs_dvh, file_path, case_name)
        self.calc_kernel.setup_dvh_calculation(ini_file_path)
        self.calc_kernel.setup_planing_item()

    def on_import(self):

        self.textBrowser.clear()
        self.name = self.lineEdit.text()
        if self.name:
            self.folder_root = QtGui.QFileDialog.getExistingDirectory(self,
                                                                      "Select the directory containing only: RP and RD Dicom RT dose files from one plan",
                                                                      QtCore.QDir.currentPath())

            if self.folder_root:
                dcm_files = self.calc_kernel.parse_dicom_folder(self.folder_root)
                if dcm_files['rtdose']:

                    if len(dcm_files['rtdose']) == 1:
                        print("PyPlanScoring is loading", dcm_files['rtdose'])

                    if len(dcm_files['rtdose']) > 1:
                        file_names = [os.path.split(dcm_file)[-1] for dcm_file in dcm_files['rtdose']]
                        print("PyPlanScoring is adding 3D doses from files: ", file_names)

                    # setup case using global variables
                    self.setup_case(criteria_file, self.case_name, ini_file_path, rs_dvh)
                    self.worker.set_calc_kernel(self.calc_kernel)
                    self.save_reports_button.setEnabled(True)
                else:
                    msg = "<p>missing Dicom RT-DOSE file"
                    QtGui.QMessageBox.critical(self, "Missing Data", msg, QtGui.QMessageBox.Abort)
        else:
            msg = "Please set the output file name"
            QtGui.QMessageBox.critical(self, "Missing Data", msg, QtGui.QMessageBox.Abort)

    def on_save(self):
        self.textBrowser.insertPlainText('------------- Calculating DVH and score --------------\n')
        self.worker.start()

    def about(self):
        txt = "PyPlanScoring - 2018 - RT Plan Competition: %s \n" \
              "Be the strongest link in the radiotherapy chain\n" \
              "https://radiationknowledge.org \n" \
              "Author: %s\n" \
              "Copyright (C) 2017 - 2018 Victor Gabriel Leandro Alves, All rights reserved\n" \
              "Platform details: Python %s on %s\n" \
              "This program aims to calculate an approximate score.\n" \
              "your final score may be different due to structure boundaries and dose interpolation uncertainties\n" \
              "%s" \
              % (__version__, __author__, platform.python_version(), platform.system(), __license__)

        QtGui.QMessageBox.about(self, 'Information', txt)


# Inherit from QThread
class Worker(QtCore.QThread):
    # This is the signal that will be emitted during the processing.
    # By including object as an argument, it lets the signal know to expect
    # any object argument when emitting.
    worker_finished = QtCore.Signal(object)

    # You can do any extra things in this init you need, but for this example
    # nothing else needs to be done expect call the super's init
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.calc_kernel = None

    def set_calc_kernel(self, pyplanscoring_kernel):
        self.calc_kernel = pyplanscoring_kernel

    # A QThread is run by calling it's start() function, which calls this run()
    # function in it's own "thread".
    def run(self):
        self.calc_kernel.calculate_dvh()
        self.calc_kernel.calc_plan_score()
        self.worker_finished.emit(self.calc_kernel)


class OutputWrapper(QtCore.QObject):
    """
    Adapted from:
        https://stackoverflow.com/questions/19855288/duplicate-stdout-stderr-in-qtextedit-widget
    """
    outputWritten = QtCore.Signal(object, object)

    def __init__(self, parent, stdout=True):
        QtCore.QObject.__init__(self, parent)
        if stdout:
            self._stream = sys.stdout
            sys.stdout = self
        else:
            self._stream = sys.stderr
            sys.stderr = self
        self._stdout = stdout

    def write(self, text):
        self._stream.write(text)
        self.outputWritten.emit(text, self._stdout)

    def __getattr__(self, name):
        return getattr(self._stream, name)

    def __del__(self):
        try:
            if self._stdout:
                sys.stdout = self._stream
            else:
                sys.stderr = self._stream
        except AttributeError:
            pass


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = MainDialog()
    form.show()
    sys.exit(app.exec_())
