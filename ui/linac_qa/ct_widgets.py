from PySide6.QtWidgets import (QWidget, QLabel, QProgressBar, QVBoxLayout, QFileDialog,
                               QListWidgetItem, QMenu, QSizePolicy, QMessageBox, 
                               QMainWindow, QFormLayout, QGridLayout,
                               QSplitter, QComboBox, QDialog, QDialogButtonBox, QLineEdit, 
                               QSpacerItem, QPushButton, QCheckBox, QHBoxLayout, QPlainTextEdit,
                               QDateEdit, QTableWidget, QTableWidgetItem)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QSize, QEvent, QThread, Signal, QDate

from ui.py_ui import icons_rc
from ui.util_widgets import worksheet_save_report
from ui.util_widgets.dialogs import MessageDialog
from ui.util_widgets.statusbar import AnalysisInfoLabel
from ui.linac_qa.qa_tools_win import QAToolsWindow
from core.analysis.ct import QCTAnalysis, QCTAnalysisWorker, PHANTOM
from core.tools.devices import DeviceManager

import platform
import webbrowser
import subprocess
import pyqtgraph as pg
from pathlib import Path

class CTAnalysisMainWindow(QAToolsWindow):
    
    def __init__(self, initData: dict = None):
        super().__init__(initData)

        self.window_title = "CT Analysis ‒ PyBeam QA"
        self.setWindowTitle(self.window_title)

        self.add_new_worksheet()

        self.ui.menuFile.addAction("Select CT Dataset", self.ui.tabWidget.currentWidget().add_dataset)
        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction("Add New Worksheet", self.add_new_worksheet)

    def add_new_worksheet(self, worksheet_name: str = None, enable_icon: bool = True):
        if worksheet_name is None:
            self.untitled_counter = self.untitled_counter + 1
            worksheet_name = f"CT Analysis (Untitled-{self.untitled_counter})"

        return super().add_new_worksheet(QCTAnalysisWorksheet(), worksheet_name, enable_icon)

class QCTAnalysisWorksheet(QWidget):

    analysis_info_signal = Signal(dict)
    save_info_signal = Signal(dict)

    def __init__(self):
        super().__init__()

        # Setup the UI manually since we don't have a UI file for CT analysis yet
        self.setup_ui()

        self.dataset_icon = QIcon()
        self.dataset_icon.addFile(u":/colorIcons/icons/picture.png", QSize(), QIcon.Normal, QIcon.Off)

        self.form_layout = QFormLayout()
        self.form_layout.setHorizontalSpacing(40)
        self.analysisInfoVL.addLayout(self.form_layout)

        self.analyzeBtn.setText("Analyze CT dataset")
        self.advancedViewBtn.setEnabled(False)
        self.genReportBtn.setEnabled(False)
        self.outcomeFrame.hide()

        # Add widgets
        self.progress_vl = QVBoxLayout()
        self.progress_vl.setSpacing(10)

        self.analysisInfoVL.addLayout(self.progress_vl)

        # Setup context menu for dataset list widget
        self.dataset_list_contextmenu = QMenu()
        self.dataset_list_contextmenu.addAction("Show Containing Folder", self.open_file_folder)
        self.remove_file_action = self.dataset_list_contextmenu.addAction("Remove from List", self.remove_file)
        self.dataset_list_contextmenu.addSeparator()
        self.select_all_action = self.dataset_list_contextmenu.addAction("Select All", lambda: self.perform_selection("selectAll"), "Ctrl+A")
        self.unselect_all_action = self.dataset_list_contextmenu.addAction("Unselect All", lambda: self.perform_selection("unselectAll"), "Ctrl+Shift+A")

        # Connect signals
        self.datasetListWidget.customContextMenuRequested.connect(self.show_context_menu)
        self.datasetListWidget.itemClicked.connect(lambda: self.update_selected_dataset())
        self.addDatasetBtn.clicked.connect(self.add_dataset)
        self.analyzeBtn.clicked.connect(self.start_analysis)
        self.advancedViewBtn.clicked.connect(self.show_advanced_view)
        self.genReportBtn.clicked.connect(self.generate_report)
        self.phantomTypeCB.currentIndexChanged.connect(self.on_config_change)

        # Setup configuration
        self.setup_config()

        # Initialize properties
        self.selected_dataset = []
        self.imageView_windows = []
        self.analysis_worker = None
        self.analysis_thread = None
        self.analysis_in_progress = False
        self.advanced_results_view = None
        self.analysis_state = AnalysisInfoLabel.IDLE
        self.analysis_message = None
        self.analysis_summary = {}
        self.analysis_progress_bar = QProgressBar()
        self.analysis_progress_bar.setMaximum(0)
        self.analysis_progress_bar.setMinimum(0)
        self.analysis_progress_bar.hide()
        self.analysis_message_label = QLabel("Analysis in progress")
        self.analysis_message_label.hide()
        self.progress_vl.addWidget(self.analysis_message_label)
        self.progress_vl.addWidget(self.analysis_progress_bar)

    def setup_ui(self):
        # Main layout
        self.main_layout = QGridLayout(self)
        self.main_layout.setContentsMargins(9, 9, 9, 9)
        
        # Left panel - Dataset selection
        self.leftFrame = QWidget(self)
        self.leftFrameLayout = QVBoxLayout(self.leftFrame)
        self.leftFrameLayout.setContentsMargins(0, 0, 0, 0)
        
        # Dataset list
        self.datasetListLabel = QLabel("CT Datasets:", self.leftFrame)
        self.leftFrameLayout.addWidget(self.datasetListLabel)
        
        self.datasetListWidget = QListWidget(self.leftFrame)
        self.datasetListWidget.setSelectionMode(QListWidget.ExtendedSelection)
        self.datasetListWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.leftFrameLayout.addWidget(self.datasetListWidget)
        
        # Add dataset button
        self.addDatasetBtn = QPushButton("Add CT Dataset", self.leftFrame)
        self.leftFrameLayout.addWidget(self.addDatasetBtn)
        
        # Configuration group
        self.configGroupBox = QWidget(self.leftFrame)
        self.configGroupBoxLayout = QVBoxLayout(self.configGroupBox)
        self.configGroupBoxLayout.setContentsMargins(0, 0, 0, 0)
        
        self.configLabel = QLabel("Configuration:", self.configGroupBox)
        self.configGroupBoxLayout.addWidget(self.configLabel)
        
        # Phantom type selection
        self.phantomTypeLayout = QHBoxLayout()
        self.phantomTypeLabel = QLabel("Phantom Type:", self.configGroupBox)
        self.phantomTypeCB = QComboBox(self.configGroupBox)
        self.phantomTypeLayout.addWidget(self.phantomTypeLabel)
        self.phantomTypeLayout.addWidget(self.phantomTypeCB)
        self.configGroupBoxLayout.addLayout(self.phantomTypeLayout)
        
        self.leftFrameLayout.addWidget(self.configGroupBox)
        
        # Analyze button
        self.analyzeBtn = QPushButton("Analyze", self.leftFrame)
        self.leftFrameLayout.addWidget(self.analyzeBtn)
        
        # Right panel - Analysis results
        self.rightFrame = QWidget(self)
        self.rightFrameLayout = QVBoxLayout(self.rightFrame)
        self.rightFrameLayout.setContentsMargins(0, 0, 0, 0)
        
        # Analysis outcome frame
        self.outcomeFrame = QWidget(self.rightFrame)
        self.outcomeFrameLayout = QHBoxLayout(self.outcomeFrame)
        self.outcomeFrameLayout.setContentsMargins(0, 0, 0, 0)
        
        self.advancedViewBtn = QPushButton("Advanced View", self.outcomeFrame)
        self.genReportBtn = QPushButton("Generate Report", self.outcomeFrame)
        
        self.outcomeFrameLayout.addWidget(self.advancedViewBtn)
        self.outcomeFrameLayout.addWidget(self.genReportBtn)
        
        self.rightFrameLayout.addWidget(self.outcomeFrame)
        
        # Analysis info
        self.analysisInfoVL = QVBoxLayout()
        self.rightFrameLayout.addLayout(self.analysisInfoVL)
        
        # Add frames to main layout
        self.main_layout.addWidget(self.leftFrame, 0, 0, 1, 1)
        self.main_layout.addWidget(self.rightFrame, 0, 1, 1, 1)
        
        # Set stretch factors
        self.main_layout.setColumnStretch(0, 1)  # Left panel
        self.main_layout.setColumnStretch(1, 2)  # Right panel

    def setup_config(self):
        """
        Setup CT analysis configuration options and values.
        """
        self.phantomTypeCB.clear()
        
        # Add phantom types
        for phantom in PHANTOM:
            self.phantomTypeCB.addItem(phantom.value)
        
        # Set default phantom type
        self.phantomTypeCB.setCurrentText(PHANTOM.CATPHAN_504.value)

    def on_config_change(self):
        """Handler for configuration changes"""
        # This can be expanded if more configuration options are added
        pass

    def add_dataset(self):
        """Add a CT dataset (zip file) to the list"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CT Dataset (ZIP)",
            "",
            "ZIP Files (*.zip)",
        )

        if file_path:
            path = Path(file_path)
            
            itemData = {
                "file_path": str(path),
                "analysis_data": None
            }
            
            listItemWidget = QListWidgetItem(self.datasetListWidget)
            listItemWidget.setText(path.name)
            listItemWidget.setIcon(self.dataset_icon)
            listItemWidget.setCheckState(Qt.Unchecked)
            listItemWidget.setData(Qt.UserRole, itemData)
            
            self.update_selected_dataset()

    def update_selected_dataset(self):
        """Update the list of selected dataset"""
        self.selected_dataset = []
        
        for i in range(self.datasetListWidget.count()):
            item = self.datasetListWidget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                self.selected_dataset.append(item.data(Qt.UserRole))
        
        if len(self.selected_dataset) > 0 and not self.analysis_in_progress:
            self.analyzeBtn.setEnabled(True)
        else:
            self.analyzeBtn.setEnabled(False)

    def show_context_menu(self, pos):
        """Show context menu for dataset list"""
        self.dataset_list_contextmenu.exec(self.datasetListWidget.mapToGlobal(pos))

    def open_file_folder(self):
        """Open the folder containing the selected file"""
        selected_items = self.datasetListWidget.selectedItems()
        
        if selected_items:
            file_path = selected_items[0].data(Qt.UserRole)["file_path"]
            
            if platform.system() == "Windows":
                subprocess.Popen(f'explorer /select,"{file_path}"')
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-R", file_path])
            else:
                subprocess.Popen(["xdg-open", str(Path(file_path).parent)])

    def remove_file(self):
        """Remove the selected file from the list"""
        selected_items = self.datasetListWidget.selectedItems()
        
        for item in selected_items:
            row = self.datasetListWidget.row(item)
            self.datasetListWidget.takeItem(row)
        
        self.update_selected_dataset()

    def perform_selection(self, select_type: str):
        """Select or unselect all items in the list"""
        for i in range(self.datasetListWidget.count()):
            if select_type == "selectAll":
                self.datasetListWidget.item(i).setCheckState(Qt.CheckState.Checked)
            else:
                self.datasetListWidget.item(i).setCheckState(Qt.CheckState.Unchecked)
        
        self.update_selected_dataset()

    def start_analysis(self):
        """Start CT dataset analysis"""
        self.analysis_info_signal.emit({
            "state": AnalysisInfoLabel.IN_PROGRESS,
            "message": None
        })
        self.analysis_state = AnalysisInfoLabel.IN_PROGRESS
        self.analysis_message = None

        self.analysis_in_progress = True
        self.advancedViewBtn.setEnabled(False)
        self.genReportBtn.setEnabled(False)

        row_count = self.form_layout.rowCount()
        for i in range(row_count):
            self.form_layout.removeRow(row_count - (i+1))

        self.addDatasetBtn.setEnabled(False)
        self.genReportBtn.setEnabled(False)
        self.analyzeBtn.setEnabled(False)
        self.analyzeBtn.setText("Analysis in progress...")
        self.analysis_message_label.setText("Analysis in progress")
        self.analysis_progress_bar.show()
        self.analysis_message_label.show()

        # Get the selected dataset
        if len(self.selected_dataset) > 0:
            dataset = self.selected_dataset[0]
            
            # Get phantom type
            phantom_type = PHANTOM.CATPHAN_504  # Default
            for phantom in PHANTOM:
                if phantom.value == self.phantomTypeCB.currentText():
                    phantom_type = phantom
                    break
            
            # Create worker thread
            self.analysis_thread = QThread()
            self.analysis_worker = QCTAnalysisWorker(dataset["file_path"], phantom_type)
            self.analysis_worker.moveToThread(self.analysis_thread)
            
            # Connect signals
            self.analysis_thread.started.connect(self.analysis_worker.analyze)
            self.analysis_worker.analysis_progress.connect(self.update_analysis_progress)
            self.analysis_worker.analysis_results_ready.connect(self.show_analysis_results)
            self.analysis_worker.analysis_failed.connect(self.analysis_failed)
            self.analysis_worker.thread_finished.connect(self.analysis_thread.quit)
            self.analysis_worker.thread_finished.connect(self.analysis_worker.deleteLater)
            self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)
            
            # Start analysis
            self.analysis_thread.start()

    def update_analysis_progress(self, message: str):
        """Update analysis progress message"""
        self.analysis_message_label.setText(message)

    def analysis_failed(self, error_message: str):
        """Handle analysis failure"""
        self.analyzeBtn.setText("Analyze CT dataset")
        self.analyzeBtn.setEnabled(True)
        self.addDatasetBtn.setEnabled(True)
        self.analysis_progress_bar.hide()
        self.analysis_message_label.hide()
        self.analysis_in_progress = False
        
        self.analysis_info_signal.emit({
            "state": AnalysisInfoLabel.FAILURE,
            "message": error_message
        })
        self.analysis_state = AnalysisInfoLabel.FAILURE
        self.analysis_message = error_message
        
        # Show error message
        error_dialog = MessageDialog()
        error_dialog.set_icon(MessageDialog.ERROR_ICON)
        error_dialog.set_title("Analysis Error")
        error_dialog.set_header_text("CT Analysis Failed")
        error_dialog.set_info_text(error_message)
        error_dialog.exec_()

    def show_analysis_results(self, results: dict):
        """Display analysis results"""
        self.analyzeBtn.setText("Analyze CT dataset")
        self.analyzeBtn.setEnabled(True)
        self.addDatasetBtn.setEnabled(True)
        self.advancedViewBtn.setEnabled(True)
        self.genReportBtn.setEnabled(True)
        self.analysis_progress_bar.hide()
        self.analysis_message_label.hide()
        self.outcomeFrame.show()
        self.analysis_in_progress = False
        
        # Update the selected dataset with analysis results
        if len(self.selected_dataset) > 0:
            dataset = self.selected_dataset[0]
            item_data = dataset
            item_data["analysis_data"] = results
            
            # Find the item in the list and update its data
            for i in range(self.datasetListWidget.count()):
                item = self.datasetListWidget.item(i)
                if item.data(Qt.UserRole)["file_path"] == dataset["file_path"]:
                    item.setData(Qt.UserRole, item_data)
                    break
        
        # Display results
        summary_text = results["summary_text"]
        
        for row in summary_text:
            if len(row) == 2:
                label = QLabel(row[0])
                value = QLabel(row[1])
                label.setStyleSheet("font-weight: bold;")
                self.form_layout.addRow(label, value)
        
        # Update analysis info
        self.analysis_info_signal.emit({
            "state": AnalysisInfoLabel.SUCCESS,
            "message": None
        })
        self.analysis_state = AnalysisInfoLabel.SUCCESS
        self.analysis_message = None
        
        # Update advanced view
        ct_analysis = results["ct_analysis_obj"]
        if self.advanced_results_view is not None:
            self.advanced_results_view.update_ct_analysis(ct_analysis)

    def show_advanced_view(self):
        """Show advanced CT analysis view"""
        if len(self.selected_dataset) > 0:
            dataset = self.selected_dataset[0]
            
            if dataset["analysis_data"] is not None:
                ct_analysis = dataset["analysis_data"]["ct_analysis_obj"]
                
                if self.advanced_results_view is None:
                    self.advanced_results_view = AdvancedCTView(self, ct_analysis)
                    self.advanced_results_view.show()
                else:
                    self.advanced_results_view.update_ct_analysis(ct_analysis)
                    self.advanced_results_view.show()
                    self.advanced_results_view.activateWindow()

    def generate_report(self):
        """Generate a PDF report of the analysis results"""
        if len(self.selected_dataset) > 0:
            dataset = self.selected_dataset[0]
            
            if dataset["analysis_data"] is not None:
                # Show save dialog
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save CT Analysis Report",
                    "",
                    "PDF Files (*.pdf)"
                )
                
                if file_path:
                    # Create a simple report
                    from core.tools.report import SimpleReport
                    
                    report = SimpleReport()
                    report.title = "CT Analysis Report"
                    report.date = QDate.currentDate().toString(Qt.ISODate)
                    
                    # Add summary text
                    summary_text = dataset["analysis_data"]["summary_text"]
                    summary_table = []
                    
                    for row in summary_text:
                        if len(row) == 2:
                            summary_table.append(row)
                    
                    report.add_table("Analysis Results", summary_table)
                    
                    # Add plots
                    ct_analysis = dataset["analysis_data"]["ct_analysis_obj"]
                    plot_images = ct_analysis.get_publishable_plots()
                    
                    for i, plot in enumerate(plot_images):
                        report.add_image(f"Plot {i+1}", plot)
                    
                    # Save report
                    report.save(file_path)
                    
                    # Open the report
                    if platform.system() == "Windows":
                        os.startfile(file_path)
                    elif platform.system() == "Darwin":
                        subprocess.call(["open", file_path])
                    else:
                        subprocess.call(["xdg-open", file_path])

class AdvancedCTView(QMainWindow):
    """Advanced view for CT analysis results"""
    
    def __init__(self, parent: QWidget | None = None, ct_analysis: QCTAnalysis = None):
        super().__init__(parent=parent)
        
        self.ct_analysis = ct_analysis
        
        self.initComplete = False
        
        self.setWindowTitle("CT Analysis (Advanced Results) ‒ PyBeam QA")
        self.resize(900, 600)
        
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        self.top_layout = QGridLayout(self.central_widget)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_policy.setVerticalStretch(0)
        size_policy.setHorizontalStretch(0)
        self.central_widget.setSizePolicy(size_policy)
        
        # Setup content
        self.tab_widget = QTabWidget(self.central_widget)
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setSizePolicy(size_policy)
        
        # Add tabs for different CT modules
        self.analyzed_img_qSplitter = QSplitter()
        self.analyzed_img_qSplitter.setSizePolicy(size_policy)
        
        self.tab_widget.addTab(self.analyzed_img_qSplitter, "CT Analysis Results")
        
        self.top_layout.addWidget(self.tab_widget, 0, 0, 1, 1)
        
        if ct_analysis is not None:
            self.update_ct_analysis(ct_analysis)
    
    def update_ct_analysis(self, ct_analysis: QCTAnalysis):
        """Update the CT analysis results display"""
        self.ct_analysis = ct_analysis
        
        # Clear existing widgets
        for i in reversed(range(self.analyzed_img_qSplitter.count())):
            self.analyzed_img_qSplitter.widget(i).deleteLater()
        
        # Create the plot widget
        ct_analysis.qplot_analyzed_image()
        self.analyzed_img_qSplitter.addWidget(ct_analysis.analyzed_image_plot_widget)
        
        # Update the window
        self.analyzed_img_qSplitter.refresh()
        self.update()