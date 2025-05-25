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

from PySide6.QtCore import Signal, Slot, QObject, Qt

from pylinac.ct import (CatPhan504, CatPhan503, CatPhan600, CatPhan604)
from pylinac.core.geometry import Circle, Rectangle

import io
from pathlib import Path
from typing import BinaryIO, Union, List, Dict

import numpy as np
import enum
import traceback

# Try to import pyqtgraph, but don't fail if it's not available
try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False

class PHANTOM(enum.Enum):
    CATPHAN_503 = "CatPhan 503"
    CATPHAN_504 = "CatPhan 504"
    CATPHAN_600 = "CatPhan 600"
    CATPHAN_604 = "CatPhan 604"

class QCTAnalysis():
    """
    A class for analyzing and displaying CT phantom images.
    This is a wrapper around pylinac.ct module.
    """
    def __init__(self, phantom):
        self._phantom = phantom
        if HAS_PYQTGRAPH:
            self.analyzed_image_plot_widget = pg.GraphicsLayoutWidget()
        else:
            self.analyzed_image_plot_widget = None

    def qplot_analyzed_image(self):
        """Plot the analyzed CT phantom images and results"""
        if not HAS_PYQTGRAPH or self.analyzed_image_plot_widget is None:
            return
            
        self.analyzed_image_plot_widget.clear()

        # Prepare the image plot widget
        g_layout = self.analyzed_image_plot_widget.ci.layout
        
        # Create a grid of plots for the different CT modules
        self.hu_linearity_plot = self.analyzed_image_plot_widget.addPlot(
            name="HU_Linearity_Plot",
            title="<b>HU Linearity</b>",
            row=0, col=0)
        self.hu_linearity_plot.setLabel('left', "Measured HU")
        self.hu_linearity_plot.setLabel('bottom', "Nominal HU")
        
        self.uniformity_plot = self.analyzed_image_plot_widget.addPlot(
            name="Uniformity_Plot",
            title="<b>HU Uniformity</b>",
            row=0, col=1)
        self.uniformity_plot.setLabel('left', "HU")
        self.uniformity_plot.setLabel('bottom', "ROI Position")
        
        self.mtf_plot = self.analyzed_image_plot_widget.addPlot(
            name="MTF_Plot",
            title="<b>Modulation Transfer Function</b>",
            row=1, col=0)
        self.mtf_plot.setLabel('left', "MTF")
        self.mtf_plot.setLabel('bottom', "Line pairs/mm")
        
        self.low_contrast_plot = self.analyzed_image_plot_widget.addPlot(
            name="Low_Contrast_Plot",
            title="<b>Low Contrast</b>",
            row=1, col=1)
        self.low_contrast_plot.setLabel('left', "Contrast")
        self.low_contrast_plot.setLabel('bottom', "ROI #")

        # HU Linearity plot
        # Check if module exists in the phantom
        if hasattr(self._phantom, 'ctp404'):
            # Plot HU linearity
            if hasattr(self._phantom.ctp404, 'rois'):
                x_data = []
                y_data = []
                for name, roi in self._phantom.ctp404.rois.items():
                    if name not in ['background', 'air']:
                        x_data.append(roi.nominal_val)
                        y_data.append(roi.pixel_value)
                
                # Add reference line (y=x)
                x_range = np.linspace(min(x_data), max(x_data), 100)
                self.hu_linearity_plot.plot(x_range, x_range, pen=pg.mkPen('r', width=1, style=Qt.DashLine), 
                                            name='Expected')
                
                # Add actual measurements
                self.hu_linearity_plot.plot(x_data, y_data, pen=None, symbol='o', symbolPen='g', 
                                            symbolBrush='g', symbolSize=8, name='Measured')

        # Uniformity plot
        if hasattr(self._phantom, 'ctp486'):
            if hasattr(self._phantom.ctp486, 'rois'):
                positions = []
                values = []
                for name, roi in self._phantom.ctp486.rois.items():
                    positions.append(name)
                    values.append(roi.pixel_value)
                
                # Bar graph for uniformity
                x_ticks = list(range(len(positions)))
                bar_width = 0.6
                bars = pg.BarGraphItem(x=x_ticks, height=values, width=bar_width, brush='b')
                self.uniformity_plot.addItem(bars)
                self.uniformity_plot.getAxis('bottom').setTicks([[(i, p) for i, p in enumerate(positions)]])

        # MTF plot
        if hasattr(self._phantom, 'ctp528'):
            if hasattr(self._phantom.ctp528, 'mtf'):
                mtf_data = self._phantom.ctp528.mtf.mtf
                lp_mm = self._phantom.ctp528.mtf.lp_mm
                
                self.mtf_plot.plot(lp_mm, mtf_data, pen=pg.mkPen('b', width=2))
                
                # Add reference lines at 50%, 10%
                for level, color in [(0.5, 'r'), (0.1, 'g')]:
                    self.mtf_plot.addLine(y=level, pen=pg.mkPen(color, width=1, style=Qt.DashLine))

        # Low contrast plot
        if hasattr(self._phantom, 'ctp515'):
            if hasattr(self._phantom.ctp515, 'rois'):
                contrasts = []
                roi_nums = []
                i = 0
                for name, roi in self._phantom.ctp515.rois.items():
                    if 'bg' not in name.lower():
                        contrasts.append(roi.contrast)
                        roi_nums.append(i)
                        i += 1
                
                self.low_contrast_plot.plot(roi_nums, contrasts, pen=None, symbol='o', 
                                            symbolPen='b', symbolBrush='b', symbolSize=8)

    def get_publishable_plots(self) -> List[io.BytesIO]:
        """
        Custom plot implementation to get smaller, high quality pdf images
        """
        plots = []
        
        # Generate module plots using matplotlib for reports
        # HU Linearity
        if hasattr(self._phantom, 'ctp404'):
            temp_buffer = io.BytesIO()
            self._phantom.ctp404.plot_linearity(figsize=(10, 6))
            import matplotlib.pyplot as plt
            plt.savefig(temp_buffer, format="pdf", dpi=150, bbox_inches='tight')
            plt.close()
            temp_buffer.seek(0)
            plots.append(temp_buffer)
        
        # Uniformity
        if hasattr(self._phantom, 'ctp486'):
            temp_buffer = io.BytesIO()
            fig, ax = plt.subplots(figsize=(10, 6))
            data = self._phantom.ctp486.results_data()
            
            # Create a bar chart of ROI values
            roi_names = list(self._phantom.ctp486.rois.keys())
            roi_values = [roi.pixel_value for roi in self._phantom.ctp486.rois.values()]
            
            ax.bar(roi_names, roi_values, color='b')
            ax.set_title('HU Uniformity')
            ax.set_xlabel('ROI Position')
            ax.set_ylabel('HU')
            
            plt.tight_layout()
            plt.savefig(temp_buffer, format="pdf", dpi=150, bbox_inches='tight')
            plt.close()
            temp_buffer.seek(0)
            plots.append(temp_buffer)
        
        # MTF
        if hasattr(self._phantom, 'ctp528'):
            temp_buffer = io.BytesIO()
            self._phantom.ctp528.plot_mtf(figsize=(10, 6))
            plt.savefig(temp_buffer, format="pdf", dpi=150, bbox_inches='tight')
            plt.close()
            temp_buffer.seek(0)
            plots.append(temp_buffer)
        
        # Low Contrast
        if hasattr(self._phantom, 'ctp515'):
            temp_buffer = io.BytesIO()
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Extract contrast values
            contrasts = []
            roi_labels = []
            for name, roi in self._phantom.ctp515.rois.items():
                if 'bg' not in name.lower():
                    contrasts.append(roi.contrast)
                    roi_labels.append(name)
            
            ax.bar(roi_labels, contrasts, color='g')
            ax.set_title('Low Contrast Detectability')
            ax.set_xlabel('ROI')
            ax.set_ylabel('Contrast')
            
            plt.tight_layout()
            plt.savefig(temp_buffer, format="pdf", dpi=150, bbox_inches='tight')
            plt.close()
            temp_buffer.seek(0)
            plots.append(temp_buffer)
            
        return plots

class QCTAnalysisWorker(QObject):
    """
    Worker class to analyze CT images in a separate thread.
    """
    analysis_progress = Signal(str)
    analysis_results_ready = Signal(dict)
    thread_finished = Signal()
    analysis_failed = Signal(str)

    def __init__(self, path: str, phantom_type: PHANTOM = PHANTOM.CATPHAN_504):
        super().__init__()
        
        self._path = path
        self._phantom_type = phantom_type
        self._ct_analysis = None
        
    def analyze(self):
        """
        Perform analysis on a CT dataset.
        """
        try:
            self.analysis_progress.emit("Loading CT dataset...")
            
            # Load and analyze the CT dataset based on phantom type
            if self._phantom_type == PHANTOM.CATPHAN_503:
                self._phantom = CatPhan503.from_zip(self._path)
            elif self._phantom_type == PHANTOM.CATPHAN_504:
                self._phantom = CatPhan504.from_zip(self._path)
            elif self._phantom_type == PHANTOM.CATPHAN_600:
                self._phantom = CatPhan600.from_zip(self._path)
            elif self._phantom_type == PHANTOM.CATPHAN_604:
                self._phantom = CatPhan604.from_zip(self._path)
            else:
                # Default to CatPhan504
                self._phantom = CatPhan504.from_zip(self._path)
                
            self.analysis_progress.emit("Analyzing CT dataset...")
            
            # Analyze the phantom
            self._phantom.analyze()
            
            # Create QCTAnalysis object
            self._ct_analysis = QCTAnalysis(self._phantom)
            
            # Prepare summary text for display
            summary_text = []
            
            # Get the results data
            data = self._phantom.results_data()
            
            # Format the results for display
            summary_text.append(["Phantom Type:", f"{self._phantom_type.value}"])
            summary_text.append(["", ""])
            
            # HU Linearity
            if hasattr(data, 'hu_linearity'):
                summary_text.append(["HU Linearity:", ""])
                for material, values in data.hu_linearity.items():
                    if material != 'background':
                        summary_text.append([f"  {material}:", f"{values.value:.2f} HU (Expected: {values.nominal:.2f} HU)"])
            
            summary_text.append(["", ""])
            
            # Uniformity
            if hasattr(data, 'uniformity'):
                summary_text.append(["HU Uniformity:", ""])
                for position, value in data.uniformity.items():
                    summary_text.append([f"  {position}:", f"{value:.2f} HU"])
                
                if hasattr(data, 'uniformity_index'):
                    summary_text.append(["Uniformity Index:", f"{data.uniformity_index:.2f}"])
            
            summary_text.append(["", ""])
            
            # Spatial Resolution (MTF)
            if hasattr(data, 'mtf'):
                summary_text.append(["Spatial Resolution:", ""])
                for percent, lp_mm in data.mtf.items():
                    summary_text.append([f"  MTF {percent}%:", f"{lp_mm:.2f} lp/mm"])
            
            summary_text.append(["", ""])
            
            # Low contrast
            if hasattr(data, 'low_contrast'):
                summary_text.append(["Low Contrast:", ""])
                for i, contrast in enumerate(data.low_contrast.values()):
                    summary_text.append([f"  ROI {i+1}:", f"{contrast:.4f}"])
                
                if hasattr(data, 'low_contrast_visibility'):
                    summary_text.append(["Low Contrast Visibility:", f"{data.low_contrast_visibility:.4f}"])
            
            # Create results dict
            results = {
                "summary_text": summary_text,
                "ct_analysis_obj": self._ct_analysis
            }
            
            self.analysis_results_ready.emit(results)
            self.thread_finished.emit()
            
        except Exception as err:
            self.analysis_failed.emit(traceback.format_exception_only(err)[-1])
            self.thread_finished.emit()
            
            raise err