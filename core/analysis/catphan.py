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

from PySide6.QtCore import Signal, Slot, QObject

from pylinac.ct import (CatPhan503, CatPhan504, CatPhan600, CatPhan604, 
                       CatPhanBase, CatphanResult)
from pylinac.core.geometry import Circle, Rectangle

import io
from matplotlib.patches import Rectangle as MatplotRect
from pathlib import Path
from typing import BinaryIO, Dict, List, Tuple, Union, Optional

import numpy as np
import pyqtgraph as pg
import enum
import traceback

class CATPHAN_MODEL(enum.Enum):
    CATPHAN503 = "CatPhan 503"
    CATPHAN504 = "CatPhan 504"
    CATPHAN600 = "CatPhan 600"
    CATPHAN604 = "CatPhan 604"

class QCatPhan():
    """
    A class that wraps PyLinac's CatPhan classes and provides plotting functionality
    using pyqtgraph for the PyBeam-QA application.
    """

    def __init__(self, phantom: CatPhanBase):
        self._phantom = phantom

        # Create plot widgets
        self.analyzed_image_plot_widget = pg.GraphicsLayoutWidget()
        self.hu_linearity_plot_widget = pg.GraphicsLayoutWidget()
        self.uniformity_plot_widget = pg.GraphicsLayoutWidget()
        self.mtf_plot_widget = pg.GraphicsLayoutWidget()
        self.low_contrast_plot_widget = pg.GraphicsLayoutWidget()

    def qplot_analyzed_image(self):
        """Plot the analyzed CatPhan image using pyqtgraph."""
        self.analyzed_image_plot_widget.clear()

        # Prepare the image plot widget
        g_layout = self.analyzed_image_plot_widget.ci.layout

        # Add the image plot 
        self.image_plot = self.analyzed_image_plot_widget.addPlot(
            name="Image_Plot",
            title="<b>Analyzed image</b>",
            row=0,
            col=0
        )
        self.image_plot.setLabel("left", "Pixel")
        self.image_plot.setLabel("bottom", "Pixel")
        self.image_plot.invertY(True)
        self.image_plot.addLegend(
            size=(50, 50), 
            pen=pg.mkPen(13, 27, 42),
            labelTextColor='w', 
            brush=pg.mkBrush((27, 38, 59, 200))
        )
        
        # Get the HU module slice
        hu_slice = self._phantom.ctp404.slice_num
        
        # Plot the image
        self.image_plot.addItem(pg.ImageItem(self._phantom.dicom_stack[hu_slice].array))
        
        # Plot phantom outline if available
        if hasattr(self._phantom, 'phantom_outline_object') and self._phantom.phantom_outline_object is not None:
            outline_obj, settings = self._phantom._create_phantom_outline_object()

            if isinstance(outline_obj, Circle):
                outline_x_data = outline_obj.radius*np.cos(np.linspace(0, 2*np.pi, 500)) + outline_obj.center.x
                outline_y_data = outline_obj.radius*np.sin(np.linspace(0, 2*np.pi, 500)) + outline_obj.center.y

                self.image_plot.plot(
                    outline_x_data, 
                    outline_y_data, 
                    pen=pg.mkPen((252, 163, 17), width=2.5),
                    name="Phantom outline"
                )
            
            elif isinstance(outline_obj, Rectangle):
                rect = MatplotRect(
                    (outline_obj.bl_corner.x, outline_obj.bl_corner.y),
                    width=outline_obj.width,
                    height=outline_obj.height,
                    angle=settings.get("angle", 0)
                )
                
                data = rect.get_verts()
                
                self.image_plot.plot(
                    data, 
                    pen=pg.mkPen((252, 163, 17), width=2.5),
                    name="Phantom Outline"
                )
        
        # Plot phantom center
        self.image_plot.plot(
            [self._phantom.phantom_center.x], 
            [self._phantom.phantom_center.y],
            symbolBrush=(206, 255, 26), 
            symbol="o", 
            symbolSize=14,
            symbolPen=pg.mkPen((0, 0, 0), width=2.5), 
            name="Phantom Center",
            pen=pg.mkPen((0, 0, 0), width=2.5)
        )

    def qplot_hu_linearity(self):
        """Plot the HU linearity results using pyqtgraph."""
        self.hu_linearity_plot_widget.clear()
        
        # Prepare the plot widget
        g_layout = self.hu_linearity_plot_widget.ci.layout
        
        # Add the HU linearity plot
        self.hu_plot = self.hu_linearity_plot_widget.addPlot(
            name="HU_Linearity_Plot",
            title="<b>HU Linearity</b>",
            row=0,
            col=0
        )
        self.hu_plot.setLabel("left", "Measured HU")
        self.hu_plot.setLabel("bottom", "Expected HU")
        
        # Get HU data
        results = self._phantom.results_data()
        hu_data = results.ctp404
        
        # Extract expected and measured HU values
        expected_hu = []
        measured_hu = []
        roi_names = []
        
        for roi_name, roi_data in hu_data.rois.items():
            if roi_name not in ['Air', 'PMP', 'LDPE', 'Polystyrene', 'Acrylic', 'Delrin', 'Teflon']:
                continue
                
            expected_hu.append(roi_data.nominal_val)
            measured_hu.append(roi_data.value)
            roi_names.append(roi_name)
        
        # Plot the data
        self.hu_plot.plot(
            expected_hu, 
            measured_hu, 
            symbolBrush=(183, 195, 243), 
            symbol="o", 
            symbolSize=12,
            symbolPen=None,
            pen=pg.mkPen((183, 195, 243), width=2.0)
        )
        
        # Add identity line (y=x)
        min_hu = min(min(expected_hu), min(measured_hu))
        max_hu = max(max(expected_hu), max(measured_hu))
        self.hu_plot.plot(
            [min_hu, max_hu], 
            [min_hu, max_hu], 
            pen=pg.mkPen('r', width=1.5, style=pg.QtCore.Qt.DashLine)
        )
        
        # Add ROI labels
        for i, name in enumerate(roi_names):
            text = pg.TextItem(text=name, color="w", anchor=(0.5, 0.5))
            text.setPos(expected_hu[i], measured_hu[i])
            self.hu_plot.addItem(text)

    def qplot_uniformity(self):
        """Plot the uniformity results using pyqtgraph."""
        self.uniformity_plot_widget.clear()
        
        # Prepare the plot widget
        g_layout = self.uniformity_plot_widget.ci.layout
        
        # Add the uniformity plot
        self.unif_plot = self.uniformity_plot_widget.addPlot(
            name="Uniformity_Plot",
            title="<b>Uniformity</b>",
            row=0,
            col=0
        )
        self.unif_plot.setLabel("left", "HU")
        self.unif_plot.setLabel("bottom", "ROI Position")
        
        # Get uniformity data
        results = self._phantom.results_data()
        unif_data = results.ctp486
        
        # Extract ROI values
        roi_positions = ['Center', 'Top', 'Right', 'Bottom', 'Left']
        roi_values = [
            unif_data.rois.center.value,
            unif_data.rois.top.value,
            unif_data.rois.right.value,
            unif_data.rois.bottom.value,
            unif_data.rois.left.value
        ]
        
        # Plot the data
        x_positions = list(range(len(roi_positions)))
        self.unif_plot.plot(
            x_positions, 
            roi_values, 
            symbolBrush=(183, 195, 243), 
            symbol="o", 
            symbolSize=12,
            symbolPen=None,
            pen=pg.mkPen((183, 195, 243), width=2.0)
        )
        
        # Add ROI labels
        for i, pos in enumerate(roi_positions):
            text = pg.TextItem(text=pos, color="w", anchor=(0.5, 0.5))
            text.setPos(i, roi_values[i])
            self.unif_plot.addItem(text)
            
        # Set x-axis ticks
        self.unif_plot.getAxis('bottom').setTicks([[(i, pos) for i, pos in enumerate(roi_positions)]])

    def qplot_mtf(self):
        """Plot the MTF results using pyqtgraph."""
        self.mtf_plot_widget.clear()
        
        # Prepare the plot widget
        g_layout = self.mtf_plot_widget.ci.layout
        
        # Add the MTF plot
        self.mtf_plot = self.mtf_plot_widget.addPlot(
            name="MTF_Plot",
            title="<b>Modulation Transfer Function (MTF)</b>",
            row=0,
            col=0
        )
        self.mtf_plot.setLabel("left", "Relative MTF")
        self.mtf_plot.setLabel("bottom", "Line pairs / mm")
        
        # Get MTF data
        results = self._phantom.results_data()
        
        # Check if CTP528 module exists (MTF data)
        if hasattr(results, 'ctp528'):
            mtf_data = results.ctp528
            
            # Extract MTF values
            lp_mm = list(mtf_data.mtf.spacings)
            mtf_values = list(mtf_data.mtf.norm_mtfs.values())
            
            # Plot the data
            self.mtf_plot.plot(
                lp_mm, 
                mtf_values, 
                symbolBrush=(183, 195, 243), 
                symbol="o", 
                symbolSize=8,
                symbolPen=None,
                pen=pg.mkPen((183, 195, 243), width=2.0)
            )
            
            # Add reference lines for 50%, 30%, 10% MTF
            for mtf_level, color in [(0.5, 'r'), (0.3, 'g'), (0.1, 'b')]:
                self.mtf_plot.addItem(
                    pg.InfiniteLine(
                        pos=mtf_level, 
                        pen=pg.mkPen(color, width=1.5, style=pg.QtCore.Qt.DashLine),
                        movable=False, 
                        angle=0,
                        label=f"{int(mtf_level*100)}% MTF"
                    )
                )
        else:
            # Add text indicating no MTF data available
            text = pg.TextItem(
                text="No MTF data available for this phantom", 
                color="w", 
                anchor=(0.5, 0.5)
            )
            text.setPos(0.5, 0.5)
            self.mtf_plot.addItem(text)

    def qplot_low_contrast(self):
        """Plot the low contrast results using pyqtgraph."""
        self.low_contrast_plot_widget.clear()
        
        # Prepare the plot widget
        g_layout = self.low_contrast_plot_widget.ci.layout
        
        # Add the low contrast plot
        self.lc_plot = self.low_contrast_plot_widget.addPlot(
            name="Low_Contrast_Plot",
            title="<b>Low Contrast Detectability</b>",
            row=0,
            col=0
        )
        self.lc_plot.setLabel("left", "Contrast")
        self.lc_plot.setLabel("bottom", "ROI #")
        
        # Get low contrast data
        results = self._phantom.results_data()
        
        # Check if CTP515 module exists (low contrast data)
        if hasattr(results, 'ctp515'):
            lc_data = results.ctp515
            
            # Extract contrast values
            roi_nums = []
            contrast_values = []
            
            for i, (roi_name, roi_data) in enumerate(lc_data.rois.items()):
                roi_nums.append(i+1)
                contrast_values.append(roi_data.contrast)
            
            # Plot the data
            self.lc_plot.plot(
                roi_nums, 
                contrast_values, 
                symbolBrush=(183, 195, 243), 
                symbol="o", 
                symbolSize=12,
                symbolPen=None,
                pen=pg.mkPen((183, 195, 243), width=2.0)
            )
            
            # Add threshold line if available
            if hasattr(self._phantom, '_low_contrast_threshold'):
                self.lc_plot.addItem(
                    pg.InfiniteLine(
                        pos=self._phantom._low_contrast_threshold, 
                        pen='r',
                        movable=False, 
                        angle=0,
                        label="Threshold"
                    )
                )
        else:
            # Add text indicating no low contrast data available
            text = pg.TextItem(
                text="No low contrast data available for this phantom", 
                color="w", 
                anchor=(0.5, 0.5)
            )
            text.setPos(0.5, 0.5)
            self.lc_plot.addItem(text)

    def get_publishable_plots(self) -> List[io.BytesIO]:
        """
        Generate high-quality PDF plots for reporting.
        
        Returns:
            List of BytesIO objects containing PDF plots.
        """
        figs, names = self._phantom.plot_analyzed_image(
            show=False, split_plots=True, figsize=(4.5, 4.5)
        )

        filenames = [io.BytesIO() for _ in names]
        for fig, name in zip(figs, filenames):
            fig.savefig(name, format="pdf", pad_inches=0.0, bbox_inches='tight', dpi=200)
        
        return filenames

class QCatPhanWorker(QObject):
    """
    Worker class for CatPhan analysis that runs in a separate thread.
    """
    
    analysis_progress = Signal(str)
    analysis_results_ready = Signal(dict)
    thread_finished = Signal()
    analysis_failed = Signal(str)
    
    def __init__(self, 
                 phantom_model: str,
                 filepath: Union[str, BinaryIO, Path, List[str], List[Path], List[BinaryIO]],
                 memory_efficient_mode: bool = False,
                 hu_tolerance: Optional[float] = None,
                 scaling_tolerance: Optional[float] = None,
                 low_contrast_threshold: Optional[float] = None,
                 high_contrast_threshold: Optional[float] = None,
                 thickness_tolerance: Optional[float] = None,
                 zip_after: bool = False,
                 clear_borders: bool = True,
                 override_values: Optional[Dict] = None):
        """
        Initialize the CatPhan worker.
        
        Args:
            phantom_model: The CatPhan model to use (503, 504, 600, 604)
            filepath: Path to the DICOM files or folder
            memory_efficient_mode: Whether to use memory-efficient mode
            hu_tolerance: Tolerance for HU linearity
            scaling_tolerance: Tolerance for image scaling
            low_contrast_threshold: Threshold for low contrast detectability
            high_contrast_threshold: Threshold for high contrast resolution
            thickness_tolerance: Tolerance for slice thickness
            zip_after: Whether to zip the DICOM files after analysis
            clear_borders: Whether to clear borders in the analysis
            override_values: Dictionary of values to override in the CatPhan analysis
        """
        super().__init__()
        
        self._phantom_model = phantom_model
        self._filepath = filepath
        self._memory_efficient_mode = memory_efficient_mode
        self._hu_tolerance = hu_tolerance
        self._scaling_tolerance = scaling_tolerance
        self._low_contrast_threshold = low_contrast_threshold
        self._high_contrast_threshold = high_contrast_threshold
        self._thickness_tolerance = thickness_tolerance
        self._zip_after = zip_after
        self._clear_borders = clear_borders
        self._override_values = override_values or {}
        
        # Initialize the phantom based on the model
        if phantom_model == CATPHAN_MODEL.CATPHAN503.value:
            self._phantom = CatPhan503(filepath, memory_efficient_mode=memory_efficient_mode)
            self._phantom.common_name = CATPHAN_MODEL.CATPHAN503.value
            
        elif phantom_model == CATPHAN_MODEL.CATPHAN504.value:
            self._phantom = CatPhan504(filepath, memory_efficient_mode=memory_efficient_mode)
            self._phantom.common_name = CATPHAN_MODEL.CATPHAN504.value
            
        elif phantom_model == CATPHAN_MODEL.CATPHAN600.value:
            self._phantom = CatPhan600(filepath, memory_efficient_mode=memory_efficient_mode)
            self._phantom.common_name = CATPHAN_MODEL.CATPHAN600.value
            
        elif phantom_model == CATPHAN_MODEL.CATPHAN604.value:
            self._phantom = CatPhan604(filepath, memory_efficient_mode=memory_efficient_mode)
            self._phantom.common_name = CATPHAN_MODEL.CATPHAN604.value
            
        else:
            raise ValueError(f"Invalid phantom model: {phantom_model}")
        
        self._catphan = QCatPhan(self._phantom)
    
    def analyze(self):
        """
        Perform the CatPhan analysis.
        """
        try:
            self.analysis_progress.emit("Analyzing CatPhan images...")
            
            # Apply any override values
            for key, value in self._override_values.items():
                if hasattr(self._phantom, key):
                    setattr(self._phantom, key, value)
            
            # Perform the analysis
            self._phantom.analyze(
                hu_tolerance=self._hu_tolerance,
                scaling_tolerance=self._scaling_tolerance,
                low_contrast_threshold=self._low_contrast_threshold,
                thickness_tolerance=self._thickness_tolerance,
                zip_after=self._zip_after,
                clear_borders=self._clear_borders
            )
            
            # Get the results
            results_data = self._phantom.results_data()
            
            # Prepare summary text
            summary_text = [
                ["Phantom Model:", results_data.catphan_model],
                ["Phantom Roll:", f"{results_data.catphan_roll_deg:.2f}°"],
                ["Origin Slice:", str(results_data.origin_slice)]
            ]
            
            # Add HU linearity results
            if hasattr(results_data, 'ctp404'):
                hu_data = results_data.ctp404
                summary_text.append(["HU Linearity Passed:", str(hu_data.passed)])
                summary_text.append(["HU Linearity Max Error:", f"{hu_data.max_difference:.2f} HU"])
                summary_text.append(["Scaling Passed:", str(hu_data.mm_per_pixel_passed)])
                summary_text.append(["Measured Pixel Size:", f"{hu_data.mm_per_pixel:.4f} mm"])
            
            # Add uniformity results
            if hasattr(results_data, 'ctp486'):
                unif_data = results_data.ctp486
                summary_text.append(["Uniformity Passed:", str(unif_data.passed)])
                summary_text.append(["Uniformity Max Error:", f"{unif_data.max_deviation:.2f} HU"])
                summary_text.append(["Uniformity Integral:", f"{unif_data.integral_non_uniformity:.2f}"])
            
            # Add MTF results
            if hasattr(results_data, 'ctp528'):
                mtf_data = results_data.ctp528
                summary_text.append(["MTF 50% (lp/mm):", f"{mtf_data.mtf.relative_resolution(50):.2f}"])
                summary_text.append(["MTF 30% (lp/mm):", f"{mtf_data.mtf.relative_resolution(30):.2f}"])
                summary_text.append(["MTF 10% (lp/mm):", f"{mtf_data.mtf.relative_resolution(10):.2f}"])
            
            # Add low contrast results
            if hasattr(results_data, 'ctp515'):
                lc_data = results_data.ctp515
                summary_text.append(["Low Contrast ROIs Visible:", str(lc_data.rois_visible)])
                summary_text.append(["Low Contrast Min Size Visible:", f"{lc_data.min_size_visible:.2f} mm"])
                summary_text.append(["Low Contrast Min Contrast Visible:", f"{lc_data.min_contrast_visible:.4f}"])
            
            # Create plots
            self._catphan.qplot_analyzed_image()
            self._catphan.qplot_hu_linearity()
            self._catphan.qplot_uniformity()
            self._catphan.qplot_mtf()
            self._catphan.qplot_low_contrast()
            
            # Prepare results
            results = {
                "summary_text": summary_text,
                "catphan_obj": self._catphan,
                "results_data": results_data
            }
            
            self.analysis_results_ready.emit(results)
            self.thread_finished.emit()
            
        except Exception as err:
            self.analysis_failed.emit(traceback.format_exception_only(err)[-1])
            self.thread_finished.emit()
            
            raise err

