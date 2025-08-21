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

from reportlab.platypus import (SimpleDocTemplate, Paragraph, PageBreak, Spacer, Table,
                                Image, TopPadder, Flowable)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from datetime import datetime

import io
from pathlib import Path
from pdfrw import PdfReader, PdfDict

class PdfImage(Flowable):
    """
    Wrapper for Image flowable to handle BytesIO objects
    """
    def __init__(self, img_data, width=None, height=None):
        Flowable.__init__(self)
        self.img_data = img_data
        self.width = width
        self.height = height
        
    def wrap(self, availWidth, availHeight):
        return self.width, self.height
    
    def drawOn(self, canvas, x, y, _sW=0):
        if self.width and self.height:
            canvas.saveState()
            img = Image(self.img_data, self.width, self.height)
            img.drawOn(canvas, x, y - self.height)
            canvas.restoreState()

class BaseReport:
    """
    Base class for generating reports
    """
    def __init__(
        self, filename: str,
        report_name: str = "Base Report",
        author: str | None = None,
        institution: str | None = None,
        treatment_unit_name: str | None = None,
        analysis_date: str | None = None,
        analysis_summary: dict | None = None,
        summary_plots: list | None = None,
        comments: str | None = None
        ):
        
        self._filename = filename
        self._report_name = report_name
        self._author = author
        self._institution = institution
        self._treatment_unit_name = treatment_unit_name
        self._analysis_date = analysis_date
        self._analysis_summary = analysis_summary
        self._summary_plots = summary_plots
        self._comments = comments
        
        self._styles = getSampleStyleSheet()
        self._styles.add(self._styles["Normal"].clone("NormalCenter", alignment=TA_CENTER))
        self._styles.add(self._styles["Normal"].clone("NormalRight", alignment=TA_RIGHT))
        
    def add_metadata(self, canvas: Canvas, doc):
        """
        Add metadata to the PDF document
        """
        canvas.saveState()
        
        # Add header
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawCentredString(doc.width/2.0 + doc.leftMargin, doc.height + doc.topMargin - 0.5*cm, self._report_name)
        
        # Add footer
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(doc.width/2.0 + doc.leftMargin, doc.bottomMargin - 0.5*cm, f"Generated with PyBeam QA on {datetime.now().strftime('%d %B %Y, %H:%M:%S')}")
        
        # Add page number
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(doc.width + doc.leftMargin, doc.bottomMargin - 0.5*cm, f"Page {canvas.getPageNumber()}")
        
        canvas.restoreState()
        
    def set_user_details(self, doc_contents: list):
        """
        Add user details to the report
        """
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">User details:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts
        
        data = [["Physicist:", self._author],
                ["Institution:", self._institution],
                ["Treatment unit:", self._treatment_unit_name],
                ["Analysis date:", self._analysis_date]]
        
        table = Table(data, colWidths=[4.0*cm, 12.0*cm])
        table.setStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('ALIGN', (0,0), (0,-1), 'RIGHT')])
        
        doc_contents.append(table)
        
    def set_analysis_details(self, doc_contents: list):
        """
        Add analysis details to the report
        """
        doc_contents.append(Spacer(1, 16))
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">Analysis details:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts
        
        if self._analysis_summary is None:
            doc_contents.append(Paragraph("No analysis details available."))
            return
        
        data = []
        data.append(["Parameter", "Value"])
        
        for key, value in self._analysis_summary.items():
            data.append([key, value])
            
        table = Table(data, colWidths=[8.0*cm, 8.0*cm])
        table.setStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
                        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                        ('LINEABOVE', (0,0), (-1,0), 1, colors.black),
                        ('LINEABOVE', (0,1), (-1,1), 1, colors.black)])
        
        doc_contents.append(table)

    def set_plot_summary(self, doc_contents: list):
        #doc_contents.append(PageBreak())
        doc_contents.append(Spacer(1, 16))
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">Summary plots:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts

        data = []

        if len(self._summary_plots) > 2:
            data.append([PdfImage(self._summary_plots[1], width=7.5*cm, height=7.5*cm), 
                         PdfImage(self._summary_plots[2], width=7.5*cm, height=7.5*cm)
                        ])
            data.append([PdfImage(self._summary_plots[0], width=7.5*cm, height=7.5*cm)])

        else:
            for image in self._summary_plots:
                data.append([PdfImage(image, width=7.5*cm, height=7.5*cm)])

        doc_contents.append(Table(data, colWidths=[8.0*cm, 8.0*cm], hAlign="CENTER"))

    def add_comments(self, doc_contents: list):
        """
        Add comments to the report
        """
        if self._comments is None or self._comments == "":
            return
            
        doc_contents.append(Spacer(1, 16))
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">Comments:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts
        
        doc_contents.append(Paragraph(self._comments.replace("\n", "<br/>")))
        
    def add_signature(self, doc_contents: list):
        """
        Add signature to the report
        """
        doc_contents.append(Spacer(1, 32))
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">Signature:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts
        
        data = [["Physicist:", "_______________________"],
                ["Date:", "_______________________"]]
        
        table = Table(data, colWidths=[4.0*cm, 12.0*cm])
        table.setStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('ALIGN', (0,0), (0,-1), 'RIGHT')])
        
        doc_contents.append(table)
        
    def save_report(self):
        document =  SimpleDocTemplate(self._filename)
        doc_contents = [Spacer(1, 2.0*cm)]

        # add document body and then build the PDF
        self.set_user_details(doc_contents)
        self.set_analysis_details(doc_contents)

        #if self._summary_plots is not None:
        #    self.set_plot_summary(doc_contents)
        
        self.add_comments(doc_contents)
        self.add_signature(doc_contents)

        document.build(doc_contents, onFirstPage=self.add_metadata)

class BaseCalibrationReport(BaseReport):
    """
    General class for generating TRS398 calibration reports
    """
    def __init__(
        self, filename: str,
        report_name: str = "Base Calibration Report",
        calibration_info: dict | None = None,
        ):
        
        super().__init__(filename, report_name)
        self._calibration_info = calibration_info
        
    def set_calibration_details(self, doc_contents: list):
        """
        Add calibration details to the report
        """
        doc_contents.append(Spacer(1, 16))
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">Calibration details:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts
        
        if self._calibration_info is None:
            doc_contents.append(Paragraph("No calibration details available."))
            return
        
        data = []
        data.append(["Parameter", "Value"])
        
        for key, value in self._calibration_info.items():
            data.append([key, value])
            
        table = Table(data, colWidths=[8.0*cm, 8.0*cm])
        table.setStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
                        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                        ('LINEABOVE', (0,0), (-1,0), 1, colors.black),
                        ('LINEABOVE', (0,1), (-1,1), 1, colors.black)])
        
        doc_contents.append(table)
        
    def save_report(self):
        document =  SimpleDocTemplate(self._filename)
        doc_contents = [Spacer(1, 2.0*cm)]

        # add document body and then build the PDF
        self.set_user_details(doc_contents)
        self.set_calibration_details(doc_contents)
        self.add_comments(doc_contents)
        self.add_signature(doc_contents)

        document.build(doc_contents, onFirstPage=self.add_metadata)

class PhotonsCalibrationReport(BaseCalibrationReport):
    """
    Class for generating TRS398 photon calibration reports
    """
    def __init__(
        self, filename: str,
        author: str | None = None,
        institution: str | None = None,
        treatment_unit_name: str | None = None,
        analysis_date: str | None = None,
        calibration_info: dict | None = None,
        comments: str | None = None
        ):
        
        super().__init__(
            filename,
            report_name="TRS-398 Photon Output Calibration Report",
            calibration_info=calibration_info
        )
        
        self._author = author
        self._institution = institution
        self._treatment_unit_name = treatment_unit_name
        self._analysis_date = analysis_date
        self._comments = comments

class ElectronsCalibrationReport(BaseCalibrationReport):
    """
    Class for generating TRS398 electron calibration reports
    """
    def __init__(
        self, filename: str,
        author: str | None = None,
        institution: str | None = None,
        treatment_unit_name: str | None = None,
        analysis_date: str | None = None,
        calibration_info: dict | None = None,
        comments: str | None = None
        ):
        
        super().__init__(
            filename,
            report_name="TRS-398 Electron Output Calibration Report",
            calibration_info=calibration_info
        )
        
        self._author = author
        self._institution = institution
        self._treatment_unit_name = treatment_unit_name
        self._analysis_date = analysis_date
        self._comments = comments

class PlanarImagingReport(BaseReport):
    """
    Class for generating planar imaging reports
    """
    def __init__(
        self, filename: str,
        author: str | None = None,
        institution: str | None = None,
        treatment_unit_name: str | None = None,
        analysis_date: str | None = None,
        imaging_system_type: str | None = None,
        imaging_system_name: str | None = None,
        phantom_name: str | None = None,
        summary_plots: list | None = None,
        analysis_summary: dict | None = None,
        comments: str | None = None
        ):
        
        super().__init__(
            filename,
            report_name="Planar Imaging QA Report",
            author=author,
            institution=institution,
            treatment_unit_name=treatment_unit_name,
            analysis_date=analysis_date,
            analysis_summary=analysis_summary,
            summary_plots=summary_plots,
            comments=comments
        )
        
        self._imaging_system_type = imaging_system_type
        self._imaging_system_name = imaging_system_name
        self._phantom_name = phantom_name
        
    def set_analysis_details(self, doc_contents: list):
        """
        Add analysis details to the report
        """
        doc_contents.append(Spacer(1, 16))
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">Analysis details:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts
        
        data = [["Imaging system type:", self._imaging_system_type],
                ["Imaging system name:", self._imaging_system_name],
                ["Phantom:", self._phantom_name]]
        
        table = Table(data, colWidths=[4.0*cm, 12.0*cm])
        table.setStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('ALIGN', (0,0), (0,-1), 'RIGHT')])
        
        doc_contents.append(table)
        
        doc_contents.append(Spacer(1, 16))
        
        if self._analysis_summary is None:
            doc_contents.append(Paragraph("No analysis details available."))
            return
        
        data = []
        data.append(["Parameter", "Value"])
        
        for key, value in self._analysis_summary.items():
            data.append([key, value])
            
        table = Table(data, colWidths=[8.0*cm, 8.0*cm])
        table.setStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
                        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                        ('LINEABOVE', (0,0), (-1,0), 1, colors.black),
                        ('LINEABOVE', (0,1), (-1,1), 1, colors.black)])
        
        doc_contents.append(table)
        
    def save_report(self):
        document =  SimpleDocTemplate(self._filename)
        doc_contents = [Spacer(1, 2.0*cm)]

        # add document body and then build the PDF
        self.set_user_details(doc_contents)
        self.set_analysis_details(doc_contents)
        
        if self._summary_plots is not None:
            self.set_plot_summary(doc_contents)
        
        self.add_comments(doc_contents)
        self.add_signature(doc_contents)

        document.build(doc_contents, onFirstPage=self.add_metadata)

class CatPhanReport(BaseReport):
    """
    Class for generating CatPhan analysis reports
    """
    def __init__(
        self, filename: str,
        author: str | None = None,
        institution: str | None = None,
        treatment_unit_name: str | None = None,
        analysis_date: str | None = None,
        phantom_model: str | None = None,
        summary_plots: list | None = None,
        analysis_summary: dict | None = None,
        comments: str | None = None
        ):
        
        super().__init__(
            filename,
            report_name="CatPhan CT QA Report",
            author=author,
            institution=institution,
            treatment_unit_name=treatment_unit_name,
            analysis_date=analysis_date,
            analysis_summary=analysis_summary,
            summary_plots=summary_plots,
            comments=comments
        )
        
        self._phantom_model = phantom_model
        
    def set_analysis_details(self, doc_contents: list):
        """
        Add analysis details to the report
        """
        doc_contents.append(Spacer(1, 16))
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">Analysis details:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts
        
        data = [["Phantom Model:", self._phantom_model]]
        
        table = Table(data, colWidths=[4.0*cm, 12.0*cm])
        table.setStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('ALIGN', (0,0), (0,-1), 'RIGHT')])
        
        doc_contents.append(table)
        
        doc_contents.append(Spacer(1, 16))
        
        if self._analysis_summary is None:
            doc_contents.append(Paragraph("No analysis details available."))
            return
        
        data = []
        data.append(["Parameter", "Value"])
        
        for key, value in self._analysis_summary.items():
            data.append([key, value])
            
        table = Table(data, colWidths=[8.0*cm, 8.0*cm])
        table.setStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
                        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                        ('LINEABOVE', (0,0), (-1,0), 1, colors.black),
                        ('LINEABOVE', (0,1), (-1,1), 1, colors.black)])
        
        doc_contents.append(table)
        
    def save_report(self):
        document = SimpleDocTemplate(self._filename)
        doc_contents = [Spacer(1, 2.0*cm)]

        # add document body and then build the PDF
        self.set_user_details(doc_contents)
        self.set_analysis_details(doc_contents)
        
        if self._summary_plots is not None:
            self.set_plot_summary(doc_contents)
        
        self.add_comments(doc_contents)
        self.add_signature(doc_contents)

        document.build(doc_contents, onFirstPage=self.add_metadata)

