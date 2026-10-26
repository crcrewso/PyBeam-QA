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
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""The CatPhan (CT/CBCT) tool: a window of worksheets, each analysing one CT series of a CatPhan 503/504/600/604/700.

A series is added as a .zip of its DICOM files or as a folder. The worksheet reads only the
:class:`core.results.catphan.CatPhanResult` the worker emits; PASS/FAIL comes from that result's checks, not from
UI code. See docs/adding-a-pylinac-test.md, which this tool follows step by step.
"""

import platform
import subprocess
import webbrowser
from pathlib import Path

from PySide6.QtCore import QDate, QEvent, QSize, Qt, QThread, Slot
from PySide6.QtGui import QBrush, QColor, QIcon, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
                               QFileDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidgetItem,
                               QMenu, QPlainTextEdit, QProgressBar, QPushButton, QSizePolicy, QSpacerItem,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
from PySide6.QtCore import Signal

from ui.py_ui import icons_rc  # noqa: F401  (registers the Qt resources)
from ui.py_ui.catphan_worksheet_ui import Ui_QCatPhanWorksheet
from ui.util_widgets import worksheet_save_report
from ui.util_widgets.dialogs import MessageDialog
from ui.util_widgets.statusbar import AnalysisInfoLabel
from ui.linac_qa.qa_tools_win import QAToolsWindow
from core.analysis.catphan import CONTRAST_METHODS, DEFAULT_PARAMETERS, PHANTOMS, QCatPhanWorker
from core.results.catphan import CatPhanResult
from core.tools.devices import DeviceManager
from core.tools.report import CatPhanReport

DEFAULT_PHANTOM = "CatPhan 504"

_OUTCOME_STYLE = ("border-color: {border};\nborder-radius: 15px;\nborder-style: solid;\nborder-width: 2px;\n"
                  "background-color: {background};\npadding-left: 15px;\nheight: 30px;\nfont-weight: bold;\n")
NEUTRAL_STYLE = _OUTCOME_STYLE.format(border="rgba(0, 0, 0, 0)", background="rgba(0, 0, 0, 0)")
PASS_STYLE = _OUTCOME_STYLE.format(border="rgb(95, 200, 26)", background="rgba(95, 200, 26, 150)")
FAIL_STYLE = _OUTCOME_STYLE.format(border="rgb(231, 29, 14)", background="rgba(231, 29, 14, 150)")
FAIL_BRUSH = QBrush(QColor(231, 29, 14, 60))


class CatPhanMainWindow(QAToolsWindow):

    def __init__(self, initData: dict = None):
        super().__init__(initData)

        self.window_title = "CatPhan Analysis ‒ PyBeam QA"
        self.setWindowTitle(self.window_title)

        self.add_new_worksheet()

        # Bound at click time, so the actions act on the tab that is current then.
        self.ui.menuFile.addAction("Add CT Series (.zip)...", lambda: self.ui.tabWidget.currentWidget().add_files())
        self.ui.menuFile.addAction("Add CT Series (Folder)...", lambda: self.ui.tabWidget.currentWidget().add_folder())
        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction("Add New Worksheet", self.add_new_worksheet)

    def add_new_worksheet(self, worksheet_name: str = None, enable_icon: bool = True):
        if worksheet_name is None:
            self.untitled_counter = self.untitled_counter + 1
            worksheet_name = f"CatPhan (Untitled-{self.untitled_counter})"

        return super().add_new_worksheet(QCatPhanWorksheet(), worksheet_name, enable_icon)


class QCatPhanWorksheet(QWidget):

    analysis_info_signal = Signal(dict)

    def __init__(self):
        super().__init__()

        self.ui = Ui_QCatPhanWorksheet()
        self.ui.setupUi(self)

        self.series_icon = QIcon()
        self.series_icon.addFile(u":/colorIcons/icons/picture.png", QSize(), QIcon.Normal, QIcon.Off)

        # results area: summary form, HU table, checks, analysed image
        self.form_layout = QFormLayout()
        self.form_layout.setHorizontalSpacing(40)
        self.ui.analysisInfoVL.addLayout(self.form_layout)

        self.hu_table = QTableWidget(0, 5)
        self.hu_table.setHorizontalHeaderLabels(["Material", "Nominal (HU)", "Measured (HU)", "Difference (HU)", "Pass"])
        self.hu_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.hu_table.verticalHeader().setVisible(False)
        self.hu_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.hu_table.hide()
        self.ui.analysisInfoVL.addWidget(self.hu_table)

        self.checks_layout = QFormLayout()
        self.checks_layout.setHorizontalSpacing(40)
        self.ui.analysisInfoVL.addLayout(self.checks_layout)

        self.analyzed_image_label = QLabel()
        self.analyzed_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.analyzed_image_label.hide()
        self.ui.analysisImageVL.addWidget(self.analyzed_image_label)

        self.analysis_progress_bar = QProgressBar()
        self.analysis_progress_bar.setRange(0, 0)
        self.analysis_progress_bar.setTextVisible(False)
        self.analysis_progress_bar.setMaximumSize(300, 10)
        self.analysis_progress_bar.setMinimumSize(300, 10)
        self.analysis_progress_bar.hide()

        self.analysis_message_label = QLabel("Analysis in progress")
        self.analysis_message_label.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred))
        self.analysis_message_label.hide()

        self.progress_vl = QVBoxLayout()
        self.progress_vl.setSpacing(10)
        self.progress_vl.addWidget(self.analysis_progress_bar, 0, Qt.AlignHCenter)
        self.progress_vl.addWidget(self.analysis_message_label, 0, Qt.AlignHCenter)
        self.ui.analysisInfoVL.addLayout(self.progress_vl)

        # "Add CT series" offers a .zip or a folder
        self.add_menu = QMenu(self)
        self.add_menu.addAction("Zip file(s) of a CT series...", self.add_files)
        self.add_menu.addAction("Folder of DICOM files...", self.add_folder)
        self.ui.addImgBtn.setMenu(self.add_menu)

        # context menu for the series list
        self.list_contextmenu = QMenu()
        self.list_contextmenu.addAction("Show Containing Folder", self.open_file_folder)
        self.remove_file_action = self.list_contextmenu.addAction("Remove from List", self.remove_file)
        self.remove_all_files_action = self.list_contextmenu.addAction("Remove All", self.remove_all_files)
        self.ui.imageListWidget.installEventFilter(self)

        self.ui.genReportBtn.setEnabled(False)
        self.ui.imageListWidget.itemChanged.connect(self.update_selection)
        self.ui.analyzeBtn.clicked.connect(self.start_analysis)
        self.ui.genReportBtn.clicked.connect(self.generate_report)

        # state (the QAToolsWindow contract: analysis_info_signal, analysis_state, analysis_message)
        self.analysis_state = AnalysisInfoLabel.IDLE
        self.analysis_message = None
        self.analysis_in_progress = False
        self.analysis_data = None
        self.selected_series = None
        self._outcome = None
        self.qthread = None

        # report dialog defaults, kept per worksheet as the other tools do
        self.report_author = ""
        self.report_institution = ""
        self.report_date = QDate.currentDate()
        self.save_comment = ""

        self.setup_config()
        self.update_selection()
        self.set_analysis_outcome()

    # ------------------------------------------------------------------ configuration
    def setup_config(self):
        self.ui.phantomCB.addItems(list(PHANTOMS))
        self.ui.phantomCB.setCurrentText(DEFAULT_PHANTOM)
        self.ui.contrastMethodCB.addItems(CONTRAST_METHODS)
        self.ui.contrastMethodCB.setCurrentText(DEFAULT_PARAMETERS["contrast_method"])

    def analysis_parameters(self) -> dict:
        """The analysis settings exactly as the user set them, in pylinac's terms."""
        return dict(hu_tolerance=self.ui.huToleranceDSB.value(),
                    scaling_tolerance=self.ui.scalingToleranceDSB.value(),
                    thickness_tolerance=self.ui.thicknessToleranceDSB.value(),
                    low_contrast_tolerance=self.ui.lowContrastToleranceSB.value(),
                    cnr_threshold=self.ui.cnrThresholdDSB.value(),
                    contrast_method=self.ui.contrastMethodCB.currentText(),
                    visibility_threshold=self.ui.visibilityThresholdDSB.value())

    def origin_slice(self) -> int | None:
        value = self.ui.originSliceSB.value()
        return None if value < 0 else value

    # ------------------------------------------------------------------ the series list
    def add_files(self, files: tuple | list | None = None):
        """Add CT series given as .zip files. With no argument, ask with a file dialog."""
        if not files:
            files, _ = QFileDialog.getOpenFileNames(self, "Select CT Series (.zip)", "", "CT series (*.zip)")
        for file in files or []:
            self._add_series(Path(file))

    def add_folder(self, folder: str | None = None):
        """Add a CT series given as a folder of DICOM files. With no argument, ask with a folder dialog."""
        if not folder:
            folder = QFileDialog.getExistingDirectory(self, "Select a Folder of CT DICOM Files")
        if folder:
            self._add_series(Path(folder))

    def _add_series(self, path: Path):
        item = QListWidgetItem(self.ui.imageListWidget)
        item.setText(path.name + ("/" if path.is_dir() else ""))
        item.setToolTip(str(path))
        item.setIcon(self.series_icon)
        item.setCheckState(Qt.Unchecked)
        item.setData(Qt.UserRole, {"file_path": str(path), "analysis_data": None})

    def update_selection(self):
        checked = [self.ui.imageListWidget.item(i) for i in range(self.ui.imageListWidget.count())
                   if self.ui.imageListWidget.item(i).checkState() == Qt.CheckState.Checked]
        self.selected_series = checked[0].data(Qt.UserRole)["file_path"] if checked else None
        self.ui.analyzeBtn.setEnabled(bool(checked) and not self.analysis_in_progress)

        if len(checked) > 1 and not self.analysis_in_progress:
            self.analysis_message_label.setText(f"One series is analysed at a time: {checked[0].text()}")
            self.analysis_message_label.show()
        elif not self.analysis_in_progress:
            self.analysis_message_label.hide()

    def remove_file(self):
        self.ui.imageListWidget.takeItem(self.ui.imageListWidget.currentRow())
        self.update_selection()

    def remove_all_files(self):
        self.ui.imageListWidget.clear()
        self.update_selection()

    def open_file_folder(self):
        item = self.ui.imageListWidget.currentItem()
        path = Path(item.data(Qt.UserRole)["file_path"])
        folder = str((path if path.is_dir() else path.parent).resolve())
        if platform.system() == "Windows":
            subprocess.Popen(["explorer", folder])
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    def eventFilter(self, source, event: QEvent):
        if event.type() == QEvent.ContextMenu and source is self.ui.imageListWidget:
            pos = self.ui.imageListWidget.mapFromGlobal(event.globalPos())
            if isinstance(self.ui.imageListWidget.itemAt(pos), QListWidgetItem):
                self.remove_file_action.setEnabled(not self.analysis_in_progress)
                self.remove_all_files_action.setEnabled(not self.analysis_in_progress)
                self.list_contextmenu.exec(event.globalPos())
        return super().eventFilter(source, event)

    # ------------------------------------------------------------------ analysis
    def _set_state(self, state: int, message: str | None = None):
        self.analysis_state = state
        self.analysis_message = message
        self.analysis_info_signal.emit({"state": state, "message": message})

    def start_analysis(self):
        if not self.selected_series:
            return

        self.analysis_in_progress = True
        self.analysis_data = None
        self.clear_results()
        self.set_analysis_outcome()

        self.ui.addImgBtn.setEnabled(False)
        self.ui.genReportBtn.setEnabled(False)
        self.ui.analyzeBtn.setEnabled(False)
        self.ui.analyzeBtn.setText("Analysis in progress...")
        self.analysis_message_label.setText("Starting analysis...")
        self.analysis_progress_bar.show()
        self.analysis_message_label.show()
        self._set_state(AnalysisInfoLabel.IN_PROGRESS)

        # Only stored by the worker: loading and analysis happen on its thread, inside its try.
        self.worker = QCatPhanWorker(self.selected_series, self.ui.phantomCB.currentText(),
                                     self.analysis_parameters(), self.origin_slice())
        self._outcome = None   # (state, message), set by the result or failure slot, published when the thread ends
        self.qthread = QThread()
        self.worker.moveToThread(self.qthread)
        self.worker.analysis_progress.connect(self.update_progress)
        self.worker.analysis_failed.connect(self.show_analysis_failure)
        self.worker.analysis_results_ready.connect(self.show_analysis_results)
        self.worker.thread_finished.connect(self.qthread.quit)
        self.worker.thread_finished.connect(self.worker.deleteLater)
        self.qthread.started.connect(self.worker.analyze)
        self.qthread.finished.connect(self.analysis_thread_finished)
        self.qthread.finished.connect(self.qthread.deleteLater)
        self.qthread.start()

    @Slot()
    def analysis_thread_finished(self):
        """Publish COMPLETE/FAILED only once the worker thread has really ended, so nothing that reacts to the
        state (closing the window, a test finishing) can destroy a QThread that is still running."""
        self.qthread = None
        state, message = self._outcome or (AnalysisInfoLabel.FAILED, "The analysis ended without a result")
        self.analysis_in_progress = False
        self.ui.analyzeBtn.setText("Analyze CT series")
        self.ui.addImgBtn.setEnabled(True)
        self.analysis_progress_bar.hide()
        self.analysis_message_label.hide()
        self.update_selection()
        self.set_analysis_outcome()
        self._set_state(state, message)

    @Slot(str)
    def update_progress(self, message: str):
        self.analysis_message_label.setText(message)

    @Slot(str)
    def show_analysis_failure(self, error_message: str = "Unknown Error"):
        self._outcome = (AnalysisInfoLabel.FAILED, error_message)

        self.error_dialog = MessageDialog()
        self.error_dialog.set_icon(MessageDialog.CRITICAL_ICON)
        self.error_dialog.set_title("Analysis Error")
        self.error_dialog.set_header_text("The CatPhan analysis failed")
        self.error_dialog.set_info_text(error_message)
        self.error_dialog.set_standard_buttons(QDialogButtonBox.StandardButton.Ok)
        self.error_dialog.exec()

    @Slot(dict)
    def show_analysis_results(self, data: dict):
        self.analysis_data = data
        result: CatPhanResult = data["result"]
        self.ui.genReportBtn.setEnabled(True)

        self.add_summary_row("Phantom:", f"CatPhan {result.phantom_model}")
        self.add_summary_row("Phantom roll:", f"{result.roll_deg:.2f}°")
        self.add_summary_row("Origin slice:", f"{result.origin_slice} (of {result.num_images} images)")
        self.add_summary_row("Uniformity index:", f"{result.uniformity_index:.2f}  "
                                                  f"(integral non-uniformity {result.integral_non_uniformity:.4f})")
        self.add_summary_row("Geometry:", f"mean node distance {result.geometry_avg_line_distance_mm:.2f} mm "
                                          f"(nominal 50 mm, tolerance ±{self.ui.scalingToleranceDSB.value():g} mm)")
        self.add_summary_row("Slice thickness:", f"{result.slice_thickness_mm:.2f} mm")
        mtf = ", ".join(f"{p} %: " + ("n/a" if result.mtf(p) is None else f"{result.mtf(p):.3f}") for p in (50, 30, 10))
        self.add_summary_row("MTF (lp/mm):", mtf)
        if result.low_contrast_available:
            self.add_summary_row("Low contrast:", f"{result.low_contrast_rois_seen} ROI(s) seen, "
                                                  f"{result.low_contrast_required} required")
        else:
            self.add_summary_row("Low contrast:", "not measured (no CTP515 module on this phantom)")
        self.add_summary_row("pylinac:", data.get("pylinac_version", result.pylinac_version))

        self.hu_table.setRowCount(len(result.hu_materials))
        for row, m in enumerate(result.hu_materials):
            cells = [m.name, f"{m.nominal_hu:.0f}", f"{m.measured_hu:.1f}", f"{m.difference_hu:+.1f}",
                     "PASS" if m.passed else "FAIL"]
            for col, text in enumerate(cells):
                cell = QTableWidgetItem(text)
                if not m.passed:
                    cell.setBackground(FAIL_BRUSH)
                self.hu_table.setItem(row, col, cell)
        self.hu_table.resizeRowsToContents()
        rows_height = sum(self.hu_table.rowHeight(r) for r in range(self.hu_table.rowCount()))
        self.hu_table.setFixedHeight(self.hu_table.horizontalHeader().height() + rows_height + 4)  # show every material
        self.hu_table.show()

        for check in result.checks:
            self.checks_layout.addRow(f"{check.name}:", QLabel(f"{'PASS' if check.passed else 'FAIL'} — {check.detail}"))

        pixmap = QPixmap()
        pixmap.loadFromData(data["analyzed_image_png"])
        self.analyzed_image_label.setPixmap(pixmap.scaledToWidth(min(900, pixmap.width()),
                                                                 Qt.TransformationMode.SmoothTransformation))
        self.analyzed_image_label.show()
        self.ui.image_vl_spacer.changeSize(0, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._outcome = (AnalysisInfoLabel.COMPLETE, None)

    def add_summary_row(self, label: str, value: str):
        self.form_layout.addRow(label, QLabel(value))

    def clear_results(self):
        for layout in (self.form_layout, self.checks_layout):
            for row in reversed(range(layout.rowCount())):
                layout.removeRow(row)
        self.hu_table.setRowCount(0)
        self.hu_table.hide()
        self.analyzed_image_label.clear()
        self.analyzed_image_label.hide()
        self.ui.image_vl_spacer.changeSize(0, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

    def set_analysis_outcome(self):
        """Shows the result's own decision (core/results/catphan.py); it is not re-decided here."""
        result = self.analysis_data["result"] if self.analysis_data else None
        if result is None or self.analysis_in_progress:
            self.ui.outcomeLE.clear()
            self.ui.outcomeLE.setToolTip("")
            self.ui.outcomeLE.setStyleSheet(NEUTRAL_STYLE)
        elif result.passed:
            self.ui.outcomeLE.setText("PASS")
            self.ui.outcomeLE.setToolTip("All checks passed")
            self.ui.outcomeLE.setStyleSheet(PASS_STYLE)
        else:
            self.ui.outcomeLE.setText("FAIL")
            self.ui.outcomeLE.setToolTip("\n".join(f"{c.name}: {c.detail}" for c in result.failed_checks))
            self.ui.outcomeLE.setStyleSheet(FAIL_STYLE)

    # ------------------------------------------------------------------ report
    def write_report(self, path: str, author: str = "N/A", institution: str = "N/A", treatment_unit: str = "N/A",
                     analysis_date: str | None = None, comments: str = ""):
        """Write the PDF report for the current analysis (the dialog in generate_report collects these)."""
        report = CatPhanReport(filename=path, author=author, institution=institution,
                               treatment_unit_name=treatment_unit,
                               analysis_date=analysis_date or QDate.currentDate().toString("dd MMMM yyyy"),
                               report_status=self.ui.outcomeLE.text(), comments=comments,
                               analysis_data=self.analysis_data)
        report.save_report()

    def generate_report(self):
        physicist_name_le = QLineEdit(self.report_author)
        institution_name_le = QLineEdit(self.report_institution)
        treatment_unit_cb = QComboBox()
        treatment_unit_cb.setEditable(True)
        treatment_unit_cb.addItems([linac.name for linac in DeviceManager.device_list["linacs"]])
        analysis_date = QDateEdit()
        analysis_date.setCalendarPopup(True)
        analysis_date.setDisplayFormat("dd MMMM yyyy")
        analysis_date.setMaximumDate(QDate.currentDate())
        analysis_date.setDate(self.report_date)
        comments_te = QPlainTextEdit(self.save_comment)

        save_path_le = QLineEdit()
        save_path_le.setReadOnly(True)
        save_win_btn = QPushButton("Save to...")
        save_location_layout = QHBoxLayout()
        save_location_layout.addWidget(save_path_le)
        save_location_layout.addWidget(save_win_btn)

        show_report_checkbox = QCheckBox()
        show_report_layout = QHBoxLayout()
        show_report_layout.addWidget(QLabel("Open report:"))
        show_report_layout.addWidget(show_report_checkbox)

        details = QFormLayout()
        details.addRow("Physicist:", physicist_name_le)
        details.addRow("Treatment unit:", treatment_unit_cb)
        details.addRow("Institution:", institution_name_le)
        details.addRow("Save location:", save_location_layout)
        details.addRow("Analysis date:", analysis_date)
        details.addRow("Comments:", comments_te)
        details.addRow("", show_report_layout)
        details.addItem(QSpacerItem(1, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))

        buttons = QDialogButtonBox()
        save_button = buttons.addButton(QDialogButtonBox.StandardButton.Save)
        save_button.setEnabled(False)
        cancel_button = buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        save_path_le.textChanged.connect(lambda: save_button.setEnabled(bool(save_path_le.text())))

        layout = QVBoxLayout()
        layout.addLayout(details)
        layout.addWidget(buttons)
        dialog = QDialog()
        dialog.setWindowTitle("Generate CatPhan Report ‒ PyBeam QA")
        dialog.setLayout(layout)
        cancel_button.clicked.connect(dialog.reject)
        save_button.clicked.connect(dialog.accept)
        save_win_btn.clicked.connect(lambda: save_path_le.setText(worksheet_save_report(self)))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.report_author = physicist_name_le.text()
            self.report_institution = institution_name_le.text()
            self.save_comment = comments_te.toPlainText()
            self.report_date = analysis_date.date()

            self.write_report(save_path_le.text(),
                              author=physicist_name_le.text() or "N/A",
                              institution=institution_name_le.text() or "N/A",
                              treatment_unit=treatment_unit_cb.currentText() or "N/A",
                              analysis_date=self.report_date.toString("dd MMMM yyyy"),
                              comments=comments_te.toPlainText())

            if show_report_checkbox.isChecked():
                webbrowser.open(save_path_le.text())
