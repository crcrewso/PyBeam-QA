# PyBeam QA
# Copyright (C) 2024 Kagiso Lebang
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from PySide6.QtWidgets import (QWidget, QLabel, QProgressBar, QVBoxLayout, QFileDialog,
                               QListWidgetItem, QMenu, QSizePolicy, QMessageBox, 
                               QMainWindow, QFormLayout, QGridLayout,
                               QSplitter, QComboBox, QDialog, QDialogButtonBox, QLineEdit, 
                               QSpacerItem, QPushButton, QCheckBox, QHBoxLayout, QPlainTextEdit,
                               QDateEdit, QTabWidget)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QSize, QEvent, QThread, Signal, QDate

from ui.py_ui.catphan_worksheet_ui import Ui_QCatPhanWorksheet
from ui.py_ui import icons_rc
from ui.util_widgets import worksheet_save_report
from ui.util_widgets.dialogs import MessageDialog
from ui.util_widgets.statusbar import AnalysisInfoLabel
from ui.linac_qa.qa_tools_win import QAToolsWindow
from core.analysis.catphan import QCatPhan, QCatPhanWorker, CATPHAN_MODEL
from core.tools.report import CatPhanReport
from core.tools.devices import DeviceManager

import platform
import webbrowser
import subprocess
import pyqtgraph as pg
from pathlib import Path
import os

class CatPhanMainWindow(QAToolsWindow):
    """
    Main window for CatPhan analysis.
    """
    
    def __init__(self, initData: dict = None):
        super().__init__(initData)

        self.window_title = "CatPhan Analysis ‒ PyBeam QA"
        self.setWindowTitle(self.window_title)

        self.add_new_worksheet()

        self.ui.menuFile.addAction("Add Image(s)", self.ui.tabWidget.currentWidget().add_files)
        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction("Add New Worksheet", self.add_new_worksheet)

    def add_new_worksheet(self, worksheet_name: str = None, enable_icon: bool = True):
        if worksheet_name is None:
            self.untitled_counter = self.untitled_counter + 1
            worksheet_name = f"CatPhan Analysis (Untitled-{self.untitled_counter})"

        return super().add_new_worksheet(QCatPhanWorksheet(), worksheet_name, enable_icon)

class QCatPhanWorksheet(QWidget):
    """
    Worksheet widget for CatPhan analysis.
    """
    
    analysis_info_signal = Signal(dict)
    save_info_signal = Signal(dict)
    
    def __init__(self):
        super().__init__()

        self.ui = Ui_QCatPhanWorksheet()
        self.ui.setupUi(self)

        self.image_icon = QIcon()
        self.image_icon.addFile(u":/colorIcons/icons/picture.png", QSize(), QIcon.Normal, QIcon.Off)

        self.form_layout = QFormLayout()
        self.form_layout.setHorizontalSpacing(40)
        self.ui.analysisInfoVL.addLayout(self.form_layout)

        self.ui.analyzeBtn.setText("Analyze CT dataset")
        self.ui.advancedViewBtn.setEnabled(False)
        self.ui.genReportBtn.setEnabled(False)
        self.ui.outcomeFrame.hide()

        #--------  add widgets --------
        self.progress_vl = QVBoxLayout()
        self.progress_vl.setSpacing(10)

        self.ui.analysisInfoVL.addLayout(self.progress_vl)

        # setup context menu for image list widget
        self.img_list_contextmenu = QMenu()
        self.img_list_contextmenu.addAction("View Original Image", self.view_dicom_image, "Ctrl+I")
        self.img_list_contextmenu.addAction("Show Containing Folder", self.open_file_folder)
        self.remove_file_action = self.img_list_contextmenu.addAction("Remove from List", self.remove_file)
        self.delete_file_action = self.img_list_contextmenu.addAction("Delete", self.delete_file)
        self.img_list_contextmenu.addAction("Properties")
        self.img_list_contextmenu.addSeparator()
        self.select_all_action = self.img_list_contextmenu.addAction("Select All", lambda: self.perform_selection("selectAll"), "Ctrl+A")
        self.unselect_all_action = self.img_list_contextmenu.addAction("Unselect All", lambda: self.perform_selection("unselectAll"),
                                                                    "Ctrl+Shift+A")
        self.invert_select_action = self.img_list_contextmenu.addAction("Invert Selection", lambda: self.perform_selection("invertSelection"))
        self.img_list_contextmenu.addSeparator()
        self.remove_selected_files_action = self.img_list_contextmenu.addAction("Remove Selected Files", self.remove_selected_files)
        self.remove_all_files_action = self.img_list_contextmenu.addAction("Remove All Files", self.remove_all_files)
        self.ui.imageListWidget.installEventFilter(self)

        #Add all context menu actions to this widget to use shortcuts
        self.addActions(self.img_list_contextmenu.actions())

        self.analysis_progress_bar = QProgressBar()
        self.analysis_progress_bar.setRange(0,0)
        self.analysis_progress_bar.setTextVisible(False)
        self.analysis_progress_bar.setMaximumSize(300, 10)
        self.analysis_progress_bar.setMinimumSize(300, 10)
        self.analysis_progress_bar.hide()

        self.analysis_message_label = QLabel("Analysis in progress")
        self.analysis_message_label.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred))
        self.analysis_message_label.hide()

        self.progress_vl.addWidget(self.analysis_progress_bar, 0, Qt.AlignHCenter)
        self.progress_vl.addWidget(self.analysis_message_label, 0, Qt.AlignHCenter)

        #--------  connect slots -------- 
        self.ui.addImgBtn.clicked.connect(self.add_files)
        self.ui.analyzeBtn.clicked.connect(self.start_analysis)
        self.ui.advancedViewBtn.clicked.connect(self.show_advanced_results_view)
        self.ui.genReportBtn.clicked.connect(self.generate_report)

        #-------- init defaults --------
        self.dicom_files = []
        self.current_results = None
        self.imageView_windows = []
        self.advanced_results_view = None
        self.analysis_in_progress = False
        self.has_analysis = False

        self.setup_config()
        self.update_file_list()

        #Set analysis state and message for status bar
        self.analysis_message = None
        self.analysis_state = AnalysisInfoLabel.IDLE

        # Set initial session save info
        self.report_author = ""
        self.report_institution = ""
        self.report_date = QDate.currentDate()
        self.save_path = ""
        self.save_comment = ""

    def setup_config(self):
        """
        Setup CatPhan analysis configuration options and values.
        """
        self.ui.phantomTypeCB.clear()

        # Add CatPhan models
        self.ui.phantomTypeCB.addItems([model.value for model in CATPHAN_MODEL])
        
        # Set default values
        self.ui.huToleranceDSB.setValue(40.0)
        self.ui.scalingToleranceDSB.setValue(0.05)
        self.ui.lowContrastThresholdDSB.setValue(0.01)
        self.ui.thicknessToleranceDSB.setValue(0.2)
        self.ui.memoryEfficientCB.setChecked(False)
        self.ui.clearBordersCB.setChecked(True)
        self.ui.zipAfterCB.setChecked(False)

    def eventFilter(self, source, event):
        """
        Event filter for handling context menu events.
        """
        if event.type() == QEvent.Type.ContextMenu and source is self.ui.imageListWidget:
            self.img_list_contextmenu.exec(event.globalPos())
            return True
        return super().eventFilter(source, event)

    def add_files(self):
        """
        Add DICOM files to the analysis.
        """
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("DICOM files (*.dcm);;All files (*.*)")
        
        if file_dialog.exec():
            filenames = file_dialog.selectedFiles()
            
            for filename in filenames:
                if filename not in self.dicom_files:
                    self.dicom_files.append(filename)
            
            self.update_file_list()

    def add_folder(self):
        """
        Add a folder of DICOM files to the analysis.
        """
        folder_dialog = QFileDialog()
        folder_dialog.setFileMode(QFileDialog.FileMode.Directory)
        folder_dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        if folder_dialog.exec():
            folder = folder_dialog.selectedFiles()[0]
            self.dicom_files.append(folder)
            self.update_file_list()

    def update_file_list(self):
        """
        Update the file list widget with the current DICOM files.
        """
        self.ui.imageListWidget.clear()
        
        for file_path in self.dicom_files:
            item = QListWidgetItem(os.path.basename(file_path))
            item.setIcon(self.image_icon)
            item.setData(Qt.ItemDataRole.UserRole, {"file_path": file_path})
            self.ui.imageListWidget.addItem(item)

    def view_dicom_image(self):
        """
        View the selected DICOM image.
        """
        selected_items = self.ui.imageListWidget.selectedItems()
        
        if not selected_items:
            return
            
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)["file_path"]
            
            # Open the image with the system's default viewer
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", file_path])
            else:  # Linux
                subprocess.call(["xdg-open", file_path])

    def open_file_folder(self):
        """
        Open the folder containing the selected file.
        """
        selected_items = self.ui.imageListWidget.selectedItems()
        
        if not selected_items:
            return
            
        file_path = selected_items[0].data(Qt.ItemDataRole.UserRole)["file_path"]
        folder_path = os.path.dirname(file_path)
        
        # Open the folder with the system's file explorer
        if platform.system() == "Windows":
            os.startfile(folder_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(["open", folder_path])
        else:  # Linux
            subprocess.call(["xdg-open", folder_path])

    def remove_file(self):
        """
        Remove the selected file from the list.
        """
        selected_items = self.ui.imageListWidget.selectedItems()
        
        if not selected_items:
            return
            
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)["file_path"]
            self.dicom_files.remove(file_path)
            
        self.update_file_list()

    def delete_file(self):
        """
        Delete the selected file from disk.
        """
        selected_items = self.ui.imageListWidget.selectedItems()
        
        if not selected_items:
            return
            
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText("Are you sure you want to delete the selected file(s)?")
        msg_box.setInformativeText("This action cannot be undone.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                file_path = item.data(Qt.ItemDataRole.UserRole)["file_path"]
                
                try:
                    os.remove(file_path)
                    self.dicom_files.remove(file_path)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete file: {str(e)}")
                    
            self.update_file_list()

    def perform_selection(self, action):
        """
        Perform selection actions on the file list.
        """
        if action == "selectAll":
            self.ui.imageListWidget.selectAll()
        elif action == "unselectAll":
            self.ui.imageListWidget.clearSelection()
        elif action == "invertSelection":
            for i in range(self.ui.imageListWidget.count()):
                item = self.ui.imageListWidget.item(i)
                item.setSelected(not item.isSelected())

    def remove_selected_files(self):
        """
        Remove selected files from the list.
        """
        selected_items = self.ui.imageListWidget.selectedItems()
        
        if not selected_items:
            return
            
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)["file_path"]
            self.dicom_files.remove(file_path)
            
        self.update_file_list()

    def remove_all_files(self):
        """
        Remove all files from the list.
        """
        self.dicom_files.clear()
        self.update_file_list()

    def start_analysis(self):
        """
        Start the CatPhan analysis.
        """
        if self.analysis_in_progress:
            return
            
        if not self.dicom_files:
            QMessageBox.warning(self, "Warning", "No DICOM files selected for analysis.")
            return
            
        # Clear previous results
        for i in reversed(range(self.form_layout.count())): 
            self.form_layout.removeRow(i)
            
        self.analysis_in_progress = True
        self.analysis_state = AnalysisInfoLabel.BUSY
        self.analysis_message = "Analyzing CatPhan images..."
        self.analysis_info_signal.emit({"state": self.analysis_state, "message": self.analysis_message})
        
        self.analysis_progress_bar.show()
        self.analysis_message_label.setText("Analysis in progress...")
        self.analysis_message_label.show()
        
        # Get analysis parameters
        phantom_model = self.ui.phantomTypeCB.currentText()
        hu_tolerance = self.ui.huToleranceDSB.value()
        scaling_tolerance = self.ui.scalingToleranceDSB.value()
        low_contrast_threshold = self.ui.lowContrastThresholdDSB.value()
        thickness_tolerance = self.ui.thicknessToleranceDSB.value()
        memory_efficient_mode = self.ui.memoryEfficientCB.isChecked()
        clear_borders = self.ui.clearBordersCB.isChecked()
        zip_after = self.ui.zipAfterCB.isChecked()
        
        # Create worker thread
        self.worker_thread = QThread()
        self.worker = QCatPhanWorker(
            phantom_model=phantom_model,
            filepath=self.dicom_files,
            memory_efficient_mode=memory_efficient_mode,
            hu_tolerance=hu_tolerance,
            scaling_tolerance=scaling_tolerance,
            low_contrast_threshold=low_contrast_threshold,
            thickness_tolerance=thickness_tolerance,
            zip_after=zip_after,
            clear_borders=clear_borders
        )
        
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.analyze)
        self.worker.analysis_progress.connect(self.update_analysis_progress)
        self.worker.analysis_results_ready.connect(self.display_analysis_results)
        self.worker.analysis_failed.connect(self.analysis_failed)
        self.worker.thread_finished.connect(self.worker_thread.quit)
        self.worker.thread_finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.analysis_finished)
        
        self.worker_thread.start()

    def update_analysis_progress(self, message):
        """
        Update the analysis progress message.
        """
        self.analysis_message_label.setText(message)
        self.analysis_message = message
        self.analysis_info_signal.emit({"state": self.analysis_state, "message": self.analysis_message})

    def analysis_failed(self, error_message):
        """
        Handle analysis failure.
        """
        self.analysis_progress_bar.hide()
        self.analysis_message_label.hide()
        
        self.analysis_state = AnalysisInfoLabel.ERROR
        self.analysis_message = f"Analysis failed: {error_message}"
        self.analysis_info_signal.emit({"state": self.analysis_state, "message": self.analysis_message})
        
        QMessageBox.critical(self, "Analysis Error", f"Analysis failed: {error_message}")

    def analysis_finished(self):
        """
        Clean up after analysis is complete.
        """
        self.analysis_in_progress = False
        self.analysis_progress_bar.hide()
        self.analysis_message_label.hide()

    def display_analysis_results(self, results):
        """
        Display the analysis results.
        """
        self.current_results = results
        self.has_analysis = True
        
        # Update status
        self.analysis_state = AnalysisInfoLabel.DONE
        self.analysis_message = "Analysis complete"
        self.analysis_info_signal.emit({"state": self.analysis_state, "message": self.analysis_message})
        
        # Show outcome frame
        self.ui.outcomeFrame.show()
        self.ui.advancedViewBtn.setEnabled(True)
        self.ui.genReportBtn.setEnabled(True)
        
        # Display summary results
        for label, value in results["summary_text"]:
            row_label = QLabel(label)
            row_value = QLabel(value)
            row_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.form_layout.addRow(row_label, row_value)
        
        # Store summary for report generation
        self.analysis_summary = {label: value for label, value in results["summary_text"]}
        
        # Create a basic results display
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        # Add the analyzed image
        catphan_obj = results["catphan_obj"]
        catphan_obj.qplot_analyzed_image()
        results_layout.addWidget(catphan_obj.analyzed_image_plot_widget)
        
        # Add the widget to the layout
        self.ui.analysisInfoVL.addWidget(results_widget)

    def show_advanced_results_view(self):
        """
        Show the advanced results view.
        """
        if self.advanced_results_view is None:
            self.advanced_results_view = CatPhanAdvancedView(catphan=self.current_results["catphan_obj"])
            self.advanced_results_view.showMaximized()
        else: 
            self.advanced_results_view.showMaximized()
    
    def generate_report(self):
        """
        Generate a report of the analysis results.
        """
        physicist_name_le = QLineEdit()
        institution_name_le = QLineEdit()
        treatment_unit_le = QComboBox()
        analysis_date = QDateEdit()
        comments_te = QPlainTextEdit()
        treatment_unit_le.setEditable(True)
        physicist_name_le.setMaximumWidth(250)
        physicist_name_le.setMinimumWidth(250)
        institution_name_le.setMaximumWidth(350)
        institution_name_le.setMinimumWidth(350)
        treatment_unit_le.setMaximumWidth(250)
        treatment_unit_le.setMinimumWidth(250)
        analysis_date.setMaximumWidth(120)
        analysis_date.setCalendarPopup(True)
        analysis_date.setDisplayFormat("dd MMMM yyyy")
        analysis_date.setMaximumDate(QDate.currentDate())

        # restore current save info
        physicist_name_le.setText(self.report_author)
        institution_name_le.setText(self.report_institution)
        analysis_date.setDate(self.report_date)
        comments_te.setPlainText(self.save_comment)

        save_path_le = QLineEdit()
        save_win_btn = QPushButton("Save to...")
        save_path_le.setReadOnly(True)
        save_location_layout = QHBoxLayout()
        save_location_layout.addWidget(save_path_le)
        save_location_layout.addWidget(save_win_btn)

        show_report_checkbox = QCheckBox()
        show_report_label = QLabel("Open report:")
        show_report_checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        show_report_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        show_report_layout = QHBoxLayout()
        show_report_layout.addWidget(show_report_label)
        show_report_layout.addWidget(show_report_checkbox)

        # get linac devices
        linac_devices = DeviceManager.device_list["linacs"]
        treatment_unit_le.addItems([linac.name for linac in linac_devices])

        user_details_layout = QFormLayout()
        user_details_layout.addRow("Physicist:", physicist_name_le)
        user_details_layout.addRow("Treatment unit:", treatment_unit_le)
        user_details_layout.addRow("Institution:", institution_name_le)
        user_details_layout.addRow("Save location:", save_location_layout)
        user_details_layout.addRow("Analysis date:", analysis_date)
        user_details_layout.addRow("Comments:", comments_te)
        user_details_layout.addRow("", show_report_layout)
        user_details_layout.addItem(QSpacerItem(1, 10, QSizePolicy.Policy.Minimum,
                                                QSizePolicy.Policy.Minimum))
        
        layout = QVBoxLayout()
        layout.addLayout(user_details_layout)

        dialog_buttons = QDialogButtonBox()
        save_button = dialog_buttons.addButton(QDialogButtonBox.StandardButton(
            QDialogButtonBox.StandardButton.Save))
        save_button.setEnabled(False)
        cancel_button = dialog_buttons.addButton(QDialogButtonBox.StandardButton(
            QDialogButtonBox.StandardButton.Cancel))
        
        # enable the save button once we have a path to save the report to
        save_path_le.textChanged.connect(lambda: save_button.setEnabled(True))
        
        layout.addWidget(dialog_buttons)

        report_dialog = QDialog()
        report_dialog.setWindowTitle("Generate CatPhan Report ‒ PyBeam QA")
        report_dialog.setLayout(layout)
        report_dialog.setMinimumSize(report_dialog.sizeHint())
        report_dialog.setMaximumSize(report_dialog.sizeHint())

        cancel_button.clicked.connect(report_dialog.reject)
        save_button.clicked.connect(report_dialog.accept)
        save_win_btn.clicked.connect(lambda: save_path_le.setText(worksheet_save_report(self)))

        result = report_dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # Amend save info
            self.report_author = physicist_name_le.text()
            self.report_institution = institution_name_le.text()
            self.save_comment = comments_te.toPlainText()
            self.report_date = analysis_date.date()

            physicist_name = "N/A" if physicist_name_le.text() == "" else physicist_name_le.text()
            institution_name = "N/A" if institution_name_le.text() == "" else institution_name_le.text()
            treatment_unit = "N/A" if treatment_unit_le.currentText() == "" else treatment_unit_le.currentText()

            catphan = self.current_results["catphan_obj"]
            results_data = self.current_results["results_data"]

            report = CatPhanReport(
                save_path_le.text(),
                author=physicist_name,
                institution=institution_name,
                treatment_unit_name=treatment_unit,
                analysis_date=self.report_date.toString("dd MMMM yyyy"),
                phantom_model=results_data.catphan_model,
                summary_plots=catphan.get_publishable_plots(),
                analysis_summary=self.analysis_summary,
                comments=comments_te.toPlainText()
            )
        
            report.save_report()

            if show_report_checkbox.isChecked():
                webbrowser.open(save_path_le.text())

class CatPhanAdvancedView(QMainWindow):
    """
    Advanced view for CatPhan analysis results.
    """
    
    def __init__(self, parent: QWidget = None, catphan: QCatPhan = None):
        super().__init__(parent=parent)

        self.catphan = catphan
 
        self.initComplete = False

        self.setWindowTitle("CatPhan Analysis (Advanced Results) ‒ PyBeam QA")
        self.resize(1024, 768)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget for different analysis components
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # Create tabs for each analysis component
        self.overview_tab = QWidget()
        self.hu_linearity_tab = QWidget()
        self.uniformity_tab = QWidget()
        self.mtf_tab = QWidget()
        self.low_contrast_tab = QWidget()

        # Add tabs to the tab widget
        self.tab_widget.addTab(self.overview_tab, "Overview")
        self.tab_widget.addTab(self.hu_linearity_tab, "HU Linearity")
        self.tab_widget.addTab(self.uniformity_tab, "Uniformity")
        self.tab_widget.addTab(self.mtf_tab, "MTF")
        self.tab_widget.addTab(self.low_contrast_tab, "Low Contrast")

        # Set up layouts for each tab
        self.overview_layout = QVBoxLayout(self.overview_tab)
        self.hu_linearity_layout = QVBoxLayout(self.hu_linearity_tab)
        self.uniformity_layout = QVBoxLayout(self.uniformity_tab)
        self.mtf_layout = QVBoxLayout(self.mtf_tab)
        self.low_contrast_layout = QVBoxLayout(self.low_contrast_tab)

        if catphan is not None:
            self.init_plots()

        self.initComplete = True
    
    def init_plots(self):
        """
        Initialize the plots for each tab.
        """
        # Overview tab - analyzed image
        self.catphan.qplot_analyzed_image()
        self.overview_layout.addWidget(self.catphan.analyzed_image_plot_widget)

        # HU Linearity tab
        self.catphan.qplot_hu_linearity()
        self.hu_linearity_layout.addWidget(self.catphan.hu_linearity_plot_widget)

        # Uniformity tab
        self.catphan.qplot_uniformity()
        self.uniformity_layout.addWidget(self.catphan.uniformity_plot_widget)

        # MTF tab
        self.catphan.qplot_mtf()
        self.mtf_layout.addWidget(self.catphan.mtf_plot_widget)

        # Low Contrast tab
        self.catphan.qplot_low_contrast()
        self.low_contrast_layout.addWidget(self.catphan.low_contrast_plot_widget)

