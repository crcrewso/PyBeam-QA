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
from pdfrw.buildxobj import pagexobj

from core.tools.toreportlab import makerl

assets_dir = Path(str(Path(__file__).parent) + "/report_assets").resolve()
assets_dir = str(assets_dir)

styles = getSampleStyleSheet()

class PdfImage(Flowable):
    """
    Wrapper for Image flowable to handle BytesIO objects and PDF objects
    """
    def __init__(self, img_data, width=None, height=None):
        Flowable.__init__(self)
        self.img_data = img_data
        self.width = width
        self.height = height
        
        # Handle PDF objects if needed
        if isinstance(img_data, io.BytesIO):
            try:
                img_data.seek(0)
                # Try to parse as PDF
                page, = PdfReader(img_data).pages
                self.img_data = pagexobj(page)
                if width is None or height is None:
                    self.width = float(page['/MediaBox'][2])
                    self.height = float(page['/MediaBox'][3])
                self.is_pdf = True
                # Reset the BytesIO position for potential future use
                img_data.seek(0)
                return
            except Exception:
                # Not a PDF or other error, use as regular image
                img_data.seek(0)
                pass
        
        self.is_pdf = False
        
    def wrap(self, availWidth, availHeight):
        return self.width, self.height
    
    def drawOn(self, canvas, x, y, _sW=0):
        if _sW > 0 and hasattr(self, 'hAlign'):
            a = self.hAlign
            if a in ('CENTER', 'CENTRE', TA_CENTER):
                x += 0.5*_sW
            elif a in ('RIGHT', TA_RIGHT):
                x += _sW
            elif a not in ('LEFT', TA_LEFT):
                raise ValueError("Bad hAlign value " + str(a))
                
        canvas.saveState()
        
        if self.is_pdf:
            # Handle PDF objects
            img = self.img_data
            if isinstance(img, PdfDict):
                xscale = self.width / img.BBox[2]
                yscale = self.height / img.BBox[3]
                canvas.translate(x, y)
                canvas.scale(xscale, yscale)
                canvas.doForm(makerl(canvas, img))
            else:
                canvas.drawImage(img, x, y, self.width, self.height)
        else:
            # Handle regular images
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

        # Handle both single image and list of images
        if not isinstance(self._summary_plots, list):
            summary_plots = [self._summary_plots]
        else:
            summary_plots = self._summary_plots

        data = []

        if len(summary_plots) > 2:
            data.append([PdfImage(summary_plots[1], width=7.5*cm, height=7.5*cm), 
                         PdfImage(summary_plots[2], width=7.5*cm, height=7.5*cm)
                        ])
            data.append([PdfImage(summary_plots[0], width=7.5*cm, height=7.5*cm)])
        else:
            for image in summary_plots:
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

class WinstonLutzReport(BaseReport):
    """
    Class for generating Winston-Lutz reports
    """
    def __init__(
        self, filename: str,
        report_name: str = "Winston-Lutz Analysis Report",
        author: str = "N/A",
        institution: str = "N/A",
        treatment_unit_name: str = None,
        analysis_date: str | None = None,
        analysis_summary: dict = None,
        patient_info: dict = None,
        summary_plot: io.BytesIO = None,
        report_status: str = "N/A",
        tolerance: float = 1.00,
        comments: str | None = None
        ):
        super().__init__(filename, report_name)

        self._author = author
        self._institution = institution
        self._treatment_unit_name = treatment_unit_name
        self._analysis_date = analysis_date
        self._analysis_summary = analysis_summary
        self._patient_info = patient_info
        self._summary_plot = summary_plot
        self._report_status = report_status
        self._tolerance = tolerance
        self._comments = comments

    def set_user_details(self, doc_contents: list):
        data = [[Paragraph("<b>Physicist</b>"), f": {self._author}"],
                [Paragraph("<b>Institution</b>"), f": {self._institution}"],
                [Paragraph("<b>Treatment unit</b>"), f": {self._treatment_unit_name}"],
                [Paragraph("<b>Analysis date</b>"), f": {self._analysis_date}"],
                [Paragraph("<b>Test tolerance</b>"), f": {self._tolerance} mm"],
                [Paragraph("<b>Test outcome</b>"), f": {self._report_status}"]]
        
        if self._patient_info is not None:
            data.append(["",""])
            data.append([Paragraph("<b>Patient name</b>"), f": {self._patient_info['patient_name']}"])
            data.append([Paragraph("<b>Patient ID</b>"), f": {self._patient_info['patient_id']}"])
        
        doc_contents.append(Table(data, colWidths=[3.5*cm, 5.0*cm], hAlign="LEFT",
                                  style=[('LEFTPADDING', (0,0), (0,-1), 0)]))

    def set_analysis_details(self, doc_contents: list):
        doc_contents.append(Spacer(1, 16)) # add spacing of 8 pts
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">Analysis Details:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts

        data = [[param, value] for param, value in self._analysis_summary.items()]
        data.insert(0, [Paragraph("<b>Parameter</b>"), Paragraph("<b>Value</b>"), Paragraph("<b>Comment(s)</b>")])

        table = Table(data, colWidths=[8.0*cm, 3.5*cm], hAlign="LEFT",
                      style=[('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                             ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                             ('LINEABOVE', (0,0), (-1,0), 1, colors.black),
                             ('LINEABOVE', (0,1), (-1,1), 1, colors.black)])
        
        doc_contents.append(table)

    def set_plot_summary(self, doc_contents: list):
        doc_contents.append(PageBreak())
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">Summary plot:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 8 pts
        doc_contents.append(PdfImage(self._summary_plot, width=16*cm, height=16*cm))

    def save_report(self):
        document =  SimpleDocTemplate(self._filename)
        doc_contents = [Spacer(1, 2.0*cm)]

        # add document body and then build the PDF
        self.set_user_details(doc_contents)
        self.set_analysis_details(doc_contents)

        if self._summary_plot is not None:
            self.set_plot_summary(doc_contents)
        
        self.add_comments(doc_contents)
        self.add_signature(doc_contents)

        document.build(doc_contents, onFirstPage=self.add_metadata)

class PicketFenceReport(BaseReport):
    """
    Class for generating Picket fence reports
    """
    def __init__(
        self, filename: str,
        report_name: str = "Picket Fence Analysis Report",
        author: str = "N/A",
        institution: str = "N/A",
        treatment_unit_name: str | None = None,
        mlc_type: str = "N/A",
        analysis_summary: list | None = None,
        analysis_date: str | None = None,
        summary_plot: io.BytesIO | None = None,
        report_status: str = "N/A",
        max_error: float | None = None,
        tolerance: float = 0.5,
        comments: str | None = None
        ):
        super().__init__(filename, report_name)

        self._author = author
        self._institution = institution
        self._treatment_unit_name = treatment_unit_name
        self._mlc_type = mlc_type
        self._analysis_date = analysis_date
        self._analysis_summary = analysis_summary
        self._summary_plot = summary_plot
        self._report_status = report_status
        self._max_error = max_error
        self._tolerance = tolerance
        self._comments = comments

    def set_user_details(self, doc_contents: list):
        data = [[Paragraph("<b>Physicist</b>"), f": {self._author}"],
                [Paragraph("<b>Institution</b>"), f": {self._institution}"],
                [Paragraph("<b>Treatment unit</b>"), f": {self._treatment_unit_name}"],
                [Paragraph("<b>MLC type</b>"), f": {self._mlc_type}"],
                [Paragraph("<b>Analysis date</b>"), f": {self._analysis_date}"],
                [Paragraph("<b>Test tolerance</b>"), f": {self._tolerance:2.2f} mm"]]
        
        if self._max_error is not None:
            data.append([Paragraph("<b>Test outcome</b>"),
                         f": {self._report_status} (Max. error = {self._max_error:2.3f} mm)"])
            
        else:
            data.append([Paragraph("<b>Test outcome</b>"), f": {self._report_status}"])
        
        doc_contents.append(Table(data, colWidths=[3.5*cm, 5.0*cm], hAlign="LEFT",
                                  style=[('LEFTPADDING', (0,0), (0,-1), 0)]))

    def set_analysis_details(self, doc_contents: list):
        doc_contents.append(Spacer(1, 16)) # add spacing of 8 pts
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">Analysis Details:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts

        data = [[param, value] if isinstance(value, str) else [param, value[0], value[1]] 
                for param, value in self._analysis_summary.items()]
        data.insert(0, [Paragraph("<b>Parameter</b>"), Paragraph("<b>Value</b>"), Paragraph("<b>Comment(s)</b>")])

        table = Table(data, colWidths=[6.0*cm, 3.0*cm, 6.5*cm], hAlign="LEFT",
                      style=[('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                             ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                             ('LINEABOVE', (0,0), (-1,0), 1, colors.black),
                             ('LINEABOVE', (0,1), (-1,1), 1, colors.black)])
        
        doc_contents.append(table)

    def set_plot_summary(self, doc_contents: list):
        doc_contents.append(Spacer(1, 16))
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">Summary plot:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 8 pts

        image = PdfImage(self._summary_plot, width=7.5*cm, height=7.5*cm)
        image.hAlign = "CENTRE"
        doc_contents.append(image)

    def save_report(self):
        document =  SimpleDocTemplate(self._filename)
        doc_contents = [Spacer(1, 2.0*cm)]

        # add document body and then build the PDF
        self.set_user_details(doc_contents)
        self.set_analysis_details(doc_contents)

        if self._summary_plot is not None:
            self.set_plot_summary(doc_contents)
        
        self.add_comments(doc_contents)
        self.add_signature(doc_contents)

        document.build(doc_contents, onFirstPage=self.add_metadata)

class FieldAnalysisReport(BaseReport):
    """
    Class for generating Field Analysis reports
    """
    def __init__(
        self, filename: str,
        report_name: str = "Field Analysis Report",
        author: str = "N/A",
        institution: str = "N/A",
        protocol: str = "N/A",
        treatment_unit_name: str | None = None,
        analysis_date: str | None = None,
        analysis_summary: dict | None = None,
        summary_plots: list[io.BytesIO] | None = None,
        comments: str | None = None
        ):
        super().__init__(filename, report_name)

        self._author = author
        self._institution = institution
        self._treatment_unit_name = treatment_unit_name
        self._protocol = protocol
        self._analysis_date = analysis_date
        self._analysis_summary = analysis_summary
        self._summary_plots = summary_plots
        self._comments = comments

    def set_user_details(self, doc_contents: list):
        data = [
            [Paragraph("<b>Physicist</b>"), f": {self._author}"],
            [Paragraph("<b>Institution</b>"), f": {self._institution}"],
            [Paragraph("<b>Treatment unit</b>"), f": {self._treatment_unit_name}"],
            [Paragraph("<b>Analysis date</b>"), f": {self._analysis_date}"],
            [],
            [Paragraph("<b>Analysis protocol</b>"), f": {self._protocol}"]
        ]
        
        doc_contents.append(Table(data, colWidths=[3.5*cm, 5.0*cm], hAlign="LEFT",
                                  style=[('LEFTPADDING', (0,0), (0,-1), 0)]))

    def set_analysis_details(self, doc_contents: list):
        results = self._analysis_summary

        for title in results.keys():
            doc_contents.append(Spacer(1, 16)) # add spacing of 8 pts
            doc_contents.append(Paragraph(f"<b><u><font size=11 color=\"darkblue\">{title}</font></u></b>"))
            doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts

            data = []
            data.insert(0, [Paragraph("<b>Parameter</b>"),
                            Paragraph("<b>Value</b>")]
                            )
            
            for item in results[title]:
                data.append(item)

            table = Table(data, colWidths=[8.0*cm, 5.0*cm], hAlign="LEFT",
                      style=[('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                             ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                             ('LINEABOVE', (0,0), (-1,0), 1, colors.black),
                             ('LINEABOVE', (0,1), (-1,1), 1, colors.black)]
                        )
        
            doc_contents.append(table)

    def set_plot_summary(self, doc_contents: list):
        #doc_contents.append(PageBreak())
        doc_contents.append(Spacer(1, 16))
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">Summary plots:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts

        data = [[PdfImage(self._summary_plots[0], width=9.0*cm, height=9.0*cm), 
                 PdfImage(self._summary_plots[1], width=9.0*cm, height=9.0*cm)]]

        doc_contents.append(Table(data, colWidths=[9.0*cm, 9.0*cm], hAlign="CENTER"))

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

class StarshotReport(BaseReport):
    """
    Class for generating Starshot reports
    """
    def __init__(
        self, filename: str,
        report_name: str = "Starshot Analysis Report",
        author: str | None = None,
        institution: str | None = None,
        treatment_unit_name: str | None = None,
        analysis_date: str | None = None,
        report_status: str = "N/A",
        analysis_data: dict | None = None,
        tolerance: float = 1.0,
        comments: str | None = None
        ):
        
        super().__init__(
            filename,
            report_name=report_name,
            author=author,
            institution=institution,
            treatment_unit_name=treatment_unit_name,
            analysis_date=analysis_date,
            comments=comments
        )

        self._report_status = report_status
        self._tolerance = tolerance
        self._analysis_data = analysis_data

    def set_user_details(self, doc_contents: list):
        """
        Add user details to the report
        """
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">User details:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts
        
        data = [["Physicist:", self._author],
                ["Institution:", self._institution],
                ["Treatment unit:", self._treatment_unit_name],
                ["Analysis date:", self._analysis_date],
                ["Test tolerance:", f"{self._tolerance:2.2f} mm"],
                ["Test outcome:", f"{self._report_status} (wobble diameter = {self._analysis_data['wobble'].diameter_mm:.2f} mm)"]]
        
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
        
        data = []
        data.append(["Parameter", "Value"])
        data.append(["Wobble (circle) diameter", f"{self._analysis_data['wobble'].diameter_mm:.2f} mm"])
        data.append(["Number of spokes detected", f"{len(self._analysis_data['spoke_lines'])}"])
        
        table = Table(data, colWidths=[8.0*cm, 8.0*cm])
        table.setStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
                        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                        ('LINEABOVE', (0,0), (-1,0), 1, colors.black),
                        ('LINEABOVE', (0,1), (-1,1), 1, colors.black)])
        
        doc_contents.append(table)

    def set_plot_summary(self, doc_contents: list):
        """
        Add plot summary to the report
        """
        doc_contents.append(Spacer(1, 16))
        doc_contents.append(Paragraph("<b><u><font size=11 color=\"darkblue\">Summary plots:</font></u></b>"))
        doc_contents.append(Spacer(1, 16)) # add spacing of 16 pts

        data = [[PdfImage(self._analysis_data["report_plots"][0], width=7.5*cm, height=7.5*cm), 
                 PdfImage(self._analysis_data["report_plots"][1], width=7.5*cm, height=7.5*cm)]]

        doc_contents.append(Table(data, colWidths=[8.0*cm, 8.0*cm], hAlign="CENTER"))

    def save_report(self):
        """
        Save the report to a PDF file
        """
        document = SimpleDocTemplate(self._filename)
        doc_contents = [Spacer(1, 2.0*cm)]

        # add document body and then build the PDF
        self.set_user_details(doc_contents)
        self.set_analysis_details(doc_contents)

        if "report_plots" in self._analysis_data and self._analysis_data["report_plots"] is not None:
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
